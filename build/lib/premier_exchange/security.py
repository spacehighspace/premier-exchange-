from cryptography.fernet import Fernet, InvalidToken


class SecretStore:
    """Encrypts credentials at rest; callers must supply a key from a secret manager."""

    def __init__(self, key: bytes):
        self._cipher = Fernet(key)
        self._secrets: dict[str, bytes] = {}

    def put(self, name: str, value: str) -> None:
        if not name or not value:
            raise ValueError("secret name and value are required")
        self._secrets[name] = self._cipher.encrypt(value.encode("utf-8"))

    def get(self, name: str) -> str:
        try:
            return self._cipher.decrypt(self._secrets[name]).decode("utf-8")
        except (KeyError, InvalidToken) as exc:
            raise KeyError("secret is unavailable") from exc

    def delete(self, name: str) -> None:
        self._secrets.pop(name, None)
