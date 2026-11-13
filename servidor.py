import cv2
import socket
import time
import threading
import argparse
import os
from fractions import Fraction
from protocolo import JOIN, EXIT, DATA, KEEPALIVE, criar_pacote, ler_pacote, agora_us

def validacao_video(path: str) -> cv2.VideoCapture:
    # verifica tamanho máximo do arquivo (20 MB)
    tamanho_max_bytes = 20 * 1024 * 1024
    tamanho_atual = os.path.getsize(path)
    if tamanho_atual > tamanho_max_bytes:
        tamanho_mb = tamanho_atual / (1024 * 1024)
        raise ValueError(f"Erro: O vídeo excede o tamanho máximo de 20 MB (Tamanho atual: {tamanho_mb:.2f} MB).")

    # abre o arquivo e checa se abriu corretamente
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError("Erro: Não foi possível abrir o vídeo.")

    # valida resolução máxima
    largura = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    altura = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if largura > 640 or altura > 480:
        cap.release()
        raise ValueError(f"Erro: A resolução do vídeo ({largura}x{altura}) excede o limite máximo permitido de 640x480.")

    # valida os 30 segs de duracao max
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        cap.release()
        raise ValueError("Erro: Não foi possível determinar o FPS do vídeo para calcular a duração.")

    duracao = total_frames / fps
    if duracao > 30.0:
        cap.release()
        raise ValueError(f"Erro: A duração do vídeo ({duracao:.2f}s) excede o limite máximo de 30 segundos.")

    print(f"Vídeo validado com sucesso! ({largura}x{altura}, {duracao:.2f}s, {tamanho_atual / (1024 * 1024):.2f} MB)")
    return cap

def iniciar_servidor(host: str, port: int, path: str, interval: float, frag_size: int, quality: int, loop: bool):
    # validando limites do video
    cap = validacao_video(path)
    
    # iniciando servidor socket
    udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_addr = (host, port)
    udp_server_socket.bind(server_addr)
    print(f"Servidor UDP escutando em {host}:{port}...")
    
    # semafaro e estrutura de dados pra armazenar ordem dos clientes
    clientes = {}
    clientes_lock = threading.Lock()
    
    TIMEOUT_CLIENTE = 7.0
    
    # definicao da thread de controle
    def thread_controle():
        while True:
            try:
                # recebe os dados de quem enviou
                data, client_address = udp_server_socket.recvfrom(2048)
                # faz a leitura do pacote
                pacote = ler_pacote(data)
            except ValueError:
                # 1. AJUSTE: Apenas o tipo da exceção (sem parênteses/string)
                continue
            except OSError:
                # Encerra silenciosamente quando o socket for fechado no finally
                break
            
            if pacote["tipo"] == JOIN:
                with clientes_lock:
                    clientes[client_address] = time.monotonic()
                print(f"[+] Cliente conectado: {client_address}")
                
            elif pacote["tipo"] == KEEPALIVE:
                with clientes_lock:
                    if client_address in clientes:
                        clientes[client_address] = time.monotonic()
                        
            elif pacote["tipo"] == EXIT:
                with clientes_lock:
                    removido = clientes.pop(client_address, None)
                if removido is not None:
                    print(f"[-] Cliente desconectado: {client_address}")
                    
    # deixando uma threading daemon para nao impedir programa principal de encerrar    
    t_controle = threading.Thread(target=thread_controle, daemon=True)
    t_controle.start()
    
    frame_id = 0
    
    #
    try:
        while True:
            # pega retorno e frames
            ret, frame = cap.read()
            
            # se acabou o vídeo: se loop=true, volta pro início; senão, sai do while
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                break
            
            # pega timestamp
            ts = agora_us()
            
            with clientes_lock:
                tempo_agora = time.monotonic()
                
                # percorre lista de clientes
                for client_addr, ultimo_contato in list(clientes.items()):
                    tempo_inativo = tempo_agora - ultimo_contato
                    if tempo_inativo > TIMEOUT_CLIENTE:
                        clientes.pop(client_addr, None)
                        print(f"[-] Cliente removido por inatividade: {client_addr}")
                            
                # copia clientes restantes ainda no lock
                clientes_ativos = list(clientes.keys()) 
                
            # sem outros clientes assistindo, vai para o prox. frame
            if not clientes_ativos:
                time.sleep(interval)
                continue   
        
            # pega frame serializado
            capturado, frame_serializado = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # verifica se frame foi capturado
            if not capturado:
                continue
            
            # transforma em bytes
            bytes_jpg = frame_serializado.tobytes()
            # fragmentos fatiados de acordo os pedacos
            fragmentos = [bytes_jpg[i : i + frag_size] for i in range(0, len(bytes_jpg), frag_size)]
            
            for index in range(len(fragmentos)):
                # cria pacotes
                pacote = criar_pacote(
                    tipo=DATA,
                    frame_id=frame_id,
                    timestamp=ts,
                    total_frags=len(fragmentos),
                    frag_index=index,
                    payload=fragmentos[index]
                )
                
                # enviando de acordo com ordem estabelecida em clientes_ativos
                for cliente_addr in clientes_ativos:
                    try:
                        udp_server_socket.sendto(pacote, cliente_addr)
                    except OSError:
                        pass
            
            frame_id += 1
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        cap.release()
        udp_server_socket.close()
        print("Recursos liberados com sucesso.")


def definir_params():
    parser = argparse.ArgumentParser(description="O melhor servidor UDP de Streaming!!!")
    
    parser.add_argument("-H", "--host", type=str, default="127.0.0.1", help="Endereço IP do servidor")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Porta UDP")
    parser.add_argument("-v", "--path", type=str, required=True, help="Caminho para vídeo .mp4 ou .avi")
    parser.add_argument("-i", "--interval", type=lambda x: float(Fraction(x)), default=1/30, help="Intervalo entre frames em segundos (ex: 0.033 ou 1/3)")
    parser.add_argument("-tFrag", "--frag-size", type=int, default=1400, help="Tamanho máximo do fragmento em bytes")
    parser.add_argument("-q", "--quality", type=int, default=80, help="Qualidade JPEG (1 a 100)")
    parser.add_argument("-l", "--loop", action="store_true", help="Reinicia o vídeo automaticamente ao chegar no final")
    
    args = parser.parse_args()
    
    if not os.path.isfile(args.path):
        parser.error(f"Arquivo de vídeo não encontrado: {args.path}")
    if not (1 <= args.quality <= 100):
        parser.error("A qualidade JPEG (--quality) deve estar entre 1 e 100.")
    if not (1 <= args.frag_size <= 1400):
        parser.error("O tamanho do fragmento (--frag-size) deve estar entre 1 e 1400 bytes.")
    if args.interval < 0:
        parser.error("O intervalo (--interval) não pode ser negativo.")
        
    return args
    

if __name__ == "__main__":
    args = definir_params()
    iniciar_servidor(host=args.host,port=args.port,path=args.path,interval=args.interval,frag_size=args.frag_size,quality=args.quality,loop=args.loop)
    
#python3 servidor.py -H 127.0.0.1 -p 5000 -v ../video2.mp4 -i 1/30 -tFrag 1400 -q 80 --loop