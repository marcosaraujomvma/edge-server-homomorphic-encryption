import socket
import argparse
import numpy as np
from phe import paillier
import fl_paillier_common as fl_common
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split
import time


class FederatedServer:
    def __init__(
        self,
        host,
        port,
        num_clients,
        num_rounds,
        input_dim,
        hidden_dim,
        classes,
        n_length,
    ):
        self.host = host
        self.port = port
        self.num_clients = num_clients
        self.num_rounds = num_rounds

        # Configuração do Modelo
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.classes = classes
        self.global_model = fl_common.MultiClassNN(
            input_dim, hidden_dim, classes
        )

        # Configuração de Criptografia
        print("[Server] Generating Paillier Keypair... this may take a moment.")
        self.public_key, self.private_key = paillier.generate_paillier_keypair(
            n_length=n_length
        )
        print("[Server] Keys generated.")

        # Dados de Teste (para avaliação)
        self.X_test = None
        self.y_test = None

    def load_test_data(self):
        print("[Server] Loading MNIST test data for server-side evaluation...")
        # Carregar um pequeno subconjunto para avaliação rápida
        mnist = fetch_openml("mnist_784", version=1, parser="auto")
        # Pegar os últimos 2000 para teste para evitar sobreposição se os clientes pegarem do início (divisão ingênua)
        X = mnist.data.iloc[-2000:].values / 255.0
        y = mnist.target.iloc[-2000:].astype(int).values
        self.X_test = X
        self.y_test = y
        print(f"[Server] Loaded {len(self.X_test)} test samples.")

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(self.num_clients)

        print(f"[Server] Listening on {self.host}:{self.port}")
        print(f"[Server] Waiting for {self.num_clients} clients to connect...")

        clients = []
        while len(clients) < self.num_clients:
            client_sock, addr = server_socket.accept()
            print(f"[Server] Client connected: {addr}")
            clients.append(client_sock)

        print("[Server] All clients connected. Starting Federated Learning.")

        try:
            # 1. Enviar Chave Pública para todos os clientes
            print("[Server] Broadcasting Public Key...")
            for sock in clients:
                fl_common.send_msg(sock, {"type": "PUB_KEY", "key": self.public_key})

            # 2. Loop de Aprendizado Federado
            for round_num in range(self.num_rounds):
                print(f"\n=== ROUND {round_num + 1}/{self.num_rounds} ===")

                # A. Transmitir Modelo Global
                global_weights = self.global_model.get_weights()
                print("[Server] Broadcasting Global Model...")
                for sock in clients:
                    fl_common.send_msg(
                        sock, {"type": "WEIGHTS", "weights": global_weights}
                    )

                # B. Receber Atualizações Criptografadas
                encrypted_updates = []
                client_sizes = []

                print("[Server] Waiting for updates...")
                for i, sock in enumerate(clients):
                    msg = fl_common.recv_msg(sock)
                    if msg and msg["type"] == "UPDATE":
                        encrypted_updates.append(msg["weights"])
                        client_sizes.append(msg["samples"])
                        print(
                            f"[Server] Received update from Client {i + 1} ({msg['samples']} samples)"
                        )
                    else:
                        print(f"[Server] Error: Invalid message from Client {i + 1}")

                # C. Agregação
                if encrypted_updates:
                    self.aggregate_encrypted(encrypted_updates, client_sizes)

                # D. Avaliação
                if self.X_test is not None:
                    acc = self.global_model.evaluate(self.X_test, self.y_test)
                    print(
                        f"📊 Global Model Accuracy (Round {round_num + 1}): {acc:.2%}"
                    )

            # 3. Finalizar
            print("\n[Server] Training Complete. Sending termination signal.")
            for sock in clients:
                fl_common.send_msg(sock, {"type": "DONE"})

        finally:
            for sock in clients:
                sock.close()
            server_socket.close()
            print("[Server] Closed.")

    def aggregate_encrypted(self, encrypted_updates, client_sizes):
        print("[Server] Aggregating Encrypted weights...")
        total_samples = sum(client_sizes)
        if total_samples == 0:
            return

        # Inicializar estrutura baseada na primeira atualização
        first_update = encrypted_updates[0]
        agg_encrypted = {}

        # Inicializar acumuladores
        for key in first_update:
            if "_shape" in key:
                agg_encrypted[key] = first_update[key]  # Copiar informação de forma (shape)
                continue

            # Começar com 0
            num_params = len(first_update[key])
            agg_encrypted[key] = [0] * num_params

        # Soma Ponderada
        for i, update in enumerate(encrypted_updates):
            factor = client_sizes[i] / total_samples

            for key in update:
                if "_shape" in key:
                    continue

                encrypted_list = update[key]
                for idx, enc_val in enumerate(encrypted_list):
                    # w_i * (n_i/N)
                    # Otimização: No Paillier real, multiplicamos o valor criptografado por um escalar simples (plain)
                    weighted = enc_val * factor

                    if i == 0:
                        agg_encrypted[key][idx] = weighted
                    else:
                        agg_encrypted[key][idx] = agg_encrypted[key][idx] + weighted

        # Descriptografar
        print("[Server] Decrypting aggregated model...")
        decrypted_weights = {}
        for key in agg_encrypted:
            if "_shape" in key:
                continue

            shape = agg_encrypted[key + "_shape"]
            encrypted_list = agg_encrypted[key]

            decrypted_flat = [self.private_key.decrypt(x) for x in encrypted_list]
            decrypted_weights[key] = np.array(decrypted_flat).reshape(shape)

        self.global_model.set_weights(decrypted_weights)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Federated Learning Server (Homomorphic)"
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=65432, help="Bind port")
    parser.add_argument(
        "--clients", type=int, default=2, help="Number of expected clients"
    )
    parser.add_argument("--rounds", type=int, default=3, help="Number of FL rounds")
    parser.add_argument("--hidden", type=int, default=32, help="Hidden layer size")
    parser.add_argument(
        "--key-size", type=int, default=2048, help="Paillier Cryptosystem key size"
    )

    args = parser.parse_args()

    server = FederatedServer(
        args.host,
        args.port,
        args.clients,
        args.rounds,
        784,
        args.hidden,
        10,
        args.key_size,
    )
    server.load_test_data()
    server.start()