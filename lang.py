import json
import os

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")
AVAILABLE_LANGS = {"EN": "en", "SK": "sk"}
DEFAULT_LANG = "EN"


class LangManager:
    def __init__(self, lang_code: str = DEFAULT_LANG):
        self._strings: dict = {}
        self.load(lang_code)

    def load(self, lang_code: str):
        filename = AVAILABLE_LANGS.get(lang_code, "en") + ".json"
        filepath = os.path.join(LOCALES_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            self._strings = json.load(f)
        self.current = lang_code

    def t(self, key: str) -> str:
        return self._strings.get(key, f"[{key}]")
