def write_decrypted_user_data_txt():
    key_dir = 'keys'
    data_file = 'user_data.enc'
    txt_file = 'decrypted_user_data.txt'
    private_key_path = os.path.join(key_dir, 'private.pem')
    if os.path.exists(private_key_path) and os.path.exists(data_file):
        try:
            import rsa
            with open(private_key_path, 'rb') as f:
                privkey = rsa.PrivateKey.load_pkcs1(f.read())
            with open(data_file, 'rb') as f:
                encrypted = f.read()
            decrypted = rsa.decrypt(encrypted, privkey)
            email, password = decrypted.decode('utf-8').split('\n')
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(f'Email: {email}\nPassword: {password}\n')
            print(f'DEBUG: Decrypted user data written to {txt_file}')
        except Exception as e:
            print(f'DEBUG: Failed to decrypt user data: {e}')
    else:
        print('DEBUG: No private key or user data file found for decryption.')

write_decrypted_user_data_txt()
import rsa
import os

class SecureBackend:
    def __init__(self, key_dir='keys', data_file='user_data.enc'):
        self.key_dir = key_dir
        self.data_file = data_file
        self.public_key_path = os.path.join(key_dir, 'public.pem')
        self.private_key_path = os.path.join(key_dir, 'private.pem')
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
        if not (os.path.exists(self.public_key_path) and os.path.exists(self.private_key_path)):
            self.generate_keys()
        self.public_key = self.load_key(self.public_key_path)
        self.private_key = self.load_key(self.private_key_path, private=True)

    def generate_keys(self):
        (pubkey, privkey) = rsa.newkeys(2048)
        with open(self.public_key_path, 'wb') as f:
            f.write(pubkey.save_pkcs1('PEM'))
        with open(self.private_key_path, 'wb') as f:
            f.write(privkey.save_pkcs1('PEM'))

    def load_key(self, path, private=False):
        with open(path, 'rb') as f:
            key_data = f.read()
        if private:
            return rsa.PrivateKey.load_pkcs1(key_data)
        else:
            return rsa.PublicKey.load_pkcs1(key_data)

    def store_user(self, email, password):
        data = f'{email}\n{password}'.encode('utf-8')
        encrypted = rsa.encrypt(data, self.public_key)
        with open(self.data_file, 'wb') as f:
            f.write(encrypted)

    def load_user(self):
        if not os.path.exists(self.data_file):
            return None, None
        with open(self.data_file, 'rb') as f:
            encrypted = f.read()
        try:
            decrypted = rsa.decrypt(encrypted, self.private_key)
            email, password = decrypted.decode('utf-8').split('\n')
            return email, password
        except Exception:
            return None, None
