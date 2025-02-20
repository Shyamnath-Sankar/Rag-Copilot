class RAGChatWidget {
    constructor() {
        // Get the script's URL to determine the backend server
        const scripts = document.getElementsByTagName('script');
        const currentScript = scripts[scripts.length - 1];
        const scriptUrl = new URL(currentScript.src);
        const scriptSrc = currentScript.src;
        this.serverUrl = scriptSrc.substring(0, scriptSrc.lastIndexOf('/static')); // Get base URL without /static/widget.js
        
        this.createElements();
        this.setupEventListeners();
    }

    createElements() {
        // Create main container
        const container = document.createElement('div');
        container.innerHTML = `
            <button class="rag-chat-button" id="ragChatButton">
                💬
            </button>

            <div class="rag-chat-container" id="ragChatContainer">
                <div class="rag-chat-header">
                    <span>Document Chat</span>
                    <button class="rag-chat-close" id="ragChatClose">×</button>
                </div>
                <div class="rag-chat-messages" id="ragChatMessages">
                </div>
                <div class="loading" id="ragChatLoading"></div>
                <div class="rag-chat-input-container">
                    <input type="text" class="rag-chat-input" id="ragChatInput" placeholder="Ask a question...">
                    <button class="rag-chat-send" id="ragChatSend">Send</button>
                </div>
            </div>
        `;

        document.body.appendChild(container);

        // Store references to elements
        this.button = document.getElementById('ragChatButton');
        this.container = document.getElementById('ragChatContainer');
        this.closeButton = document.getElementById('ragChatClose');
        this.messages = document.getElementById('ragChatMessages');
        this.input = document.getElementById('ragChatInput');
        this.sendButton = document.getElementById('ragChatSend');
        this.loading = document.getElementById('ragChatLoading');
    }

    setupEventListeners() {
        this.button.addEventListener('click', () => this.toggleChat());
        this.closeButton.addEventListener('click', () => this.toggleChat());
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }

    toggleChat() {
        this.container.style.display = 
            this.container.style.display === 'none' || this.container.style.display === '' 
                ? 'flex' 
                : 'none';
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.input.value = '';

        // Show loading
        this.loading.style.display = 'block';

        try {
            console.log('Sending request to:', this.serverUrl + '/ask'); // Debug log
            const response = await fetch(this.serverUrl + '/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                mode: 'cors',
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Add bot response
            this.addMessage(data.answer, 'bot');
        } catch (error) {
            console.error('Error:', error); // Debug log
            this.addMessage('Sorry, there was an error processing your request: ' + error.message, 'bot');
        } finally {
            this.loading.style.display = 'none';
        }
    }

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = text;
        this.messages.appendChild(messageDiv);
        this.messages.scrollTop = this.messages.scrollHeight;
    }
}

// Initialize widget when script is loaded
window.addEventListener('load', () => {
    new RAGChatWidget();
});