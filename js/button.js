const inputField = document.getElementById("input");
const sendBtn = document.getElementById("send_btn");

let isStreaming = false;

// Показывать кнопку, когда есть текст
inputField.addEventListener("input", () => {
    if (inputField.value.trim().length > 0 && !isStreaming) {
        sendBtn.classList.remove("hidden");
        sendBtn.classList.add("send");
        sendBtn.classList.remove("stop");
    } else if (!isStreaming) {
        sendBtn.classList.add("hidden");
    }
});

// push button event to input "Enter" key event
sendBtn.addEventListener("click", () => {
    if (!isStreaming) {
        // send message
        inputField.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
    } else {
        // stop streaming
        if (window.stopStreaming) {
            window.stopStreaming();
        }
    }
});

// functions to change button state from streaming to send and back, called from index.js
window.setButtonToStop = function () {
    isStreaming = true;
    sendBtn.classList.remove("send");
    sendBtn.classList.add("stop");
    sendBtn.classList.remove("hidden");
};

window.setButtonToSend = function () {
    isStreaming = false;
    window.stopStreaming = null;
    sendBtn.classList.remove("stop");
    sendBtn.classList.add("send");

    if (inputField.value.trim().length === 0) {
        sendBtn.classList.add("hidden");
    }
};
