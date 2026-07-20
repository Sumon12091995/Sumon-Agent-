import requests
from config import Config
from .prompt_builder import _build_prompt

class GeminiAgent:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_MODEL
        self.base_url = Config.GEMINI_BASE_URL
        self.name = "Gemini"
        self.status = "disconnected"
        self.last_error = None

    def check_connection(self):
        if not self.api_key:
            self.status = "no_api_key"
            self.last_error = "API key not configured"
            return False

        try:
            url = f"{self.base_url}/models/{self.model}?key={self.api_key}"
            response = requests.get(url, timeout=10)
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
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            full_prompt = _build_prompt(prompt, context, debate_context)
            max_tokens = Config.MAX_TOKENS_DEBATE_RESPONSE if debate_context else Config.MAX_TOKENS_PER_RESPONSE

            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                }
            }

            response = requests.post(url, json=payload, timeout=30)
            data = response.json()

            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
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
            "free_tier": "1M context, 1500 req/day",
            "provider": "Google AI"
        }
