from phe import paillier

# Geração das chaves pública e privada
public_key, private_key = paillier.generate_paillier_keypair()

# Números que queremos somar
m1 = 5
m2 = 10

# Criptografando os números
encrypted_m1 = public_key.encrypt(m1)
encrypted_m2 = public_key.encrypt(m2)

print(f"Criptografia de {m1}: {encrypted_m1.ciphertext()}")
print(f"Criptografia de {m2}: {encrypted_m2.ciphertext()}")

# Soma homomórfica dos valores criptografados
encrypted_sum = encrypted_m1 + encrypted_m2

# Descriptografando o resultado
decrypted_sum = private_key.decrypt(encrypted_sum)

print(f"Soma descriptografada: {decrypted_sum}")
