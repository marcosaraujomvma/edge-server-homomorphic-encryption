import socket
import time
import threading
import csv
import psutil  # Para capturar a carga da CPU

HOST = '172.20.0.22'  # O servidor escuta em todas as interfaces
PORT = 65432      # Porta de comunicação
CSV_FILE = "execution_data.csv"  # Arquivo para salvar os tempos de execução

# Criar um lock para escrita segura no arquivo CSV
lock = threading.Lock()

def save_execution_time(client_addr, execution_time, cpu_load):
    """Salva o tempo de execução e carga da CPU em um arquivo CSV."""
    with lock:
        with open(CSV_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([client_addr, execution_time, cpu_load])

def handle_client(conn, addr):
    """Lida com um cliente, processando os números enviados e registrando o tempo de execução."""
    print(f"Conexão estabelecida com {addr}")

    try:
        start_time = time.time()  # Início da medição do tempo

        # Recebe os números do cliente
        data = conn.recv(1024).decode()
        if not data:
            return
        
        num1, num2 = map(int, data.split(","))
        result = num1 + num2  # Soma dos números

        # Tempo total de execução (receber e processar)
        execution_time = time.time() - start_time

        # Obtém a carga da CPU durante a operação
        cpu_load = psutil.cpu_percent(interval=1)  # Carga média em 1 segundo

        # Salva no arquivo CSV
        save_execution_time(addr, execution_time, cpu_load)

        # Envia o resultado de volta ao cliente
        conn.sendall(str(result).encode())

    except Exception as e:
        print(f"Erro ao processar cliente {addr}: {e}")

    finally:
        conn.close()
        print(f"Conexão encerrada com {addr}")

def main():
    """Inicia o servidor e aguarda conexões."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen()

        print(f"Servidor aguardando conexões na porta {PORT}...")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()  # Processa clientes em threads

if __name__ == "__main__":
    # Criar o arquivo CSV com cabeçalho, se não existir
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Client Address", "Execution Time (seconds)", "CPU Load (%)"])

    main()
