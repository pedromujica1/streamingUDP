import cv2
import socket
import pickle
import struct
import argparse
import os
from fractions import Fraction

def testar_video(host: str,port: int, path: str, interval: float, frag_size: int, quality: int, loop: bool):
    #abrindo o arquivo
    cap = cv2.VideoCapture(path)
    
    #checar se o video abriu corretamente
    if not cap.isOpened():
        raise ValueError("Erro: Não foi possível abrir o vídeo.")
    else:
        print("Arquivo de víde aberto com sucesso!")
        
    #le o primeiro frame para confirmar leitura
    ret, frame = cap.read()
    
    if ret:
        cv2.imshow("Primeiro Framee!", frame)
        
        #se pressiona a tecla q, destroi janela
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows() 

    
def definir_params():
    
    parser = argparse.ArgumentParser(description="O melhor servidor UDP de Streaming!!!")
    
    parser.add_argument("-H", "--host", type=str, default="127.0.0.1", help="Endereço IP do servidor")
    parser.add_argument("-p", "--port", type=int, default=5000, help="Porta UDP")
    parser.add_argument("-v", "--path", type=str, required=True, help="Caminho para vídeo .mp4 ou .avi")
    
    #aceita fracoes tbm
    parser.add_argument("-i", "--interval", type=lambda x: float(Fraction(x)), default=1/30, help="Intervalo entre frames em segundos (ex: 0.033 ou 1/3)")
    #tamanho do fragmento
    parser.add_argument("-tFrag", "--frag-size", type=int, default=1400, help="Tamanho máximo do fragmento em bytes")
    #qualidade do frame
    parser.add_argument("-q", "--quality", type=int, default=80, help="Qualidade JPEG (1 a 100)")
    #loop unico
    parser.add_argument("-l", "--loop", action="store_true", help="Reinicia o vídeo automaticamente ao chegar no final")
    
    args = parser.parse_args()
    
    #validacoes
    if not os.path.isfile(args.path):
        parser.error(f"Arquivo de vídeo não encontrado: {args.path}")
    if not (1 <= args.quality <= 100):
        parser.error("A qualidade JPEG (--quality) deve estar entre 1 e 100.")
    if not (1 <= args.frag_size <= 65507):
        parser.error("O tamanho do fragmento (--frag-size) deve estar entre 1 e 65507 bytes.")
    if args.interval < 0:
        parser.error("O intervalo (--interval) não pode ser negativo.")
        
    return args
    

if __name__ == "__main__":
    definir_params()