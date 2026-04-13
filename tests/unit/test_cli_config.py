from typer.testing import CliRunner

from pyjx2.cli.app import app

runner = CliRunner()

def test_cli_config_encrypt_command():
    raw_password = "test_cli_password"
    result_encrypt = runner.invoke(app, ["config", "encrypt-pass", raw_password])
    
    assert result_encrypt.exit_code == 0
    assert "Contrasena cifrada:" in result_encrypt.output
    assert "ENC:" in result_encrypt.output

def test_cli_config_decrypt_command():
    from pyjx2.infrastructure.security.encryption import SymmetricEncryptionService
    svc = SymmetricEncryptionService()
    raw_password = "test_cli_password"
    encrypted_token = svc.encrypt(raw_password)
    
    result_decrypt = runner.invoke(app, ["config", "decrypt-pass", encrypted_token])
    
    assert result_decrypt.exit_code == 0
    assert "Contrasena descifrada:" in result_decrypt.output
    assert raw_password in result_decrypt.output

def test_cli_config_decrypt_unencrypted_token():
    raw_password = "im_not_encrypted"
    result_decrypt = runner.invoke(app, ["config", "decrypt-pass", raw_password])
    
    assert result_decrypt.exit_code == 0
    assert "Aviso:" in result_decrypt.output
    # Should echo the raw text back
    assert raw_password in result_decrypt.output
