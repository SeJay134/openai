// index.js

function fixMobileHeight() {
  const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
  document.documentElement.style.setProperty('--app-height', `${h}px`);
}

fixMobileHeight();
window.addEventListener('resize', fixMobileHeight);
window.visualViewport?.addEventListener('resize', fixMobileHeight);

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
        // bubble.textContent = msg.content;

        // text
        if (msg.content) {
        const text = document.createElement("div");
        text.className = "msg-text";
        text.textContent = msg.content;
        bubble.appendChild(text);
        }

        // image
        if (msg.image_url) {
        const img = document.createElement("img");
        img.className = "msg-image";
        img.src = msg.image_url;
        img.alt = "generated image";
        img.loading = "lazy";
        bubble.appendChild(img);

        const a = document.createElement("a");
        a.className = "msg-download";
        a.href = msg.image_url;
        a.download = msg.image_filename || "image.jpg";
        a.textContent = "Download";
        bubble.appendChild(a);
        }

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
    if (event.shiftKey) return;
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
    messages.push({
    role: "assistant",
    content: data.reply || "",
    image_url: data.image_url,              // может быть undefined
    image_filename: data.image_filename     // опционально
    });
    renderChat();

    // const reply = data.reply;

    // messages.push({ role: "assistant", content: reply }); // 'bot' for ollama, 'assistant' for open ai
    // renderChat();
});

