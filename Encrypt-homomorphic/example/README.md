# Homomorphic Federated Learning Demo (Host-to-Host)

This directory contains a modular implementation of Federated Learning using Paillier Homomorphic Encryption. It allows you to run a central server and multiple clients that communicate over TCP sockets.

## Structure

*   `fl_common.py`: Shared logic (Neural Network architecture, math helpers, networking protocol).
*   `fl_server.py`: The Server. Manages the global model, generates keys, collects encrypted updates, and aggregates them.
*   `fl_client.py`: The Client. Loads local data, trains locally, encrypts updates, and sends them to the server.

## Prerequisites

Ensure you are using the project's virtual environment which contains `phe` (Paillier Homomorphic Encryption) and `sklearn`.

```bash
# From the project root
source .venv/bin/activate
```

## Usage

### 1. Start the Server

Start the server first. You need to specify how many clients to wait for.

```bash
# Wait for 2 clients, run for 3 rounds
python fl_server.py --clients 2 --rounds 3
```

**Options:**
*   `--host`: IP to bind to (default 0.0.0.0).
*   `--port`: Port to listen on (default 65432).
*   `--clients`: Number of clients required to start rounds.
*   `--rounds`: Number of Federated Learning rounds.
*   `--hidden`: Size of the hidden layer (must match clients).

### 2. Start Clients

Open separate terminals (one for each client) and run the client script. **Important:** Give each client a unique `--id` so they load different parts of the dataset.

**Client 1:**
```bash
python fl_client.py --id 0
```

**Client 2:**
```bash
python fl_client.py --id 1
```

**Options:**
*   `--ip`: Server IP address (default 127.0.0.1).
*   `--port`: Server port (default 65432).
*   `--id`: Unique Client ID (int). Used to slice the MNIST dataset.
*   `--epochs`: Number of local training epochs per round.

## Notes

*   **Encryption Speed:** Paillier encryption is computationally intensive. The encryption step on the client side and the aggregation step on the server side might take some time (seconds to minutes depending on hardware and model size).
*   **Data:** The scripts automatically download MNIST using `sklearn.datasets.fetch_openml` if not cached.
