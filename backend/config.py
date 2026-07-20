import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')

    GEMINI_MODEL = "gemini-2.5-flash"
    GROQ_MODEL = "llama-3.3-70b-versatile"
    MISTRAL_MODEL = "mistral-small-4"
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3.1:free')

    GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    GROQ_BASE_URL = "https://api.groq.com/openai/v1"
    MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    TELEGRAM_API_URL = "https://api.telegram.org"

    GEMINI_RPM = 15
    GROQ_RPM = 30
    MISTRAL_RPM = 30
    OPENROUTER_RPM = 20

    MAX_DEBATE_ROUNDS = 3
    ENABLE_CONSENSUS_CHECK = True

    MAX_TOKENS_PER_RESPONSE = 700
    MAX_TOKENS_DEBATE_RESPONSE = 900
    MAX_TOKENS_CONSENSUS = 1400
    MAX_TOKENS_AGREEMENT_CHECK = 200

    AUTO_SEND_TELEGRAM = True

    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
