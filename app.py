# app.py
import os
import logging
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from openai import OpenAI

# ----------------- setup -----------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=API_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ----------------- helpers -----------------
SYSTEM_PROMPT = """
You are a helpful assistant for Sergei's personal portfolio website.
You answer clearly, concisely, and help with code, AI, RAG, and web dev.
If the user speaks Russian, answer in Russian. If English, answer in English.
"""

def detect_language(text: str) -> str:
    cyr = sum('а' <= ch.lower() <= 'я' or ch == 'ё' for ch in text)
    lat = sum('a' <= ch.lower() <= 'z' for ch in text)
    if cyr > lat:
        return "russian"
    if lat > cyr:
        return "english"
    return "unknown"


def normalize_history(messages):
    """
    Frontend sends:
      { role: "user" | "bot", content: ... }

    OpenAI expects:
      "user" | "assistant" | "system" | ...
    """
    normalized = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if role == "bot":
            role = "assistant"

        normalized.append({"role": role, "content": content})

    return normalized


# ----------------- CORS -----------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.route("/api/chat", methods=["OPTIONS"])
def chat_options():
    return ("", 200)


# ----------------- main chat endpoint -----------------
@app.route("/api/chat", methods=["POST"])
def chat():
    logger.info("app.py 'chat' was invoked")

    data = request.get_json(force=True)
    messages_in = data.get("messages", [])
    prompt = data.get("prompt", "")

    logger.info(f"Incoming message: {messages_in}")

    # normalize history for OpenAI
    history = normalize_history(messages_in)

    # language detection on latest user message or prompt
    user_text = prompt or (messages_in[-1]["content"] if messages_in else "")
    lang = detect_language(user_text)
    logger.info(f"Detected language: {lang}")

    # build OpenAI messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if lang == "russian":
        messages.append({"role": "system", "content": "Отвечай строго на русском языке."})
    elif lang == "english":
        messages.append({"role": "system", "content": "Answer strictly in English."})

    messages.extend(history)
    if prompt:
        messages.append({"role": "user", "content": prompt})

    logger.debug(f"Payload to OpenAI: {messages}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        reply = response.choices[0].message.content
        logger.info(f"[BOT] {reply}")
        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return jsonify({"reply": "Error: OpenAI request failed."}), 200


# ----------------- entry -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
