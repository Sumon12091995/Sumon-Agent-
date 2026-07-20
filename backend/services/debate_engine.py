import asyncio
from agents import GeminiAgent, GroqAgent, MistralAgent, OpenRouterAgent, LeaderAgent
from services.web_search import WebSearchService
from config import Config

class DebateEngine:
    def __init__(self):
        self.gemini = GeminiAgent()
        self.groq = GroqAgent()
        self.mistral = MistralAgent()
        self.openrouter = OpenRouterAgent()
        self.leader = LeaderAgent()
        self.search = WebSearchService()
        self.agents = [self.gemini, self.groq, self.mistral, self.openrouter]

    async def run_debate(self, question, status_callback=None):
        def notify(msg):
            if status_callback:
                try:
                    status_callback(msg)
                except Exception:
                    pass

        notify("রাউন্ড ১: সবাই মিলে ওয়েব থেকে তথ্য সংগ্রহ করছে...")
        connection_status = {}
        for agent in self.agents:
            agent.check_connection()
            connection_status[agent.name] = agent.get_status()

        search_results = self.search.search(question, num_results=5)
        search_context = "\n".join([f"{r['title']}: {r['snippet']}" for r in search_results])

        rounds = []

        notify("রাউন্ড ২: প্রত্যেক AI স্বাধীনভাবে নিজের মতামত দিচ্ছে...")
        opinion_responses = await self._get_all_responses(question, search_context, debate_context=None)
        rounds.append({"round": 2, "type": "opinion", "responses": opinion_responses})

        current_responses = opinion_responses
        agreement_reached = False
        round_num = 3

        while round_num <= Config.MAX_DEBATE_ROUNDS + 2:
            notify(f"রাউন্ড {round_num}: সবাই একে অপরের উত্তর পড়ছে, ভুল খুঁজছে ও প্রশ্ন করছে...")
            debate_context = self._build_cross_context(current_responses)
            debate_responses = await self._get_all_responses(question, search_context, debate_context=debate_context)
            round_entry = {"round": round_num, "type": "debate", "responses": debate_responses}

            if Config.ENABLE_CONSENSUS_CHECK:
                notify(f"রাউন্ড {round_num}: সবাই একমত কিনা যাচাই করছে (Leader)...")
                agreement = self.leader.check_agreement(question, debate_responses)
                round_entry["agreement"] = agreement
                if agreement.get("agreed"):
                    agreement_reached = True

            rounds.append(round_entry)
            current_responses = debate_responses

            if agreement_reached:
                notify(f"✅ রাউন্ড {round_num}-এ সবাই একমত হয়েছে!")
                break

            round_num += 1
        else:
            notify("⚠️ সর্বোচ্চ বিতর্ক-রাউন্ড শেষ, সম্পূর্ণ একমত না হলেও সেরা উত্তর নেওয়া হচ্ছে...")

        notify("Leader: সবার মতামত ও বিতর্ক বিশ্লেষণ করে চূড়ান্ত উত্তর তৈরি করছে...")
        consensus = self.leader.synthesize(question, rounds, search_results)

        return {
            "question": question,
            "connections": connection_status,
            "search_results": search_results,
            "rounds": rounds,
            "consensus": consensus,
            "agreement_reached": agreement_reached,
            "max_debate_rounds": Config.MAX_DEBATE_ROUNDS
        }

    def _build_cross_context(self, responses):
        parts = []
        for r in responses:
            if r.get('response'):
                parts.append(f"### {r['agent']} বলেছে:\n{r['response']}")
            else:
                parts.append(f"### {r['agent']}:\n(এই মডেল উত্তর দিতে ব্যর্থ হয়েছে: {r.get('error', 'unknown error')})")
        return "\n\n".join(parts)

    async def _get_all_responses(self, question, context, debate_context=None):
        tasks = []
        active_agents = []
        for agent in self.agents:
            if agent.status == "connected":
                tasks.append(self._get_single_response(agent, question, context, debate_context))
                active_agents.append(agent)

        if not tasks:
            return []

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        formatted_responses = []
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                formatted_responses.append({"agent": active_agents[i].name, "response": None, "error": str(resp)})
            else:
                formatted_responses.append({
                    "agent": active_agents[i].name,
                    "response": resp.get('response'),
                    "error": resp.get('error'),
                    "model": resp.get('model')
                })
        return formatted_responses

    async def _get_single_response(self, agent, question, context, debate_context):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, agent.generate_response, question, context, debate_context)

    def get_system_status(self):
        status = {}
        for agent in self.agents:
            agent.check_connection()
            status[agent.name] = agent.get_status()
        status["Leader"] = self.leader.get_status()
        return status
