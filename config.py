import json
import os
from cryptography.fernet import Fernet

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
KEY_FILE = os.path.join(os.path.dirname(__file__), ".key")

DEFAULT_CONFIG = {
    "provider": "groq",
    "groq_api_key": "",
    "groq_model": "llama-3.3-70b-versatile",
    "ollama_host": "127.0.0.1",
    "ollama_port": 11434,
    "ollama_model": "llama3",
    "theme": "Dark",
    "language": "EN",
    "geometry": "1400x800"
}

def get_cipher():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return Fernet(key)

def encrypt_key(plain_text: str) -> str:
    if not plain_text:
        return ""
    cipher = get_cipher()
    return cipher.encrypt(plain_text.encode()).decode()

def decrypt_key(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        cipher = get_cipher()
        return cipher.decrypt(cipher_text.encode()).decode()
    except Exception:
        # Fallback if decryption fails (e.g. key changed or it was already plain text)
        return cipher_text

def load() -> dict:
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded_cfg = json.load(f)
        cfg.update(loaded_cfg)
    
    # Decrypt sensitive fields
    if cfg.get("groq_api_key"):
        cfg["groq_api_key"] = decrypt_key(cfg["groq_api_key"])
        
    return cfg

def save(cfg: dict):
    # Work on a copy to avoid encrypting the key in the live app state
    cfg_to_save = cfg.copy()
    if cfg_to_save.get("groq_api_key"):
        cfg_to_save["groq_api_key"] = encrypt_key(cfg_to_save["groq_api_key"])
        
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg_to_save, f, indent=2, ensure_ascii=False)
