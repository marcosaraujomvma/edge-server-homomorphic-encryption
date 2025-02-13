import socket
import threading
import struct
import time
import csv
import psutil
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

# Função para receber todos os bytes esperados
def receive_all(conn, expected_size):
    """Recebe todos os bytes esperados do cliente."""
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

# Gera par de chaves ECC
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Serializa a chave pública para envio
public_key_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

def handle_client(conn, addr, log_file):
    print(f"Conectado por {addr}")

    try:
        # Envia a chave pública para o cliente
        conn.sendall(struct.pack('!I', len(public_key_pem)) + public_key_pem)

        # Recebe os dados criptografados do cliente
        encrypted_data = receive_data_with_size(conn)
        if not encrypted_data:
            print(f"Erro: não recebeu dados válidos de {addr}")
            return

        # Descriptografa os dados
        decrypted_message = private_key.decrypt(
            encrypted_data,
            ec.ECIESHKDFRecipientInfo(
                hashes.SHA256()
            )
        )
        
        num1, num2 = map(int, decrypted_message.decode().split(","))
        start_time = time.time()

        # Realiza a soma dos valores recebidos
        result = num1 + num2
        execution_time = time.time() - start_time

        # Obtém a carga da CPU durante a operação
        cpu_load = psutil.cpu_percent(interval=0.1)

        # Registra no log
        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([addr, execution_time, cpu_load])

        print(f"Soma enviada para {addr}: {result} (Tempo: {execution_time:.6f}s, CPU: {cpu_load}%)")

    except Exception as e:
        print(f"Erro com o cliente {addr}: {e}")

    finally:
        conn.close()
        print(f"Conexão com {addr} encerrada.")

# Configuração do servidor
HOST = '0.0.0.0'
PORT = 65432
LOG_FILE = 'execution_data_ecc.csv'

# Criação do arquivo CSV com cabeçalho
with open(LOG_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Client Address', 'Execution Time (seconds)', 'CPU Load (%)'])

# Inicialização do servidor socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Servidor aguardando conexões...")

while True:
    conn, addr = s.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr, LOG_FILE))
    thread.start()
