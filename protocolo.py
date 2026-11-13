import struct
import time

HEADER_FMT = '!BIQHHH' #big-endian
HEADER_SIZE = struct.calcsize(HEADER_FMT)  #tamanho do header: 19 bytes
MAX_PAYLOAD = 1400

JOIN, EXIT, DATA, KEEPALIVE = 0, 1, 2, 3

#instante atual em microssegundos, usado no campo timestamp
def agora_us() -> int:
    return time.time_ns() // 1000


def criar_pacote(tipo: int, frame_id: int, timestamp: int, total_frags: int,frag_index: int, payload: bytes = b'') -> bytes:
    #verifica se pacote passa do limite de payload
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"Payload excede o limite de {MAX_PAYLOAD} bytes")
    #monta o formato do struct
    header_udp = struct.pack(HEADER_FMT,tipo,frame_id,timestamp,total_frags,frag_index,len(payload))
    
    return header_udp + payload
    

def ler_pacote(datagrama: bytes) -> dict:
    #verifica se o datagragrama passou do tamanho do header
    if len(datagrama) < HEADER_SIZE:
        raise ValueError(f"Datagrama menor que o cabeçalho ({HEADER_SIZE} bytes)")

    #faz o unpack dos campos
    tipo, frame_id, timestamp, total_frags, frag_index, payload_len = struct.unpack(HEADER_FMT, datagrama[:HEADER_SIZE])

    #verifica integridade do payload
    #tamanho do head + tamanho do payload
    payload = datagrama[HEADER_SIZE  :HEADER_SIZE + payload_len]
    if len(payload) < payload_len:
        raise ValueError("Datagrama truncado: menos dados que tamanho do payload")

    return {"tipo": tipo,
        "frame_id": frame_id,
        "timestamp": timestamp,
        "total_frags": total_frags,
        "frag_index": frag_index,
        "payload_len": payload_len,
        "payload": payload}