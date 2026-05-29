const API_BASE_URL = 'http://localhost:5000/api';
const chatWindow = document.getElementById('chatWindow');
const userInput = document.getElementById('userInput');

async function sendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;

    // Agregar mensaje del usuario al chat
    addMessageToChat(message, 'user');
    userInput.value = '';

    // Mostrar indicador de carga
    showLoadingMessage();

    try {
        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });

        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }

        const data = await response.json();
        
        // Remover indicador de carga
        removeLoadingMessage();
        
        // Agregar respuesta del bot
        addMessageToChat(data.response, 'bot');
        
        // Actualizar historial
        updateHistory();

    } catch (error) {
        console.error('Error:', error);
        removeLoadingMessage();
        addMessageToChat('Lo siento, ocurrió un error. Por favor, verifica tu conexión con el servidor.', 'bot');
    }
}

function addMessageToChat(message, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}-message`;
    
    if (sender === 'bot') {
        // Formatear la respuesta del bot con saltos de línea
        const formattedMessage = message
            .split('\n')
            .map(line => line.trim())
            .filter(line => line)
            .join('<br>');
        messageDiv.innerHTML = `<p>${formattedMessage}</p>`;
    } else {
        messageDiv.textContent = message;
    }
    
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showLoadingMessage() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message bot-message';
    loadingDiv.id = 'loading-message';
    loadingDiv.innerHTML = '<p><span class="loading"></span><span class="loading"></span><span class="loading"></span></p>';
    chatWindow.appendChild(loadingDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function removeLoadingMessage() {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

function quickMessage(message) {
    userInput.value = message;
    sendMessage();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function updateHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);
        const data = await response.json();
        
        const historyList = document.getElementById('history');
        
        if (data.history.length > 0) {
            historyList.innerHTML = '';
            data.history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.textContent = `${item.topic} - ${new Date(item.date).toLocaleString()}`;
                historyItem.onclick = () => {
                    userInput.value = `Cuéntame sobre ${item.topic}`;
                    sendMessage();
                };
                historyList.appendChild(historyItem);
            });
        }
    } catch (error) {
        console.error('Error actualizando historial:', error);
    }
}

// Cargar historial al iniciar
window.addEventListener('load', updateHistory);

// Focus en el input al cargar
userInput.focus();
