import numpy as np
import struct
import pickle

# ==========================================
# 1. HELPERS DE REDE
# ==========================================

def send_msg(sock, data):
    """Serializa (pickle) os dados e os envia com um prefixo de comprimento de 4 bytes."""
    msg = pickle.dumps(data)
    # Prefixar cada mensagem com um inteiro não assinado big-endian de 4 bytes (ordem de byte de rede)
    sock.sendall(struct.pack('>I', len(msg)) + msg)

def recv_msg(sock):
    """Recebe um prefixo de comprimento de 4 bytes e depois os dados serializados."""
    # Ler comprimento da mensagem
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Ler os dados da mensagem
    msg = recvall(sock, msglen)
    if not msg:
        return None
    return pickle.loads(msg)

def recvall(sock, n):
    """Função auxiliar para receber n bytes ou retornar None se EOF for atingido."""
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

# ==========================================
# 2. HELPERS MATEMÁTICOS
# ==========================================

def one_hot(y, num_classes=10):
    m = y.shape[0]
    y_int = y.astype(int)
    one_hot_matrix = np.zeros((m, num_classes))
    one_hot_matrix[np.arange(m), y_int] = 1
    return one_hot_matrix

def softmax(z):
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

def relu(z):
    return np.maximum(0, z)

def relu_deriv(z):
    return (z > 0).astype(float)

# ==========================================
# 3. CLASSE REDE NEURAL
# ==========================================

class MultiClassNN:
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        np.random.seed(42)
        # Inicialização He
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))

    def forward(self, X):
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = relu(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = softmax(self.z2)
        return self.a2

    def train(self, X, y, epochs=5, learning_rate=0.1, batch_size=32):
        m = X.shape[0]
        y_encoded = one_hot(y, num_classes=10)

        for _ in range(epochs):
            permutation = np.random.permutation(m)
            X_shuffled = X[permutation]
            y_shuffled = y_encoded[permutation]

            for i in range(0, m, batch_size):
                X_batch = X_shuffled[i : i + batch_size]
                y_batch = y_shuffled[i : i + batch_size]
                current_batch_size = X_batch.shape[0]

                # --- Forward ---
                z1 = np.dot(X_batch, self.W1) + self.b1
                a1 = relu(z1)
                z2 = np.dot(a1, self.W2) + self.b2
                a2 = softmax(z2)

                # --- Backward ---
                dz2 = a2 - y_batch
                dW2 = np.dot(a1.T, dz2) / current_batch_size
                db2 = np.sum(dz2, axis=0, keepdims=True) / current_batch_size

                da1 = np.dot(dz2, self.W2.T)
                dz1 = da1 * relu_deriv(z1)
                dW1 = np.dot(X_batch.T, dz1) / current_batch_size
                db1 = np.sum(dz1, axis=0, keepdims=True) / current_batch_size

                # --- Atualização ---
                self.W1 -= learning_rate * dW1
                self.b1 -= learning_rate * db1
                self.W2 -= learning_rate * dW2
                self.b2 -= learning_rate * db2

    def get_weights(self):
        return {
            "W1": self.W1.copy(),
            "b1": self.b1.copy(),
            "W2": self.W2.copy(),
            "b2": self.b2.copy(),
        }

    def set_weights(self, weights):
        self.W1, self.b1 = weights["W1"].copy(), weights["b1"].copy()
        self.W2, self.b2 = weights["W2"].copy(), weights["b2"].copy()

    def evaluate(self, X, y):
        """Calcula a precisão nos dados de teste"""
        predictions = self.forward(X)
        pred_labels = np.argmax(predictions, axis=1)
        return np.mean(pred_labels == y)