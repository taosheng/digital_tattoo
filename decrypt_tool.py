import argparse
import sys
import os
import base64

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    print("Error: 'pycryptodome' is required but not installed.")
    print("Please install it by running: pip install pycryptodome")
    sys.exit(1)

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypts data using AES CBC mode from IV + Ciphertext."""
    iv = encrypted_data[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size)

def main():
    parser = argparse.ArgumentParser(description="Digital Tattoo Local Decryption Tool")
    parser.add_argument("-k", "--key", required=True, help="Decryption key (exactly as provided when uploaded)")
    parser.add_argument("-i", "--input", required=True, help="Path to the downloaded encrypted file")
    parser.add_argument("-o", "--output", required=True, help="Path to save the decrypted file")
    
    args = parser.parse_args()

    input_path = args.input
    output_path = args.output
    key_str = args.key

    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    try:
        # The key is expected to be a string that we encode to bytes
        # The backend uses: key.encode('utf-8') where key is the generated token
        key_bytes = key_str.encode('utf-8')

        with open(input_path, 'rb') as f:
            file_data = f.read()

        # Attempt to detect if it's base64 encoded (which string tattoos are, but files usually aren't)
        # Assuming the input is the raw encrypted bytes from the blockchain
        try:
            decrypted_data = decrypt_data(file_data, key_bytes)
        except ValueError:
            # Maybe it's a base64 encoded string tattoo? Let's try base64 decode first
            try:
                decoded_b64 = base64.b64decode(file_data)
                decrypted_data = decrypt_data(decoded_b64, key_bytes)
            except Exception:
                # Raise the original ValueError if fallback fails
                raise ValueError("Padding is incorrect. Make sure you are using the correct key.")

        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

        print(f"Success! File decrypted and saved to: {output_path}")

    except ValueError as e:
        print(f"Decryption failed. Error: {e}")
        print("Please check if your decryption key is correct.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
