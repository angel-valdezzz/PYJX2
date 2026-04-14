from cryptography.fernet import InvalidToken
from pyjx2.infrastructure.security.encryption import SymmetricEncryptionService


def test_symmetric_encryption_encrypts_and_decrypts():
    service = SymmetricEncryptionService(key_seed="axa", prefix="ENC:")

    plain_text = "my_secret_jira_password"

    encrypted = service.encrypt(plain_text)

    assert encrypted != plain_text
    assert encrypted.startswith("ENC:")

    decrypted = service.decrypt(encrypted)

    assert decrypted == plain_text


def test_symmetric_encryption_ignores_already_encrypted():
    service = SymmetricEncryptionService(key_seed="axa", prefix="ENC:")
    already_encrypted = "ENC:something_already_encrypted"

    result = service.encrypt(already_encrypted)
    assert result == already_encrypted


def test_symmetric_encryption_decrypts_raw_text_as_raw():
    service = SymmetricEncryptionService(key_seed="axa", prefix="ENC:")
    raw = "im_not_encrypted"

    result = service.decrypt(raw)
    assert result == raw


def test_encryption_handles_empty_string():
    service = SymmetricEncryptionService()
    assert service.encrypt("") == ""
    assert service.decrypt("") == ""


def test_api_client_encryption_utils():
    from pyjx2.api.client import PyJX2

    plain_text = "test_api_password"
    encrypted = PyJX2.encrypt_password(plain_text)

    assert encrypted != plain_text
    assert encrypted.startswith("ENC:")

    decrypted = PyJX2.decrypt_password(encrypted)
    assert decrypted == plain_text


def test_api_client_decryption_ignores_raw_text():
    from pyjx2.api.client import PyJX2

    raw = "unencrypted_string"
    assert PyJX2.decrypt_password(raw) == raw


def test_encryption_fails_on_tampered_token():
    import pytest

    service = SymmetricEncryptionService(key_seed="axa", prefix="ENC:")
    plain_text = "test_password"
    encrypted = service.encrypt(plain_text)

    # Case 1: Tamper with character at the end (extra data after padding)
    tampered_end = encrypted + "A"
    with pytest.raises(ValueError, match="Invalid token: encoding or padding error"):
        service.decrypt(tampered_end)

    # Case 2: Tamper with character in the middle (HMAC mismatch or decoding error)
    # We change a character in the base64 part (not the prefix)
    middle_index = len("ENC:") + 10
    tampered_list = list(encrypted)
    # Swap a character
    tampered_list[middle_index] = "A" if tampered_list[middle_index] != "A" else "B"
    tampered_middle = "".join(tampered_list)

    with pytest.raises(InvalidToken):
        service.decrypt(tampered_middle)
