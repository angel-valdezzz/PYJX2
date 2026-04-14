import abc


class EncryptionService(abc.ABC):
    """
    Port / Interface for encryption capabilities in the Application layer.
    """

    @abc.abstractmethod
    def encrypt(self, plain_text: str) -> str:
        """Encrypts a plaintext string and returns a securely encoded representation."""
        pass

    @abc.abstractmethod
    def decrypt(self, encrypted_text: str) -> str:
        """Decrypts a previously encrypted string back into its plaintext form."""
        pass
