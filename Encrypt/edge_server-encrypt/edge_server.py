from phe import paillier
import socket
import pickle
import threading
import struct
import time
import csv
import psutil  # Importa a biblioteca psutil

# Função para receber todos os dados com base no tamanho esperado
def receive_all(conn, buffer_size=4096):
    data = b""
    while len(data) < buffer_size:
        packet = conn.recv(buffer_size - len(data))
        if not packet:
            break
        data += packet
    return data

# Função para receber dados com tamanho prefixado
def receive_data_with_size(conn):
    raw_size = receive_all(conn, 4)  # Recebe o tamanho (4 bytes)
    size = struct.unpack('!I', raw_size)[0]  # Desempacota o tamanho
    return receive_all(conn, size)  # Recebe os dados completos

# Função para lidar com cada cliente
def handle_client(conn, addr, public_key, private_key, log_file):
    print(f"Conectado por {addr}")

    try:
        # Envia a chave pública para o cliente
        data = pickle.dumps(public_key)
        conn.sendall(struct.pack('!I', len(data)) + data)

        # Recebe os dados criptografados do cliente
        encrypted_data = pickle.loads(receive_data_with_size(conn))

        # Mede o tempo de execução da soma homomórfica
        start_time = time.time()
        encrypted_sum = encrypted_data[0] + encrypted_data[1]
        decrypted_sum = private_key.decrypt(encrypted_sum)
        execution_time = time.time() - start_time

        # Obtém a carga da CPU durante a operação
        cpu_load = psutil.cpu_percent(interval=1)  # Carga média em 1 segundo

        # Registra o tempo de execução e a carga da CPU no arquivo CSV
        with open(log_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([addr, execution_time, cpu_load])

        # Envia o resultado de volta ao cliente
        #result = pickle.dumps(decrypted_sum)
        #conn.sendall(struct.pack('!I', len(result)) + result)

        print(f"Soma descriptografada enviada para {addr}: {decrypted_sum} (Tempo: {execution_time:.6f}s, CPU: {cpu_load}%)")

    except Exception as e:
        print(f"Erro com o cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"Conexão com {addr} encerrada.")

# Configuração do servidor
HOST = '172.20.0.22'  # Endereço IP local
PORT = 65432         # Porta para conexão
LOG_FILE = 'execution_datacsv'  # Arquivo para salvar os tempos e carga da CPU

# Geração das chaves Paillier
public_key, private_key = paillier.generate_paillier_keypair()

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
        thread = threading.Thread(target=handle_client, args=(conn, addr, public_key, private_key, LOG_FILE))
        thread.start()
