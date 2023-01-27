#!/app/virtualenv/bin/python3
from cryptography.fernet import Fernet
import os,json
from auth import config
_key_file='secret.key'
def generate_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    print(f"generated key: {key} to file {_key_file}")
    with open(_key_file, "wb") as key_file:
        key_file.write(key)

def load_key():
    """
    Load the previously generated key
    """
    return open(_key_file, "rb").read()

def encrypt_message(message):
    """
    Encrypts a message
    """
    key = load_key()
    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)
    # print(encrypted_message)
    return encrypted_message
def decrypt_message(message):
    """
        decrypts a message
        """
    key = load_key()
    f = Fernet(key)
    encrypted_message = f.decrypt(message.encode())
    # print(encrypted_message)
    return encrypted_message
def write_backup(_config):
    with open(f'{config["credential_file"]}.bak', 'w') as f:
        f.write(json.dumps(_config))

if __name__ == "__main__":

    if not  os.path.exists(_key_file):
        generate_key()
    if not os.path.exists(config['credential_file']):
        exit()
    else:

        _config ={}
        with open(config['credential_file'], 'r') as f:

            _config = json.loads(f.read())
            write_backup(_config)
            for k,v in _config.items():
                if type(v) != dict:
                    continue

                else:
                    print(f'processing {k} _config')
                    if 'password' in v:
                        _config[k]['password']=encrypt_message(_config[k]['password']).decode('utf-8')
            # f.write(json.dumps(_config))
        with open(config['credential_file'], 'w') as f:
            f.write(json.dumps(_config))
        # encrypt_message("encrypt this message")
        # decrypt_message('gAAAAABf1lvyRVVGq9O7xZ3mwhw49EenLXXCy5kuVRcRpgDCsFGGgYLiDqTAyp7CGerBIczXATZvc3kiN64Bpm9358JuKmvceawnEvZrgEGtoS8bXRGFeD8=')
