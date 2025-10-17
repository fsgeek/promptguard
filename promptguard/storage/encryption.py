"""
Encryption utilities for sensitive target LLM responses.

Uses AES-256 for encrypting response text before storage.
Key stored outside repository for security.
"""

import os
import base64
from pathlib import Path
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class ResponseEncryption:
    """
    AES-256 encryption for target LLM response text.

    Key storage: ~/.promptguard/target_responses.key

    Design:
    - Single key for all responses (simplifies key management)
    - Key outside repository (never committed)
    - Deterministic key path (discoverable for authorized users)
    """

    def __init__(self, key_path: Optional[str] = None):
        """
        Initialize encryption with key from file.

        Args:
            key_path: Path to encryption key file (default: ~/.promptguard/target_responses.key)

        Raises:
            ValueError: If key file doesn't exist
        """
        if key_path is None:
            key_path = Path.home() / ".promptguard" / "target_responses.key"
        else:
            key_path = Path(key_path)

        self.key_path = key_path

        # Load or generate key
        if not key_path.exists():
            raise ValueError(
                f"Encryption key not found at {key_path}. "
                f"Generate with: ResponseEncryption.generate_key('{key_path}')"
            )

        with open(key_path, 'rb') as f:
            self.key = f.read()

        if len(self.key) != 32:
            raise ValueError("Invalid key length. Expected 32 bytes for AES-256.")

    @staticmethod
    def generate_key(key_path: Optional[str] = None) -> Path:
        """
        Generate new AES-256 encryption key and save to file.

        Args:
            key_path: Where to save key (default: ~/.promptguard/target_responses.key)

        Returns:
            Path where key was saved
        """
        if key_path is None:
            key_path = Path.home() / ".promptguard" / "target_responses.key"
        else:
            key_path = Path(key_path)

        # Create directory if needed
        key_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate 32-byte (256-bit) key
        key = os.urandom(32)

        # Save with restrictive permissions
        with open(key_path, 'wb') as f:
            f.write(key)

        # Restrict permissions to owner only
        os.chmod(key_path, 0o600)

        return key_path

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string to base64-encoded ciphertext.

        Args:
            plaintext: Text to encrypt

        Returns:
            Base64-encoded ciphertext (includes IV)
        """
        # Generate random IV (initialization vector)
        iv = os.urandom(16)

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()

        # Pad plaintext to multiple of 16 bytes (PKCS7)
        plaintext_bytes = plaintext.encode('utf-8')
        padding_length = 16 - (len(plaintext_bytes) % 16)
        padded = plaintext_bytes + bytes([padding_length] * padding_length)

        # Encrypt
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        # Prepend IV to ciphertext and base64 encode
        encrypted_data = iv + ciphertext
        return base64.b64encode(encrypted_data).decode('ascii')

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt base64-encoded ciphertext to plaintext.

        Args:
            ciphertext: Base64-encoded encrypted text

        Returns:
            Decrypted plaintext
        """
        # Decode base64
        encrypted_data = base64.b64decode(ciphertext)

        # Extract IV (first 16 bytes)
        iv = encrypted_data[:16]
        ciphertext_bytes = encrypted_data[16:]

        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()

        # Decrypt
        padded = decryptor.update(ciphertext_bytes) + decryptor.finalize()

        # Remove padding (PKCS7)
        padding_length = padded[-1]
        plaintext_bytes = padded[:-padding_length]

        return plaintext_bytes.decode('utf-8')


def ensure_encryption_key(key_path: Optional[str] = None) -> Path:
    """
    Ensure encryption key exists, generating if needed.

    Args:
        key_path: Path to key file (default: ~/.promptguard/target_responses.key)

    Returns:
        Path to key file
    """
    if key_path is None:
        key_path = Path.home() / ".promptguard" / "target_responses.key"
    else:
        key_path = Path(key_path)

    if not key_path.exists():
        print(f"Generating new encryption key at {key_path}")
        ResponseEncryption.generate_key(key_path)

    return key_path
