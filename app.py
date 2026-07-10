# app.py
import os                                       # files
import logging
from dotenv import load_dotenv                  # .env
from flask import Flask, request, jsonify
import json
from openai import OpenAI

# ----------------- logging -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
# ----------------- setup -----------------
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables")

client = OpenAI(api_key=API_KEY)
logger = logging.getLogger(__name__)
app = Flask(__name__) # HTTP

# ----------------- prompt -----------------
SYSTEM_PROMPT = """
You are a iishka from Irishki, personal assistant.
You answer clearly, concisely, and help with code, AI, RAG, and web dev.

iishka = иишка = ai = Artificial intelligence (AI)
Irishka = Ирина is name of women

RULES:
1. You must always answer in the same language the user writes in.
- Do not switch languages unless the user switches.
- Do not guess the user's preferred language.
- Detect the language only from the current user message.
2. Follow the user’s instructions exactly.
3. Do not invent facts. If you don’t know something, say: “I do not have information about it.”
4. Keep answers short, clear, and deterministic.
5. Output only the answer. No extra comments.
 - after answer do not provide extra information about something specific or not fully provided.
"""

# ------------- memory ---------------
MEMORY_FILE = 'memory.json'

def load_memory():
    logging.info('app.py load_memory() was invoked')
    if not os.path.exists(MEMORY_FILE):
        return [] # empty
    try:
        with open(MEMORY_FILE, 'r', encoding='UTF-8') as f: # read data
            return json.load(f)         # {user, assistant}
    except Exception:
        logger.exception("Couldn't load memory")
        return [] # empty
    
def save_memory(memory):
    logging.info('app.py save_memory() was invoked')
    with open(MEMORY_FILE, 'w', encoding='UTF-8') as f: # write data
        json.dump(memory, f, ensure_ascii=False, indent=2) # memory to json file

def add_to_memory(user_message, assistant_reply): # what user said + current memory
    memory = load_memory()
    memory.append({
        'user': user_message,
        'assistant': assistant_reply
    })
    save_memory(memory)

# ------------- bot → assistant ---------------
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


# ----------------- CORS for ngrok front -----------------
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
    logger.info("app.py 'chat()' was invoked")

    data = request.get_json(force=True) # read json
    messages_in = data.get("messages", []) # data of chat from frontend
    prompt = data.get("prompt", "") # current user message

    logger.info(f"Incoming message: {messages_in}")

    history = normalize_history(messages_in) # use normalize

    # load memory
    memory = load_memory() # load memory from memory.json
    memory_text = '\n'.join(
        [f"user: {m['user']}\nassistant: {m['assistant']}" for m in memory]
    )

    # build OpenAI messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f'Conversation memory:\n{memory_text}'}
    ]

    messages.extend(history) # add history
    messages.append({"role": "user", "content": prompt})

    logger.debug(f"Payload to OpenAI: {messages}")

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # gpt-4o-mini, gpt-4.1
            messages=messages,
        )
        reply = response.choices[0].message.content

        add_to_memory(prompt, reply) # memory saving

        logger.info(f"[BOT] {reply}")

        return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return jsonify({"reply": "Error: OpenAI request failed."}), 200

@app.route("/api/memory", methods=["GET"])
def get_memory():
    return jsonify(load_memory())

# ----------------- entry -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
