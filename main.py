@app.get("/", response_class=HTMLResponse)
async def home_ui():
    return """
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>gois.v1 | Mobile Workspace</title>
    <style>
        :root {
            --bg-main: #0d1117;
            --bg-sidebar: #161b22;
            --bg-panel: #21262d;
            --border: #30363d;
            --fg: #e6edf3;
            --muted: #8b949e;
            --accent: #238636;
            --accent-hover: #2ea043;
            --user-bubble: #1f6feb;
            --bot-bubble: #161b22;
            --danger: #da3633;
        }
        * { box-sizing: border-box; }
        body {
            background-color: var(--bg-main);
            color: var(--fg);
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            display: flex;
            height: 100vh;
            overflow: hidden;
            position: relative;
        }
        /* Sidebar adaptada para Telemóvel (Gaveta deslizante) */
        #sidebar {
            position: absolute;
            left: -280px;
            top: 0;
            width: 280px;
            height: 100%;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            z-index: 1000;
            transition: left 0.3s ease;
        }
        #sidebar.open {
            left: 0;
            box-shadow: 10px 0 30px rgba(0,0,0,0.5);
        }
        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--border);
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .new-chat-btn {
            background-color: var(--accent);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 14px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .new-chat-btn:hover { background-color: var(--accent-hover); }
        .history-list {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            color: var(--fg);
            background: transparent;
        }
        .history-item:hover { background-color: var(--bg-panel); }
        .history-item.active { background-color: var(--bg-panel); border: 1px solid var(--border); }
        .history-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .delete-chat-btn { background: none; border: none; color: var(--muted); cursor: pointer; padding: 4px; }
        .delete-chat-btn:hover { color: var(--danger); }

        /* Overlay para fechar ao tocar fora no telemóvel */
        #overlay {
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
        }
        #overlay.active { display: block; }

        /* Main Workspace */
        #main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100vh;
            width: 100%;
            position: relative;
        }
        .top-nav {
            padding: 12px 16px;
            background-color: var(--bg-sidebar);
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-weight: 600;
            font-size: 0.95rem;
        }
        .menu-toggle-btn {
            background: none;
            border: none;
            color: var(--fg);
            font-size: 1.2rem;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        }
        .menu-toggle-btn:hover { background-color: var(--bg-panel); }

        #chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            padding-bottom: 120px;
            scroll-behavior: smooth;
        }
        .message-wrapper { max-width: 100%; width: 100%; margin: 0 auto; display: flex; flex-direction: column; gap: 4px; }
        .message { padding: 12px 16px; border-radius: 12px; line-height: 1.5; word-wrap: break-word; white-space: pre-wrap; font-size: 0.9rem; }
        .message.user { background-color: var(--user-bubble); color: white; align-self: flex-end; border-bottom-right-radius: 4px; max-width: 85%; }
        .message.bot { background-color: var(--bot-bubble); border: 1px solid var(--border); color: var(--fg); align-self: flex-start; border-bottom-left-radius: 4px; width: 100%; }
        .sender-label { font-size: 0.75rem; color: var(--muted); margin-bottom: 2px; font-weight: 600; }

        /* Input Area */
        #input-panel {
            position: absolute; bottom: 0; left: 0; width: 100%;
            background: linear-gradient(transparent, var(--bg-main) 30%);
            padding: 12px 16px; display: flex; justify-content: center; box-sizing: border-box;
        }
        .input-box-wrapper {
            width: 100%; background-color: var(--bg-sidebar);
            border: 1px solid var(--border); border-radius: 12px; padding: 8px 12px;
            display: flex; align-items: flex-end; gap: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        }
        textarea { flex: 1; background: transparent; color: var(--fg); border: none; resize: none; height: 24px; max-height: 120px; outline: none; font-family: inherit; font-size: 0.95rem; }
        .send-btn { background-color: var(--accent); color: white; border: none; border-radius: 8px; width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
        .send-btn svg { width: 16px; height: 16px; fill: currentColor; }
    </style>
</head>
<body>
    <div id="overlay" onclick="toggleSidebar()"></div>

    <!-- Sidebar / Histórico Deslizante -->
    <div id="sidebar">
        <div class="sidebar-header">
            <button class="new-chat-btn" onclick="createNewChat()"><span>+</span> Nova Conversa</button>
        </div>
        <div class="history-list" id="historyList"></div>
    </div>

    <!-- Área Principal -->
    <div id="main-content">
        <div class="top-nav">
            <div style="display: flex; align-items: center; gap: 10px;">
                <button class="menu-toggle-btn" onclick="toggleSidebar()">☰</button>
                <span>🟢 gois.v1</span>
            </div>
            <span id="activeChatTitle" style="color: var(--muted); font-size: 0.8rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 150px;">Nova Conversa</span>
        </div>

        <div id="chat-container"></div>

        <div id="input-panel">
            <div class="input-box-wrapper">
                <textarea id="userInput" placeholder="Escreve uma mensagem..." rows="1" oninput="autoResize(this)"></textarea>
                <button class="send-btn" onclick="sendMessage()"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
            </div>
        </div>
    </div>

    <script>
        let chats = JSON.parse(localStorage.getItem('gois_chats') || '[]');
        let currentChatId = localStorage.getItem('gois_current_chat') || null;

        function saveState() {
            localStorage.setItem('gois_chats', JSON.stringify(chats));
            localStorage.setItem('gois_current_chat', currentChatId);
        }

        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        }

        function initApp() {
            if (chats.length === 0) createNewChat();
            else {
                if (!currentChatId || !chats.find(c => c.id === currentChatId)) currentChatId = chats[0].id;
                renderHistory(); loadCurrentChat();
            }
        }

        function createNewChat() {
            const newChat = { id: 'chat_' + Date.now(), title: 'Nova Conversa', messages: [] };
            chats.unshift(newChat); currentChatId = newChat.id;
            saveState(); renderHistory(); loadCurrentChat();
            if(window.innerWidth <= 768) toggleSidebar();
        }

        function deleteChat(id, event) {
            event.stopPropagation();
            chats = chats.filter(c => c.id !== id);
            if (chats.length === 0) createNewChat();
            else if (currentChatId === id) { currentChatId = chats[0].id; loadCurrentChat(); }
            saveState(); renderHistory();
        }

        function switchChat(id) {
            currentChatId = id; saveState(); renderHistory(); loadCurrentChat();
            if(window.innerWidth <= 768) toggleSidebar();
        }

        function renderHistory() {
            const listEl = document.getElementById('historyList'); listEl.innerHTML = '';
            chats.forEach(chat => {
                const item = document.createElement('div');
                item.className = `history-item ${chat.id === currentChatId ? 'active' : ''}`;
                item.onclick = () => switchChat(chat.id);
                item.innerHTML = `<div class="history-title">${chat.title}</div><button class="delete-chat-btn" onclick="deleteChat('${chat.id}', event)">✕</button>`;
                listEl.appendChild(item);
            });
        }

        function loadCurrentChat() {
            const chat = chats.find(c => c.id === currentChatId);
            const container = document.getElementById('chat-container');
            const titleEl = document.getElementById('activeChatTitle');
            container.innerHTML = '';
            if (!chat) return;
            titleEl.textContent = chat.title;
            if (chat.messages.length === 0) {
                appendMessageUI('gois.v1', 'Olá! O teu workspace móvel está pronto.', 'bot');
            } else {
                chat.messages.forEach(m => appendMessageUI(m.role === 'user' ? 'Tu' : 'gois.v1', m.content, m.role === 'user' ? 'user' : 'bot'));
            }
            scrollToBottom();
        }

        function appendMessageUI(sender, text, type) {
            const container = document.getElementById('chat-container');
            const wrapper = document.createElement('div'); wrapper.className = 'message-wrapper';
            const label = document.createElement('div'); label.className = 'sender-label'; label.textContent = sender;
            const msg = document.createElement('div'); msg.className = `message ${type}`; msg.textContent = text;
            wrapper.appendChild(label); wrapper.appendChild(msg); container.appendChild(wrapper);
            scrollToBottom();
            return msg;
        }

        async function sendMessage() {
            const textarea = document.getElementById('userInput');
            const text = textarea.value.trim(); if (!text) return;
            textarea.value = ''; textarea.style.height = '24px';
            const chat = chats.find(c => c.id === currentChatId);
            if (chat.messages.length === 0) { chat.title = text.substring(0, 24); renderHistory(); }
            chat.messages.push({ role: 'user', content: text });
            appendMessageUI('Tu', text, 'user'); saveState();
            const botMsgEl = appendMessageUI('gois.v1', '...', 'bot');
            let fullReply = "";
            try {
                const response = await fetch('/v1/chat/completions', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ messages: chat.messages, stream: true })
                });
                const reader = response.body.getReader(); const decoder = new TextDecoder();
                while (true) {
                    const { done, value } = await reader.read(); if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    for (const line of chunk.split('\\n')) {
                        if (line.startsWith('data:')) {
                            const dataStr = line.slice(5).trim();
                            if (dataStr === '[DONE]') break;
                            try {
                                const parsed = JSON.parse(dataStr);
                                const delta = parsed.choices?.[0]?.delta?.content;
                                if (delta) { fullReply += delta; botMsgEl.textContent = fullReply; scrollToBottom(); }
                            } catch (e) {}
                        }
                    }
                }
                chat.messages.push({ role: 'assistant', content: fullReply }); saveState();
            } catch (err) { botMsgEl.textContent = "Erro: " + err.message; }
        }

        function scrollToBottom() { const c = document.getElementById('chat-container'); c.scrollTop = c.scrollHeight; }
        function autoResize(t) { t.style.height = '24px'; t.style.height = (t.scrollHeight) + 'px'; }
        window.onload = initApp;
    </script>
</body>
</html>
    """
