# UDP examples

## Cliente e servidor UDP simples - Prática 06 RC

### Servidor UDP básico

```python
import socket

#criação do socket UDP
udp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#ligação do socket ao endereço e porta
#IPv4='localhost' ou '127.0.0.1', IPv6='::1'
server_address = ('localhost', 12345)
udp_server_socket.bind(server_address)

print("Servidor UDP aguardando mensagens...")

# Recebe dados do cliente
while True:
    # Buffer de 1024 bytes
    data, address = udp_server_socket.recvfrom(1024)
    print(f"Mensagem recebida: {data.decode()} de {address}")

    # Enviar uma resposta opcional para o cliente
    response = "Mensagem recebida com sucesso"
    udp_server_socket.sendto(response.encode(), address)
    print(f"Resposta enviada para {address}")
```

### Cliente UDP básico
```python
import socket

# Criação do socket UDP
udp_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Endereço do servidor e porta
# No mesmo host, IPv4='localhost' ou '127.0.0.1', IPv6='::1'
dest_ip = '127.0.0.1'  # Altere para o IP de destino
dest_port = 12345  # Porta de destino
server_address = (dest_ip, dest_port)

# Mensagem a ser enviada ao servidor
message = "Ola, servidor UDP!"
udp_client_socket.sendto(message.encode(), server_address)

# Recebe resposta do servidor
data, server = udp_client_socket.recvfrom(1024)
print(f"Resposta do servidor: {data.decode()}")

# Fechando o socket do cliente
udp_client_socket.close()
```


## Servidor de Streaming de Video com OpenCV

[Tutorial Medium: Criando um servidor de Streming de video usando OpenCV](https://medium.com/@prasadparit006/python-project-building-a-simple-video-streaming-server-using-opencv-c8a9d9ba86d2)
[Outro tutorial Medium](https://medium.com/@anshulsjr6/building-a-basic-video-streaming-application-in-python-with-opencv-cfb6995e2479)

### Server.py
```python
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

```


### Client.py
```python
import cv2
import socket
import pickle
import struct

# Create a socket client
video_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_client_socket.connect(('10.81.191.214', 9999))  # Replace with the server’s IP address

received_data = b""
payload_size = struct.calcsize("L")

while True:
    # Receive and assemble the data until the payload size is reached
    while len(received_data) < payload_size:
        received_data += video_client_socket.recv(4096)

    # Extract the packed message size
    packed_msg_size = received_data[:payload_size]
    received_data = received_data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    # Receive and assemble the frame data until the complete frame is received
    while len(received_data) < msg_size:
        received_data += video_client_socket.recv(4096)

    # Extract the frame data
    frame_data = received_data[:msg_size]
    received_data = received_data[msg_size:]

    # Deserialize the received frame
    received_frame = pickle.loads(frame_data)

    # Display the received frame
    cv2.imshow('Client Video', received_frame)

    # Press ‘q’ to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cv2.destroyAllWindows()
video_client_socket.close()
```
