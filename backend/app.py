from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.debate_engine import DebateEngine
from services.web_search import WebSearchService
from services.telegram_service import TelegramService

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)
app.config['SECRET_KEY'] = Config.SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="*")

debate_engine = DebateEngine()
search_service = WebSearchService()
telegram_service = TelegramService()

def _maybe_send_telegram(result):
    if Config.AUTO_SEND_TELEGRAM and telegram_service.is_configured():
        telegram_service.send_debate_result(result)

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/status')
def get_status():
    status = debate_engine.get_system_status()
    status["Telegram"] = {
        "name": "Telegram",
        "status": "connected" if telegram_service.is_configured() else "no_api_key",
        "provider": "Telegram Bot API"
    }
    return jsonify({"status": "success", "data": status})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('message', '')
    if not question:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(debate_engine.run_debate(question))
    loop.close()

    _maybe_send_telegram(result)
    return jsonify({"status": "success", "data": result})

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"status": "error", "message": "No query provided"}), 400
    results = search_service.search(query)
    return jsonify({"status": "success", "data": results})

@app.route('/api/agents/<agent_name>/test')
def test_agent(agent_name):
    agent_map = {
        'gemini': debate_engine.gemini,
        'groq': debate_engine.groq,
        'mistral': debate_engine.mistral,
        'openrouter': debate_engine.openrouter
    }
    agent = agent_map.get(agent_name.lower())
    if not agent:
        return jsonify({"status": "error", "message": "Agent not found"}), 404
    connected = agent.check_connection()
    return jsonify({"status": "success" if connected else "error", "data": agent.get_status()})

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to AI Debate Agent'})

@socketio.on('ask_question')
def handle_question(data):
    question = data.get('message', '')

    def status_callback(message):
        socketio.emit('status_update', {'message': message})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(debate_engine.run_debate(question, status_callback))
    loop.close()

    _maybe_send_telegram(result)
    emit('debate_complete', result)

if __name__ == '__main__':
    port = Config.PORT
    socketio.run(app, host='0.0.0.0', port=port, debug=Config.DEBUG)
