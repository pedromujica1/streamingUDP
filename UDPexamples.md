## UDP examples


### Cliente UDP
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

### Servidor UDP

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
