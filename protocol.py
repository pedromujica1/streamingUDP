import struct
import time

# Cabeçalho da aplicação (ordem de rede / big-endian), 19 bytes:
# tipo(1) frame_id(4) timestamp(8) total_frags(2) frag_index(2) payload_len(2)
HEADER_FMT = '!BIQHHH'
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 19 bytes
MAX_PAYLOAD = 1400

JOIN, LEAVE, DATA, KEEPALIVE = 0, 1, 2, 3

#instante atual em microssegundos, usado no campo timestamp
def agora_us() -> int:
  
    return time.time_ns() // 1000


def criar_pacote(tipo: int, frame_id: int, timestamp: int, total_frags: int,frag_index: int, payload: bytes = b'') -> bytes:
    if len(payload) > MAX_PAYLOAD:
        raise ValueError(f"Payload excede o limite de {MAX_PAYLOAD} bytes")
    cabecalho = struct.pack(HEADER_FMT, tipo, frame_id, timestamp,total_frags, frag_index, len(payload))
    return cabecalho + payload


def ler_pacote(datagrama: bytes) -> dict:
    if len(datagrama) < HEADER_SIZE:
        raise ValueError(f"Datagrama menor que o cabeçalho ({HEADER_SIZE} bytes)")

    tipo, frame_id, timestamp, total_frags, frag_index, payload_len = struct.unpack(
        HEADER_FMT, datagrama[:HEADER_SIZE])

    #verificar integridade
    payload = datagrama[HEADER_SIZE:HEADER_SIZE + payload_len]
    if len(payload) < payload_len:
        raise ValueError("Datagrama truncado: menos dados que payload_len")

    return {
        "tipo": tipo,
        "frame_id": frame_id,
        "timestamp": timestamp,
        "total_frags": total_frags,
        "frag_index": frag_index,
        "payload_len": payload_len,
        "payload": payload,
    }