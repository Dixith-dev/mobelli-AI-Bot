const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");
const microphoneBtn = document.getElementById('microphone-btn');

let userMessage = null;
const inputInitHeight = chatInput.scrollHeight;

// Function to get or create a unique user ID
function getUserId() {
    let userId = localStorage.getItem('userId');
    if (!userId) {
        userId = 'user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('userId', userId);
    }
    return userId;
}

function linkify(inputText) {
    return inputText.replace(/(\bhttps?:\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/gim, (match) => {
        return `<a href="${match}" target="_blank">here</a>`;
    });
}

const createChatLi = (message, className) => {
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", className);
    let chatContent = className === "outgoing" ? 
        `<p>${message}</p>` : 
        `<img src="static/images/logo.png" alt="Chatbot Icon" class="chat-icon" style="filter: invert(0);height: 40px;width: 40px;"><p>${linkify(message)}</p>`;
    chatLi.innerHTML = chatContent;
    return chatLi;
};

const generateResponse = (chatElement) => {
    const SERVER_URL = "https://flask-bot-mobelli.onrender.com//get-response";
    const messageElement = chatElement.querySelector("p");
    const userId = getUserId();

    fetch(SERVER_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
            message: userMessage,
            user_id: userId
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log('Original response:', data.response); // Log the original response

        // Use a more generic regular expression to remove citations
        const citationPattern = /\[\d+\+?\w*\]|\(\d+\+?\w*\)/g;
        const cleanResponse = data.response.replace(citationPattern, '');
        console.log('Cleaned response:', cleanResponse); // Log the cleaned response

        messageElement.innerHTML = linkify(cleanResponse);
    })
    .catch((error) => {
        console.error('Error:', error);
        messageElement.classList.add("error");
        messageElement.textContent = "Oops! Something went wrong. Please try again.";
    })
    .finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
}



const handleSend = () => {
    userMessage = chatInput.value.trim();
    if (!userMessage) return;

    const outgoingChatLi = createChatLi(userMessage, "outgoing");
    chatbox.appendChild(outgoingChatLi);
    chatbox.scrollTo(0, chatbox.scrollHeight);
    chatInput.value = "";
    chatInput.style.height = `${inputInitHeight}px`;

    setTimeout(() => {
        const incomingChatLi = createChatLi("Typing...", "incoming");
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
        generateResponse(incomingChatLi);
    }, 600);
};

chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault(); // Prevent the default action to avoid a newline
        handleSend(); // Call the send handler
    }
});

sendChatBtn.addEventListener("click", handleSend);
closeBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));


// Enhanced Speech Recognition setup
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.continuous = false;
recognition.lang = 'en-US';
recognition.interimResults = false;
recognition.maxAlternatives = 1;

let isSpeechDetected = false;
let recognitionTimeout;

function updateMicrophoneIcon(isListening) {
    if (isListening) {
        microphoneBtn.classList.add('listening');
    } else {
        microphoneBtn.classList.remove('listening');
    }
}

recognition.onstart = function() {
    console.log('Voice recognition activated. Start speaking.');
    updateMicrophoneIcon(true);
    clearTimeout(recognitionTimeout);
    isSpeechDetected = false;
};

recognition.onspeechend = function() {
    setTimeout(() => {
        recognition.stop();
        if (!isSpeechDetected) {
            chatbox.appendChild(createChatLi("No speech detected. Please try again.", "incoming"));
        }
    }, 2000 + Math.random() * 2000); // Random delay between 2 to 4 seconds
};

recognition.onresult = function(event) {
    isSpeechDetected = true;
    const transcript = event.results[0][0].transcript;
    chatInput.value = transcript;
    updateMicrophoneIcon(false);
    handleChat();
};

recognition.onerror = function(event) {
    console.error('Speech recognition error detected: ' + event.error);
    updateMicrophoneIcon(false);
    chatbox.appendChild(createChatLi(`Error in speech recognition: ${event.error}`, "incoming"));
};

microphoneBtn.addEventListener('click', function() {
    if (microphoneBtn.classList.contains('listening')) {
        recognition.stop();
    } else {
        recognition.start();
        recognitionTimeout = setTimeout(() => {
            if (!isSpeechDetected) {
                recognition.stop();
                updateMicrophoneIcon(false);
                chatbox.appendChild(createChatLi("No speech detected. Please try again.", "incoming"));
            }
        }, 12000); // Adjusted total time to 12 seconds (10 seconds listening + up to 2 seconds delay)
    }
});
