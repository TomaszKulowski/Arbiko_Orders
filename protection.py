import base64
import gzip

import cryptography.fernet
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class Protection:
    def __init__(self, password, name):
        self.password = bytes(password)
        self.name = name

    def key_creation(self) -> cryptography.fernet.Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            salt=b'\xfaz\xb5\xf2|\xa1z\xa9\xfe\xd1F@1\xaa\x8a\xc2',
            iterations=1024,
            length=32,
            backend=default_backend(),
        )

        key = Fernet(base64.urlsafe_b64encode(kdf.derive(self.password)))
        return key

    def encrypt(self, data):
        key = self.key_creation()
        safe = key.encrypt(data)
        return safe

    def decrypt(self, data):
        key = self.key_creation()
        result = key.decrypt(data)
        return result

    def decrypt_file(self) -> str:
        file = gzip.open(self.name.name, 'rb')
        data = file.read()
        file.close()

        content = self.decrypt(data)
        content = content.decode('utf-8')

        return content

    def save_database_dump(self, database_dump):
        encrypted_data = self.encrypt(database_dump)

        file = gzip.open(self.name, 'wb')
        file.write(encrypted_data)
        file.close()
