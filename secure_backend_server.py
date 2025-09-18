from flask import Flask, request, jsonify
import rsa
import os

# Decrypt and print user data before SecureBackend __init__
def debug_print_decrypted_user_data():
    key_dir = 'keys'
    data_file = 'user_data.enc'
    public_key_path = os.path.join(key_dir, 'public.pem')
    private_key_path = os.path.join(key_dir, 'private.pem')
    if os.path.exists(private_key_path) and os.path.exists(data_file):
        try:
            with open(private_key_path, 'rb') as f:
                privkey = rsa.PrivateKey.load_pkcs1(f.read())
            with open(data_file, 'rb') as f:
                encrypted = f.read()
            decrypted = rsa.decrypt(encrypted, privkey)
            email, password = decrypted.decode('utf-8').split('\n')
            print(f'DEBUG: Decrypted user data -> Email: {email}, Password: {password}')
        except Exception as e:
            print(f'DEBUG: Failed to decrypt user data: {e}')
    else:
        print('DEBUG: No private key or user data file found for decryption.')

debug_print_decrypted_user_data()

app = Flask(__name__)
backend = None

class SecureBackend:
    def __init__(self, key_dir='keys', enc_file='user_data.enc', plain_file='user_data.txt'):
        self.key_dir = key_dir
        self.enc_file = enc_file
        self.plain_file = plain_file
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

    def store_user(self, username, email, password):
        # Check for duplicates before storing
        if os.path.exists(self.enc_file):
            with open(self.enc_file, 'rb') as f:
                content = f.read()
            entries = content.split(b'\n---\n')
            for entry in entries:
                if not entry.strip():
                    continue
                try:
                    decrypted = rsa.decrypt(entry, self.private_key)
                    existing_username, existing_email, existing_password = decrypted.decode('utf-8').split('\n')
                    if existing_username == username:
                        return False, 'Username already in use'
                    if existing_email == email:
                        return False, 'Email already in use'
                    if existing_password == password:
                        return False, 'Password already in use'
                except Exception:
                    continue
        # Append plaintext for debugging
        with open(self.plain_file, 'a', encoding='utf-8') as f:
            f.write(f'username:{username}\nemail:{email}\npassword:{password}\n---\n')
        # Append encrypted
        data = f'{username}\n{email}\n{password}'.encode('utf-8')
        encrypted = rsa.encrypt(data, self.public_key)
        with open(self.enc_file, 'ab') as f:
            f.write(encrypted + b'\n---\n')
        return True, 'Account created successfully'

    def find_user(self, username, email, password):
        if not os.path.exists(self.enc_file):
            return None, None, None
        with open(self.enc_file, 'rb') as f:
            content = f.read()
        entries = content.split(b'\n---\n')
        for entry in entries:
            if not entry.strip():
                continue
            try:
                decrypted = rsa.decrypt(entry, self.private_key)
                entry_username, entry_email, entry_password = decrypted.decode('utf-8').split('\n')
                # Only allow login if username, email, and password match the same entry
                if entry_username == username and entry_email == email and entry_password == password:
                    return entry_username, entry_email, entry_password
            except Exception:
                continue
        return None, None, None

    def load_user(self):
        if not os.path.exists(self.enc_file):
            return None, None, None
        with open(self.enc_file, 'rb') as f:
            encrypted = f.read()
        try:
            decrypted = rsa.decrypt(encrypted, self.private_key)
            username, email, password = decrypted.decode('utf-8').split('\n')
            return username, email, password
        except Exception:
            return None, None, None

backend = SecureBackend()

@app.route('/store_user', methods=['POST'])
def store_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    if not username or not email or not password:
        return jsonify({'error': 'Missing username, email, or password'}), 400
    success, message = backend.store_user(username, email, password)
    if not success:
        return jsonify({'error': message}), 409
    return jsonify({'status': 'success'})

@app.route('/public_key', methods=['POST'])
def get_public_key():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    # Authenticate user
    found_username, found_email, found_password = backend.find_user(username, email, password)
    if username == found_username and email == found_email and password == found_password:
        pubkey = backend.public_key.save_pkcs1().decode('utf-8')
        return jsonify({'public_key': pubkey, 'username': found_username})
    else:
        return jsonify({'error': 'Incorrect username, email, or password'}), 401

@app.route('/load_user', methods=['GET'])
def load_user():
    username, email, password = backend.load_user()
    if username and email and password:
        return jsonify({'username': username, 'email': email, 'password': password})
    else:
        return jsonify({'error': 'No user found'}), 404

@app.route('/decrypt_user_data', methods=['GET'])
def decrypt_user_data():
    username, email, password = backend.load_user()
    return jsonify({'username': username, 'email': email, 'password': password})

if __name__ == '__main__':
    app.run(port=5000)
