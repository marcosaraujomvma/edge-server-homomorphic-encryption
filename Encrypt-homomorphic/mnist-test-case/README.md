# Demonstração de Aprendizado Federado Homomórfico usando o Conjunto de Dados MNIST

Este diretório contém uma implementação modular de Aprendizado Federado usando Criptografia Homomórfica de Paillier. Ele permite que você execute um servidor central e vários clientes que se comunicam por soquetes TCP.

## Estrutura

*   `fl_paillier_common.py`: Lógica compartilhada (arquitetura de Rede Neural, auxiliares matemáticos, protocolo de rede).
*   `fl_paillier_server.py`: O Servidor. Gerencia o modelo global, gera chaves, coleta atualizações criptografadas e as agrega.
*   `fl_paillier_client.py`: O Cliente. Carrega dados locais, treina localmente, criptografa atualizações e as envia para o servidor.

## Requisitos

Você pode executar o comando abaixo para instalar todas as bibliotecas necessárias para o programa:

```bash
# Do diretório de exemplo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Quando terminar de executar o programa, desative o Ambiente Virtual usando:

```bash
deactivate
```

## Uso

### 1. Iniciar o Servidor

**Inicie o servidor primeiro**. Você precisa especificar quantos clientes aguardar.

```bash
# Aguardar 2 clientes, executar por 3 rodadas
python fl_paillier_server.py --clients 2 --rounds 3
```

**Opções:**
*   `--host`: IP para vincular (padrão 0.0.0.0).
*   `--port`: Porta para escutar (padrão 65432).
*   `--clients`: Número de clientes necessários para iniciar as rodadas.
*   `--rounds`: Número de rodadas de Aprendizado Federado.
*   `--hidden`: Tamanho da camada oculta (deve corresponder aos clientes).
*   `--key-size`: Tamanho da chave do Criptossistema Paillier

### 2. Iniciar Clientes

Execute o script do cliente. Dê a cada cliente um `--id` único para que eles carreguem diferentes partes do conjunto de dados.

**Cliente 1:**
```bash
python fl_paillier_client.py --id 0
```

**Cliente 2:**
```bash
python fl_paillier_client.py --id 1
```

**Opções:**
*   `--ip`: Endereço IP do servidor (padrão 127.0.0.1).
*   `--port`: Porta do servidor (padrão 65432).
*   `--id`: ID único do Cliente (int). Usado para fatiar o conjunto de dados MNIST.
*   `--epochs`: Número de épocas de treinamento local por rodada.

## Notas

*   **Velocidade de Criptografia:** A criptografia Paillier é computacionalmente intensiva para tamanhos de chave recomendados (>=2048). A etapa de criptografia no lado do cliente e a etapa de agregação no lado do servidor podem levar algum tempo (segundos a minutos dependendo do hardware e tamanho do modelo).
*   **Dados:** Os scripts baixam automaticamente o MNIST usando `sklearn.datasets.fetch_openml` se não estiver em cache.