from phe import paillier
import socket
import pickle
import struct

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
    raw_size = receive_all(conn, 4)  # Primeiro, recebe o tamanho (4 bytes)
    size = struct.unpack('!I', raw_size)[0]  # Desempacota o tamanho
    return receive_all(conn, size)  # Recebe os dados completos

# Configuração do cliente
HOST = '172.20.0.22'  # Endereço IP do servidor
PORT = 65432         # Porta do servidor

# Conecta ao servidor
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    # Recebe a chave pública do servidor
    public_key = pickle.loads(receive_data_with_size(s))

    # Números a serem somados
    m1 = 5
    m2 = 10

    # Criptografa os números usando a chave pública
    encrypted_m1 = public_key.encrypt(m1)
    encrypted_m2 = public_key.encrypt(m2)

    # Envia os dados criptografados para o servidor
    data = pickle.dumps([encrypted_m1, encrypted_m2])
    s.sendall(struct.pack('!I', len(data)) + data)

    # Recebe o resultado descriptografado do servidor
    #decrypted_sum = pickle.loads(receive_data_with_size(s))

    #print(f"Soma descriptografada recebida do servidor: {decrypted_sum}")
