import requests
from config import Config
from .prompt_builder import _build_prompt

class GroqAgent:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.model = Config.GROQ_MODEL
        self.base_url = Config.GROQ_BASE_URL
        self.name = "Groq"
        self.status = "disconnected"
        self.last_error = None

    def check_connection(self):
        if not self.api_key:
            self.status = "no_api_key"
            self.last_error = "API key not configured"
            return False

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                self.status = "connected"
                self.last_error = None
                return True
            else:
                self.status = "error"
                self.last_error = f"HTTP {response.status_code}"
                return False
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            return False

    def generate_response(self, prompt, context="", debate_context=None):
        if not self.check_connection():
            return {"error": self.last_error, "response": None}

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            system_msg = "You are a precise, logical AI debate participant. Answer clearly and concisely."
            user_content = _build_prompt(prompt, context, debate_context)
            max_tokens = Config.MAX_TOKENS_DEBATE_RESPONSE if debate_context else Config.MAX_TOKENS_PER_RESPONSE

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                text = data['choices'][0]['message']['content']
                return {"error": None, "response": text, "model": self.model}
            else:
                err = data.get('error', {}).get('message', 'No response generated')
                return {"error": err, "response": None}

        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            return {"error": str(e), "response": None}

    def get_status(self):
        return {
            "name": self.name,
            "model": self.model,
            "status": self.status,
            "last_error": self.last_error,
            "free_tier": "128K context, 30 RPM",
            "provider": "Groq Cloud"
        }
