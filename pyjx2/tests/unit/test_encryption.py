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
