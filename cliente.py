"""
Cliente de Streaming de Imagens via UDP
Requisitos e Bibliotecas:
- Python 3.8+
- opencv-python (cv2): Manipulacao e decodificacao de imagens / exibicao em janela
- numpy: Conversao de buffers de bytes para matrizes de imagem
Instalacao:
    pip install opencv-python numpy
"""

import socket
import threading
import queue
import time
import argparse
import cv2
import numpy as np
from protocolo import JOIN, EXIT, DATA, KEEPALIVE, criar_pacote, ler_pacote, agora_us

def thread_keepalive(sock: socket.socket, servidor_addr: tuple, ativo: threading.Event, intervalo: float = 2.0):
    while ativo.is_set():
        # Aguarda o intervalo de envio ou acorda imediatamente caso ativo seja desmarcado
        if ativo.wait(timeout=intervalo):
            # Se ativo.wait retornou True antes do timeout, significa que ativo foi sinalizado para parar
            break
        
        if not ativo.is_set():
            break

        try:
            pacote = criar_pacote(
                tipo=KEEPALIVE,
                frame_id=0,
                timestamp=agora_us(),
                total_frags=0,
                frag_index=0
            )
            sock.sendto(pacote, servidor_addr)
        except OSError:
            # Ocorre caso o socket tenha sido fechado pela thread principal durante o encerramento
            break

def thread_recepcao(sock: socket.socket, fila_frames: queue.Queue, ativo: threading.Event):
    sock.settimeout(0.5)
    buffer_montagem = {}
    ultimo_frame_id = -1

    while ativo.is_set():
        try:
            dados, _ = sock.recvfrom(2048)
            pacote = ler_pacote(dados)
        except (socket.timeout, ValueError):
            continue
        except OSError:
            break

        if pacote["tipo"] == EXIT:
            print("\n[*] Servidor encerrou a transmissao.")
            ativo.clear()
            break

        if pacote["tipo"] != DATA:
            continue

        f_id = pacote["frame_id"]
        idx = pacote["frag_index"]
        total = pacote["total_frags"]
        payload = pacote["payload"]

        # 1. Descarta fragmentos de frames que ja foram ultrapassados (prioridade tempo real)
        if f_id <= ultimo_frame_id:
            continue

        # 2. Inicializa o buffer do frame se for o primeiro fragmento a chegar
        if f_id not in buffer_montagem:
            buffer_montagem[f_id] = {"total": total, "frags": {}}

        buffer_montagem[f_id]["frags"][idx] = payload

        # 3. Verifica se todos os fragmentos do frame foram recebidos
        if len(buffer_montagem[f_id]["frags"]) == total:
            try:
                frame_bytes = b"".join(buffer_montagem[f_id]["frags"][i] for i in range(total))
                
                # Se a fila de exibicao estiver cheia, descarta o mais antigo para priorizar tempo real
                if fila_frames.full():
                    try:
                        fila_frames.get_nowait()
                    except queue.Empty:
                        pass
                
                fila_frames.put_nowait(frame_bytes)
                ultimo_frame_id = f_id
            except KeyError:
                pass

            # 4. Limpeza: remove este frame e quaisquer frames anteriores que ficaram incompletos
            chaves_antigas = [k for k in buffer_montagem.keys() if k <= f_id]
            for k in chaves_antigas:
                del buffer_montagem[k]

def iniciar_cliente(host: str, port: int):
    servidor_addr = (host, port)
    
    # Criacao do socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Aumento do buffer de recepcao do SO (1 MB) para mitigar descarte por rajadas
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
    
    # Evento para coordenar a parada limpa das threads e fila compartilhada de frames
    ativo = threading.Event()
    ativo.set()
    fila_frames = queue.Queue(maxsize=30)
    
    # Envio do pacote inicial de registro (JOIN)
    pacote_join = criar_pacote(
        tipo=JOIN,
        frame_id=0,
        timestamp=agora_us(),
        total_frags=0,
        frag_index=0
    )
    sock.sendto(pacote_join, servidor_addr)
    print(f"[*] Registrado no servidor {host}:{port} via JOIN.")

    # Inicializacao das threads em segundo plano
    t_keepalive = threading.Thread(
        target=thread_keepalive,
        args=(sock, servidor_addr, ativo),
        daemon=True
    )
    t_recepcao = threading.Thread(
        target=thread_recepcao,
        args=(sock, fila_frames, ativo),
        daemon=True
    )
    
    t_keepalive.start()
    t_recepcao.start()
    
    cv2.namedWindow("Streaming UDP", cv2.WINDOW_AUTOSIZE)

    try:
        while ativo.is_set():
            try:
                # Leitura com timeout para nao travar a thread e responder a interrupcoes
                frame_bytes = fila_frames.get(timeout=0.1)
                
                # Decodificacao do buffer JPEG para matriz BGR do OpenCV
                frame_matriz = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_matriz, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    cv2.imshow("Streaming UDP", frame)
            except queue.Empty:
                pass
            
            # Atualizacao da janela do OpenCV e checagem de saida
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n[*] Solicitacao de saida pelo usuario ('q').")
                break

    except KeyboardInterrupt:
        print("\n[*] Interrupcao via teclado (Ctrl+C).")
    finally:
        # Sinaliza parada para as demais threads
        ativo.clear()
        
        # Notifica o servidor para remocao imediata da lista de clientes
        try:
            pacote_exit = criar_pacote(
                tipo=EXIT,
                frame_id=0,
                timestamp=agora_us(),
                total_frags=0,
                frag_index=0
            )
            sock.sendto(pacote_exit, servidor_addr)
        except OSError:
            pass
        
        sock.close()
        cv2.destroyAllWindows()
        print("[*] Recursos liberados e socket fechado.")

def definir_params():
    parser = argparse.ArgumentParser(description="Cliente Streaming UDP")
    parser.add_argument("-H", "--host", type=str, default="127.0.0.1", help="IP do servidor")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Porta do servidor")
    return parser.parse_args()

if __name__ == "__main__":
    args = definir_params()
    iniciar_cliente(args.host, args.port)




