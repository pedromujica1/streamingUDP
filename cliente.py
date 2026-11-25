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

def thread_recepcao(sock, fila_frames, running_event):
    # Recebe pacotes, remonta no dicionário e joga na fila
    pass

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



#TRECHOS uteis
#vai precisar usar isso
# cv2.imshow("Top Video",frame)
'''

#se pressiona a tecla q, destroi janela
    if 0xFF == ord('q'):
        break
'''

'''
Seguindo a arquitetura definida nas Seções 4, 5 e 6 do seu documento de projeto, a lógica do `cliente.py` se divide em quatro etapas diretas:

1. **Inicialização e Conexão (`JOIN`)**
* Lê os argumentos via `argparse`: endereço IP e porta do servidor, além do timeout para descartar frames incompletos.


* Abre um socket UDP (`SOCK_DGRAM`), aumenta o buffer de recepção (`SO_RCVBUF`) para evitar perdas em rajadas e envia um pacote `JOIN` (com os demais campos zerados) para o servidor.


* Inicia duas threads secundárias (`daemon=True`) e uma `Queue` compartilhada.




2. **Thread de Keep-Alive**
* Roda em loop dormindo um intervalo fixo (ex: a cada 2 ou 3 segundos, bem menor que os 7s de timeout do seu servidor) e envia um pacote `KEEPALIVE` para manter o cadastro ativo no servidor.




3. **Thread de Recepção e Remontagem**
* Fica em `recvfrom()` lendo os datagramas com `ler_pacote()` e gerenciando um dicionário de remontagem indexado por `frame_id`:


* **Descarte de atrasados:** Ignora qualquer pacote cujo `frame_id` seja menor ou igual ao do último frame já exibido.


* **Armazenamento:** Salva o payload na posição `frag_idx` (ignorando duplicatas) e registra o instante de chegada do primeiro pedaço daquele frame.


* **Frame completo:** Quando a quantidade de pedaços atingir `total_frags`, junta os bytes na ordem (`0` até `total_frags - 1`), coloca o frame pronto e seu `timestamp` na `Queue` de exibição, e apaga do dicionário todos os frames incompletos mais antigos (`frame_id` menor).


* **Limpeza por timeout:** Remove frames incompletos que ultrapassaram o tempo limite configurado ou o limite máximo de frames simultâneos no buffer (ex: 5).






4. **Thread Principal: Exibição e Encerramento (`EXIT`)**
* Pega os bytes JPEG prontos da `Queue`, converte em matriz com `np.frombuffer` + `cv2.imdecode`, calcula a latência (`agora_us() - timestamp`) para as métricas e atualiza a janela com `cv2.imshow`. (Se nenhum frame novo chegar, mantém o último frame exibido sem piscar tela preta).


* Ao pressionar `'q'` ou fechar com `Ctrl+C`, envia um pacote `EXIT` ao servidor, fecha a janela e encerra o socket.'''



