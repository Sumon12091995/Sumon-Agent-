const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
    fetchStatus();
});

socket.on('status_update', (data) => {
    const statusMsg = document.getElementById('statusMessage');
    statusMsg.style.display = 'block';
    statusMsg.textContent = data.message;
});

socket.on('debate_complete', (result) => {
    displayDebateResult(result);
    const statusMsg = document.getElementById('statusMessage');
    statusMsg.style.display = 'none';
});

async function fetchStatus() {
    try {
        const res = await fetch('/api/status');
        const json = await res.json();
        if (json.status === 'success') {
            updateStatusUI(json.data);
        }
    } catch (e) {
        console.error('Failed to fetch status', e);
    }
}

function updateStatusUI(statusData) {
    const statusMap = {
        'Gemini': { el: 'geminiStatus', card: 'geminiCard' },
        'Groq': { el: 'groqStatus', card: 'groqCard' },
        'Mistral': { el: 'mistralStatus', card: 'mistralCard' },
        'OpenRouter': { el: 'openrouterStatus', card: 'openrouterCard' },
        'Telegram': { el: 'telegramStatus', card: 'telegramCard' }
    };

    Object.entries(statusData).forEach(([name, info]) => {
        const map = statusMap[name];
        if (map) {
            const badge = document.getElementById(map.el);
            if (badge) {
                const isConn = info.status === 'connected';
                badge.textContent = isConn ? 'Connected' : (info.status === 'no_api_key' ? 'No API Key' : 'Error');
                badge.className = `status-badge status-${isConn ? 'connected' : 'disconnected'}`;
            }
        }
    });
}

function askQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    if (!question) return;

    const statusMsg = document.getElementById('statusMessage');
    statusMsg.style.display = 'block';
    statusMsg.textContent = 'বিতর্ক শুরু হচ্ছে...';

    const resultsArea = document.getElementById('resultsArea');
    resultsArea.classList.remove('active');

    socket.emit('ask_question', { message: question });
}

function displayDebateResult(data) {
    const resultsArea = document.getElementById('resultsArea');
    const agreementBanner = document.getElementById('agreementBanner');
    const consensusText = document.getElementById('consensusText');

    resultsArea.classList.add('active');

    if (typeof data.agreement_reached !== 'undefined') {
        const bannerClass = data.agreement_reached ? 'agreement-box' : 'disagreement-box';
        const bannerText = data.agreement_reached
            ? '✅ সব AI স্বাধীনভাবে একমত হয়েছে (Consensus Reached)'
            : `⚠️ সর্বোচ্চ বিতর্ক-রাউন্ড (${data.max_debate_rounds}) শেষ, সম্পূর্ণ একমত না হলেও Leader সেরা উত্তরটি বেছে নিয়েছে`;
        agreementBanner.innerHTML = `<div class="${bannerClass}">${bannerText}</div>`;
    }

    if (data.consensus && data.consensus.consensus) {
        consensusText.textContent = data.consensus.consensus;
    } else {
        consensusText.textContent = 'কোনো ফলাফল পাওয়া যায়নি।';
    }
}
