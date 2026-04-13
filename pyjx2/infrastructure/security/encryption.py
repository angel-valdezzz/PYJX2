import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from pyjx2.application.services.encryption_service import EncryptionService


class SymmetricEncryptionService(EncryptionService):
    """
    Implements symmetric encryption using AES via Fernet.
    """

    def __init__(self, key_seed: str = "axa", prefix: str = "ENC:"):
        self.prefix = prefix
        # Use a constant salt to ensure the derived key is the same across application runs
        salt = b"pyjx2_static_salt_value"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_seed.encode("utf-8")))
        self.fernet = Fernet(key)

    def encrypt(self, plain_text: str) -> str:
        if not plain_text:
            return plain_text
        if plain_text.startswith(self.prefix):
            return plain_text  # Already encrypted

        encrypted_bytes = self.fernet.encrypt(plain_text.encode("utf-8"))
        return f"{self.prefix}{encrypted_bytes.decode('utf-8')}"

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return encrypted_text
        if not encrypted_text.startswith(self.prefix):
            return encrypted_text  # Not encrypted

        token_str = encrypted_text[len(self.prefix):]
        token_bytes = token_str.encode("utf-8")

        # Strict Base64 validation to prevent "excess data after padding" issues
        try:
            # Fernet uses urlsafe base64, so we replace characters correctly before validation
            standard_b64 = token_str.replace('-', '+').replace('_', '/')
            base64.b64decode(standard_b64, validate=True)
        except Exception:
            # If base64 is invalid or has trailing garbage, raise error
            # This is caught by the TUI/CLI and reported as a corrupted token
            raise ValueError("Invalid token: encoding or padding error")

        decrypted_bytes = self.fernet.decrypt(token_bytes)
        return decrypted_bytes.decode("utf-8")

