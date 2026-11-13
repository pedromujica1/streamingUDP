import cv2
import socket
import pickle
import struct
import argparse
import os
from fractions import Fraction

# Initialize video capture from the default camera
video_capture = cv2.VideoCapture(0)

# Create a socket server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('10.81.191.214', 9999))  # Replace with the server's IP address
server_socket.listen(10)

# Accept a client connection
client_socket, client_address = server_socket.accept()
print(f"[*] Accepted connection from {client_address}")

while True:
    # Read a frame from the camera
    ret, frame = video_capture.read()

    # Serialize the frame to bytes
    serialized_frame = pickle.dumps(frame)

    # Pack the data size and frame data
    message_size = struct.pack("L", len(serialized_frame))
    client_socket.sendall(message_size + serialized_frame)

    # Display the frame on the server-side (optional)
    cv2.imshow('Server Video', frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
video_capture.release()
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