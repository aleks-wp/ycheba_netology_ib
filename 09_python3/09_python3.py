import time
import hashlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def make_key(password):

#Получаем ключ AES-256 из пароля.

    return hashlib.sha256(password.encode()).digest()


def encrypt_text(text, password):

# Шифруем текст с помощью AES-256.

    key = make_key(password)
    cipher = AES.new(key, AES.MODE_ECB)

    encrypted_data = cipher.encrypt(pad(text.encode(), AES.block_size))

    return encrypted_data


def try_decrypt(encrypted_data, password, expected_text):

    try:
        key = make_key(password)
        cipher = AES.new(key, AES.MODE_ECB)

        decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        decrypted_text = decrypted_data.decode("utf-8")

        if decrypted_text == expected_text:
            return decrypted_text

        return None

    except (ValueError, UnicodeDecodeError):
        return None


def brute_force(encrypted_data, expected_text):

#Перебор трёхзначных паролей от 100 до 999.
    attempts = 0

    for i in range(100, 1000):
        password = str(i)
        attempts += 1

        print(f"[{attempts}] Пробуем пароль: {password}")

        decrypted_text = try_decrypt(encrypted_data, password, expected_text)

        if decrypted_text is not None:
            print("Пароль подошёл!")
            return password, decrypted_text, attempts
        else:
            print("Не подошёл.")

    return None, None, attempts


if __name__ == "__main__":
    text = "Top Secret"
    password = "123"

    encrypted_data = encrypt_text(text, password)

    print("Зашифрованные данные в hex:")
    print(encrypted_data.hex())
    print()

    print("Начинаем brute force атаку...")
    print("Перебираются трёхзначные пароли от 100 до 999")
    print()

    start_time = time.time()

    found_password, found_text, attempts = brute_force(
        encrypted_data,
        text
    )

    end_time = time.time()
    duration = end_time - start_time

    print()

    if found_password is not None:
        print("Пароль найден!")
        print("Пароль:", found_password)
        print("Расшифрованный текст:", found_text)
    else:
        print("Пароль не найден.")

    print()
    print(f"Количество попыток: {attempts}")
    print(f"Время: {duration:.3f} сек.")