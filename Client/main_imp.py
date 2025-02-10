import random
from math import gcd
from sympy import isprime, nextprime

# Função para calcular o Mínimo Comum Múltiplo (LCM)
def lcm(a, b):
    return abs(a * b) // gcd(a, b)

# Função para calcular o inverso modular
def modinv(a, m):
    m0, x0, x1 = m, 0, 1
    if m == 1:
        return 0
    while a > 1:
        q = a // m
        m, a = a % m, m
        x0, x1 = x1 - q * x0, x0
    if x1 < 0:
        x1 += m0
    return x1

# Função para gerar um primo seguro de tamanho especificado
def generate_safe_prime(bit_length):
    prime = random.getrandbits(bit_length)
    prime = nextprime(prime)  # Garante que seja primo
    while not isprime(prime):
        prime = nextprime(prime)
    return prime

# Geração de chaves Paillier com verificação adequada
def generate_paillier_keypair(bit_length):
    p = generate_safe_prime(bit_length // 2)
    q = generate_safe_prime(bit_length // 2)
    if p == q:
        q = generate_safe_prime(bit_length // 2)  # Garante que p != q

    n = p * q
    lam = lcm(p - 1, q - 1)
    g = n + 1
    mu = modinv(lam, n)
    return (n, g), (lam, mu)

# Criptografar um número
def encrypt(public_key, plaintext):
    n, g = public_key
    r = random.randint(1, n - 1)
    while gcd(r, n) != 1:
        r = random.randint(1, n - 1)
    c = (pow(g, plaintext, n * n) * pow(r, n, n * n)) % (n * n)
    return c

# Descriptografar um número
def decrypt(private_key, public_key, ciphertext):
    n, g = public_key
    lam, mu = private_key
    x = pow(ciphertext, lam, n * n) - 1
    plaintext = ((x // n) * mu) % n
    return plaintext

# Exemplo de uso
bit_length = 4096  # Controla o tamanho das chaves
public_key, private_key = generate_paillier_keypair(bit_length)

# Criptografar dois números
num1 = 10
num2 = 5

encrypted_num1 = encrypt(public_key, num1)
encrypted_num2 = encrypt(public_key, num2)

print(f"Número 1 criptografado: {encrypted_num1}")
print(f"Número 2 criptografado: {encrypted_num2}")

# Somar os números criptografados
encrypted_sum = (encrypted_num1 * encrypted_num2) % (public_key[0] ** 2)

# Descriptografar o resultado
decrypted_sum = decrypt(private_key, public_key, encrypted_sum)

print(f"Resultado da soma após descriptografar: {decrypted_sum}")