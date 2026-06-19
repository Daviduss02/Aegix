import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = "You are Aegix, an expert AI assistant for penetration testing. Be concise and technical."


class AIEngine:
    def __init__(self, provider: str = "groq", api_key: str = "",
                 ollama_host: str = "127.0.0.1", ollama_port: int = 11434,
                 groq_model: str = "llama-3.3-70b-versatile",
                 ollama_model: str = "llama3"):
        self.provider = provider
        self.api_key = api_key
        self.ollama_host = ollama_host
        self.ollama_port = ollama_port
        self.groq_model = groq_model
        self.ollama_model = ollama_model

    def ask(self, prompt: str) -> str:
        if self.provider == "ollama":
            return self._ask_ollama(prompt)
        return self._ask_groq(prompt)

    def _ask_groq(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("Groq API key is not set. Go to Settings → AI.")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _ask_ollama(self, prompt: str) -> str:
        url = f"http://{self.ollama_host}:{self.ollama_port}/api/chat"
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"]
