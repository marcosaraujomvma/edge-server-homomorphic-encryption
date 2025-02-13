import socket
import pickle
import struct
import concurrent.futures
import time

# Função para receber todos os bytes esperados do servidor
def receive_all(conn, expected_size):
    """Recebe todos os bytes esperados do servidor."""
    data = b""
    while len(data) < expected_size:
        packet = conn.recv(expected_size - len(data))
        if not packet:
            return None  # Retorna None se a conexão for interrompida
        data += packet
    return data

# Função para receber dados com tamanho prefixado
def receive_data_with_size(conn):
    """Recebe dados onde os primeiros 4 bytes indicam o tamanho."""
    raw_size = receive_all(conn, 4)  # Recebe os 4 bytes iniciais
    if not raw_size:
        return None  # Erro ao receber o tamanho
    expected_size = struct.unpack('!I', raw_size)[0]  # Converte para int
    return receive_all(conn, expected_size)  # Recebe os dados completos

# Função cliente para conectar ao servidor, enviar dados e receber a resposta
def client_task(client_id):
    HOST = '172.20.0.22'  # Endereço IP do servidor
    PORT = 65432         # Porta do servidor

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Recebe a chave pública do servidor
            public_key_serialized = receive_data_with_size(s)
            if not public_key_serialized:
                print(f"Cliente {client_id}: Erro ao receber chave pública")
                return

            public_key = pickle.loads(public_key_serialized)

            # Números a serem somados
            m1 = 5
            m2 = 10

            # Criptografa os números usando a chave pública
            encrypted_m1 = public_key.encrypt(m1)
            encrypted_m2 = public_key.encrypt(m2)

            # Serializa e envia os dados criptografados
            data = pickle.dumps([encrypted_m1, encrypted_m2])
            s.sendall(struct.pack('!I', len(data)) + data)

            print(f"Cliente {client_id}: Enviou números criptografados.")

    except Exception as e:
        print(f"Cliente {client_id}: Erro ao conectar ao servidor: {e}")

# Função para disparar múltiplos clientes simultaneamente
def run_multiple_clients(num_clients):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(client_task, i) for i in range(num_clients)]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    # Dispara diferentes quantidades de clientes simultaneamente
    for num_clients in [300]:
        print(f"\nDisparando {num_clients} clientes simultaneamente...")
        run_multiple_clients(num_clients)
