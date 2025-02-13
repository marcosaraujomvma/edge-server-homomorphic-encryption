import socket
import struct
import concurrent.futures
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

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
    raw_size = receive_all(conn, 4)
    if not raw_size:
        return None
    expected_size = struct.unpack('!I', raw_size)[0]
    return receive_all(conn, expected_size)

# Cliente envia números criptografados
def client_task(client_id):
    HOST = '127.0.0.1'
    PORT = 65432

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Recebe a chave pública do servidor
            public_key_pem = receive_data_with_size(s)
            if not public_key_pem:
                print(f"Cliente {client_id}: Erro ao receber chave pública")
                return

            public_key = serialization.load_pem_public_key(public_key_pem)

            # Números a serem enviados
            num1, num2 = 5, 10
            message = f"{num1},{num2}".encode()

            # Criptografa os números com a chave pública do servidor
            encrypted_message = public_key.encrypt(
                message,
                ec.ECIESHKDFRecipientInfo(hashes.SHA256())
            )

            # Envia os dados criptografados
            s.sendall(struct.pack('!I', len(encrypted_message)) + encrypted_message)

            print(f"Cliente {client_id}: Enviou números criptografados.")

    except Exception as e:
        print(f"Cliente {client_id}: Erro ao conectar ao servidor: {e}")

# Dispara múltiplos clientes simultaneamente
def run_multiple_clients(num_clients):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(client_task, i) for i in range(num_clients)]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    run_multiple_clients(10)  # Número de clientes simultâneos
