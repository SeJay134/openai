// index.js

function fixMobileHeight() {
    const vh = (window.visualViewport?.height || window.innerHeight) * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
}

fixMobileHeight();
window.visualViewport?.addEventListener('resize', fixMobileHeight);
window.addEventListener('orientationchange', fixMobileHeight);

// const API_URL;

let messages = [];
console.log("Chat initialized");
console.log("API URL:", API_URL);
console.log('messages:', messages);
function renderChat() {
    const chat = document.getElementById("chat");
    chat.innerHTML = "";

    messages.forEach(msg => {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper " + msg.role;

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = msg.content;

        wrapper.appendChild(bubble);
        chat.appendChild(wrapper);
    });

    const container = document.getElementById("chat_container");

    requestAnimationFrame(() => {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: "smooth"
        });
    });
}

const input = document.getElementById("input");

input.addEventListener("input", () => {
    if (input.value.trim() === "") {
        input.style.height = "45px";
        return;
    }
    input.style.height = "45px";
    input.style.height = input.scrollHeight + "px";
});

input.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();

    const prompt = input.value.trim();
    if (!prompt) return;

    messages.push({ role: "user", content: prompt });
    renderChat();
    input.value = "";
    input.style.height = "";

    const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages, prompt })
    });

    const data = await response.json();
    const reply = data.reply;

    messages.push({ role: "assistant", content: reply }); // 'bot' for ollama, 'assistant' for open ai
    renderChat();
});

