import requests
from config import Config

class TelegramService:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID

    def is_configured(self):
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text):
        if not self.is_configured():
            return False

        chunks = [text[i:i + 4000] for i in range(0, len(text), 4000)] or [text]

        try:
            url = f"{Config.TELEGRAM_API_URL}/bot{self.bot_token}/sendMessage"
            for chunk in chunks:
                requests.post(url, json={
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True
                }, timeout=10)
            return True
        except Exception as e:
            print(f"Telegram send failed: {e}")
            return False

    def send_debate_result(self, result):
        question = result.get("question", "")
        consensus = result.get("consensus", {}).get("consensus", "উত্তর পাওয়া যায়নি।")
        rounds_used = len(result.get("rounds", []))
        agreed = result.get("agreement_reached", False)

        status_line = "✅ সব AI একমত হয়েছে" if agreed else f"⚠️ সর্বোচ্চ রাউন্ড ({rounds_used}) শেষে সেরা উত্তর"

        message = (
            f"🤖 AI Debate Agent\n"
            f"প্রশ্ন: {question}\n"
            f"{status_line}\n\n"
            f"{consensus}"
        )
        return self.send_message(message)
