import socket
import concurrent.futures
import random

HOST = '127.0.0.1'  # IP do servidor (local)
PORT = 65432        # Porta de comunicação
NUM_CLIENTS = 500   # Número de clientes simultâneos

def send_numbers(client_id):
    """Função que envia dois números ao servidor e recebe a soma."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        # Gera dois números aleatórios
        num1 = random.randint(1, 100)
        num2 = random.randint(1, 100)
        
        message = f"{num1},{num2}"
        client_socket.sendall(message.encode())

        # Recebe a resposta do servidor
        result = client_socket.recv(1024).decode()
        print(f"Cliente {client_id}: {num1} + {num2} = {result}")

def run_multiple_clients(num_clients):
    """Executa múltiplos clientes simultaneamente."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_clients) as executor:
        executor.map(send_numbers, range(num_clients))

if __name__ == "__main__":
    run_multiple_clients(NUM_CLIENTS)
