import requests
from config import Config

class LeaderAgent:
    def __init__(self):
        self.groq_api_key = Config.GROQ_API_KEY
        self.groq_model = Config.GROQ_MODEL
        self.base_url = Config.GROQ_BASE_URL
        self.name = "Leader"
        self.status = "ready"

    def check_agreement(self, question, responses):
        valid = [r for r in responses if r.get('response')]
        if len(valid) <= 1:
            return {"agreed": True, "reason": "একটির বেশি বৈধ উত্তর নেই, তুলনা করার কিছু নেই।"}

        answers_text = "\n\n".join([f"[{r['agent']}]: {r['response']}" for r in valid])
        check_prompt = f"""নিচের প্রশ্নের জন্য কয়েকটি AI মডেলের সর্বশেষ উত্তর দেওয়া আছে।
বলো তারা মূল সিদ্ধান্তে (core answer/conclusion) একমত কিনা - ছোটখাটো ভাষাগত পার্থক্য উপেক্ষা করো, শুধু মূল তথ্য/সিদ্ধান্তে বাস্তব দ্বিমত আছে কিনা দেখো।

প্রশ্ন: {question}

উত্তরসমূহ:
{answers_text}

শুধু এই ফরম্যাটে উত্তর দাও, আর কিছু লিখো না:
AGREED: YES অথবা NO
REASON: (এক লাইনে কারণ)"""

        if not self.groq_api_key:
            return {"agreed": True, "reason": "Groq API কনফিগার নেই, agreement-check বাদ দেওয়া হলো।"}

        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.groq_model,
                "messages": [
                    {"role": "system", "content": "You strictly output only AGREED: and REASON: lines."},
                    {"role": "user", "content": check_prompt}
                ],
                "max_tokens": Config.MAX_TOKENS_AGREEMENT_CHECK,
                "temperature": 0.0
            }
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=20)
            data = response.json()
            text = data['choices'][0]['message']['content']
            agreed = 'AGREED: YES' in text.upper() or 'AGREED:YES' in text.upper()
            reason_line = ""
            for line in text.splitlines():
                if line.strip().upper().startswith('REASON'):
                    reason_line = line.split(':', 1)[-1].strip()
            return {"agreed": agreed, "reason": reason_line or text.strip()}
        except Exception as e:
            return {"agreed": True, "reason": f"Agreement-check ব্যর্থ হয়েছে ({e}), তাই এগিয়ে যাওয়া হলো।"}

    def synthesize(self, question, rounds, search_results):
        rounds_text = self._format_rounds(rounds)
        search_text = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results]) or "কোনো সার্চ ফলাফল পাওয়া যায়নি।"

        synthesis_prompt = f"""তুমি একজন নিরপেক্ষ Leader/সমন্বয়কারী AI। নিচে একটি প্রশ্ন নিয়ে একাধিক AI মডেলের মধ্যে হওয়া সম্পূর্ণ বিতর্কের বিবরণ দেওয়া আছে।

মূল প্রশ্ন: {question}

ওয়েব সার্চ থেকে পাওয়া তথ্য:
{search_text}

সম্পূর্ণ বিতর্কের বিবরণ (রাউন্ড অনুযায়ী):
{rounds_text}

তোমার কাজ:
১) কোন কোন পয়েন্টে সব মডেল একমত হয়েছে তা চিহ্নিত করো।
২) কোথায় দ্বিমত ছিল এবং কীভাবে (বা কেন) সেটা সমাধান হলো তা ব্যাখ্যা করো।
৩) সবকিছু বিবেচনা করে একটি সুস্পষ্ট, সঠিক ও চূড়ান্ত উত্তর দাও।

উত্তর অবশ্যই নিচের ফরম্যাটে দাও:

CONSENSUS: (চূড়ান্ত উত্তর, স্পষ্ট ভাষায়)

AGREEMENT: (যে বিষয়ে সব মডেল একমত হয়েছে)

DISAGREEMENT: (যে বিষয়ে দ্বিমত ছিল এবং কীভাবে সমাধান করা হলো)

CONFIDENCE: (High/Medium/Low এবং কেন)"""

        if self.groq_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": "You are an expert, neutral fact-checker and debate moderator who writes the final consensus answer in Bengali."},
                        {"role": "user", "content": synthesis_prompt}
                    ],
                    "max_tokens": Config.MAX_TOKENS_CONSENSUS,
                    "temperature": 0.3
                }
                response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=30)
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    consensus = data['choices'][0]['message']['content']
                    return {"error": None, "consensus": consensus, "model": self.groq_model, "rounds_used": len(rounds)}
            except Exception:
                pass

        return self._fallback_consensus(question, rounds)

    def _format_rounds(self, rounds):
        lines = []
        for r in rounds:
            label = f"প্রাথমিক মতামত (Round {r['round']})" if r["type"] == "opinion" else f"ক্রস-পরীক্ষা / বিতর্ক (Round {r['round']})"
            lines.append(f"--- {label} ---")
            for resp in r["responses"]:
                if resp.get("response"):
                    lines.append(f"[{resp['agent']}]: {resp['response']}")
                else:
                    lines.append(f"[{resp['agent']}]: (এরর: {resp.get('error', 'unknown')})")
            if "agreement" in r:
                lines.append(f"(Agreement check: {'YES' if r['agreement']['agreed'] else 'NO'} - {r['agreement']['reason']})")
            lines.append("")
        return "\n".join(lines)

    def _fallback_consensus(self, question, rounds):
        last_round = rounds[-1] if rounds else {"responses": []}
        valid_responses = [r for r in last_round.get("responses", []) if r.get('response')]
        if not valid_responses:
            return {"error": "No valid responses", "consensus": "Unable to reach consensus.", "model": "Fallback", "rounds_used": 0}
        best_response = max(valid_responses, key=lambda x: len(x.get('response', '')))
        consensus_text = f"""CONSENSUS: {best_response.get('response', 'No consensus')}

AGREEMENT: N/A

DISAGREEMENT: N/A

CONFIDENCE: Medium (Fallback mode)"""
        return {"error": None, "consensus": consensus_text, "model": "Fallback Consensus", "rounds_used": len(rounds)}

    def get_status(self):
        return {
            "name": self.name,
            "model": self.groq_model,
            "status": self.status,
            "last_error": None,
            "free_tier": "Uses other agents' free tiers",
            "provider": "Internal Consensus Engine"
        }
