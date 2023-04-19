"""The collections of the tools to encrypt and decrypt the database file."""
import base64
import gzip

import cryptography.fernet
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class Protection:
    """The class to encrypt and decrypt database.

    Methods:
        key_creation(): create the key for the encryption
        encrypt(data: str): encrypt passed data and return it
        decrypt(data: str): decrypt passed data and return it
        decrypt_file(): decrypt database file and return content
        save_database_dump(database_dump: str): encrypt database dump and save to the file
    """
    def __init__(self, password: str, name: str):
        """Construct all the necessary attributes for the protection object.

        Args:
            password (str): database password
            name (str): database name
        """
        self.password = bytes(password)
        self.name = name

    def key_creation(self) -> cryptography.fernet.Fernet:
        """Create the key for the encryption.

        Returns:
            object (cryptographt.fernet.Fernet): key for encrypt and decrypt data
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            salt=b'\xfaz\xb5\xf2|\xa1z\xa9\xfe\xd1F@1\xaa\x8a\xc2',
            iterations=1024,
            length=32,
            backend=default_backend(),
        )

        key = Fernet(base64.urlsafe_b64encode(kdf.derive(self.password)))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt and return passed data.

        Args:
            data (str): data to encrypt

        Returns:
            (str): encrypted data
        """
        key = self.key_creation()
        safe = key.encrypt(data)
        return safe

    def decrypt(self, data: str) -> str:
        """Decrypt and return passed data.

        Args:
            data (str): data to decrypt

        Returns:
            (str): decrypted data
        """
        key = self.key_creation()
        result = key.decrypt(data)
        return result

    def decrypt_file(self) -> str:
        """Open, decrypt and return database content.

        Returns:
            (str): database content
        """
        file = gzip.open(self.name.name, 'rb')
        data = file.read()
        file.close()

        content = self.decrypt(data)
        content = content.decode('utf-8')

        return content

    def save_database_dump(self, database_dump: str):
        """Encrypt and save to the file passed database dump."""
        encrypted_data = self.encrypt(database_dump)

        file = gzip.open(self.name, 'wb')
        file.write(encrypted_data)
        file.close()
