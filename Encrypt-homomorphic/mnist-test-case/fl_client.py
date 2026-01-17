import socket
import argparse
import pickle
import numpy as np
import fl_common
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split


class FederatedClient:
    def __init__(self, server_ip, server_port, client_id, hidden_dim, classes):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_id = client_id

        # Model
        self.model = fl_common.MultiClassNN(784, hidden_dim, classes)

        # State
        self.public_key = None
        self.X_train = None
        self.y_train = None

    def load_data(self, samples=1000):
        print(f"[Client {self.client_id}] Loading local data...")
        mnist = fetch_openml("mnist_784", version=1, parser="auto")

        # Simple partitioning based on client ID to simulate distributed data
        # Offset to avoid the test set used by server (last 2000)
        start_idx = self.client_id * samples
        end_idx = start_idx + samples

        # Safety check
        if end_idx > 68000:
            print("Warning: Index out of bounds, wrapping around")
            start_idx = start_idx % 60000
            end_idx = start_idx + samples

        self.X_train = mnist.data.iloc[start_idx:end_idx].values / 255.0
        self.y_train = mnist.target.iloc[start_idx:end_idx].astype(int).values
        print(f"[Client {self.client_id}] Loaded {len(self.X_train)} samples.")

    def start(self, local_epochs):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.server_ip, self.server_port))
            print(
                f"[Client {self.client_id}] Connected to {self.server_ip}:{self.server_port}"
            )

            while True:
                msg = fl_common.recv_msg(sock)
                if not msg:
                    break

                if msg["type"] == "PUB_KEY":
                    print(f"[Client {self.client_id}] Received Public Key.")
                    self.public_key = msg["key"]

                elif msg["type"] == "WEIGHTS":
                    print(
                        f"[Client {self.client_id}] Received Global Model. Starting Local Training..."
                    )
                    # 1. Update Local Model
                    self.model.set_weights(msg["weights"])

                    # 2. Train Locally
                    self.model.train(self.X_train, self.y_train, epochs=local_epochs)

                    # 3. Encrypt Weights
                    print(
                        f"[Client {self.client_id}] Encrypting weights (this takes time)..."
                    )
                    encrypted_weights = self.encrypt_weights(self.model.get_weights())

                    # 4. Send Update
                    response = {
                        "type": "UPDATE",
                        "weights": encrypted_weights,
                        "samples": len(self.X_train),
                    }
                    fl_common.send_msg(sock, response)
                    print(f"[Client {self.client_id}] Update sent.")

                elif msg["type"] == "DONE":
                    print(f"[Client {self.client_id}] Training finished by server.")
                    break

        except ConnectionRefusedError:
            print(
                f"[Client {self.client_id}] Connection refused. Is the server running?"
            )
        except Exception as e:
            print(f"[Client {self.client_id}] Error: {e}")
        finally:
            sock.close()

    def encrypt_weights(self, weights):
        if not self.public_key:
            raise ValueError("Public key not received yet!")

        encrypted_dict = {}
        for key, val in weights.items():
            flat_val = val.flatten()
            # Encrypt each scalar
            encrypted_dict[key] = [self.public_key.encrypt(float(x)) for x in flat_val]
            encrypted_dict[key + "_shape"] = val.shape

        return encrypted_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Federated Learning Client (Homomorphic)"
    )
    parser.add_argument("--ip", type=str, default="127.0.0.1", help="Server IP")
    parser.add_argument("--port", type=int, default=65432, help="Server Port")
    parser.add_argument(
        "--id", type=int, required=True, help="Client ID (for data partition)"
    )
    parser.add_argument("--epochs", type=int, default=1, help="Local training epochs")
    parser.add_argument("--hidden", type=int, default=32, help="Hidden layer size")

    args = parser.parse_args()

    client = FederatedClient(args.ip, args.port, args.id, args.hidden, 10)
    client.load_data()
    client.start(args.epochs)
