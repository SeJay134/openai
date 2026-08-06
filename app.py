# roadofflowers project based on OpenAI
# app.py

from flask import send_from_directory
from uuid import uuid4
from datetime import datetime, timezone
import base64                                   # for generate img
import io
import os                                       # files
import logging
from dotenv import load_dotenv                  # .env
from flask import Flask, request, jsonify
import json
from flask import Flask, request, send_file, jsonify
from PIL import Image                           # for generate img
from openai import OpenAI
from cors_config import ALLOWED_ORIGIN

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

# --------------------- path generated ----------------------------
GENERATED_DIR = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

@app.get("/generated/<path:filename>")
def get_generated(filename):
    logger.info("app.py 'get_generated()' was invoked")
    return send_from_directory(GENERATED_DIR, filename, mimetype="image/jpeg", as_attachment=False)

# ----------------- prompt -----------------
SYSTEM_PROMPT = """
You are a iishka from Irishki, personal assistant.
You answer clearly, concisely.

iishka = иишка = ai = Artificial intelligence (AI)
Irishka = Ирина is name of women

RULES:
1. You must always answer in the same language the user writes in.
- Do not switch languages unless the user switches.
- Do not guess the user's preferred language.
- Detect the language only from the current user message.
2. Follow the user’s instructions carefully. If requirements are unclear or conflict, ask clarifying questions or explain assumptions.
3. Do not fabricate facts. If information is missing or uncertain, clearly state the uncertainty, ask for clarification when needed, or provide a qualified answer based on available information.
4. Provide concise, clear, and practical answers. Adjust the level of detail based on the complexity of the request.
5. Answer directly and avoid unnecessary commentary. Do not add unrelated information. Include additional details only when they are relevant to the user’s request.

When you need to show an image in chat, respond ONLY in JSON:
{
  "reply": "text for user",
  "make_image": true,
  "image_prompt": "prompt for image generation in English or Russian",
  "size": "1536x1024"
}
When no image needed:
{
  "reply": "text for user",
  "make_image": false
}
No extra text outside JSON.
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
    logger.info("app.py 'add_to_memory()' was invoked")
    memory = load_memory()
    memory.append({
        'user': user_message,
        'assistant': assistant_reply
    })
    save_memory(memory)

# ------------- bot → assistant ---------------
def normalize_history(messages):
    logger.info("app.py 'normalize_history()' was invoked")
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
    logger.info("app.py 'add_cors_headers()' was invoked")
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

@app.route("/api/chat", methods=["OPTIONS"])
def chat_options():
    logger.info("app.py 'chat_options()' was invoked")
    return ("", 200)

# ------------- generate img ------------------
def generate_image_to_file(prompt: str, size: str = "1024x1024"):
    allowed_sizes = {"1024x1024", "1536x1024", "1024x1536"}
    if size not in allowed_sizes:
        size = "1536x1024"

    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size=size,
    )
    b64 = result.data[0].b64_json
    img_bytes = base64.b64decode(b64)

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{uuid4().hex}.jpg"

    filepath = os.path.join(GENERATED_DIR, filename)
    img.save(filepath, format="JPEG", quality=97, optimize=True)   # settings

    base_url = request.host_url.rstrip("/")
    url = f"{base_url}/generated/{filename}"
    return url, filename

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
            model="gpt-5.2", # gpt-4o-mini, gpt-4.1, gpt-4o, gpt-5.4-mini-2026-03-17
            messages=messages,
        )
        # reply = response.choices[0].message.content
        # -------------------------------------------
        raw = (response.choices[0].message.content or "").strip()

        # parse JSON from model
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"reply": raw, "make_image": False}

        reply = (payload.get("reply") or "").strip()
        make_image = bool(payload.get("make_image", False))

        image_url = None
        image_filename = None

        if make_image:
            image_prompt = (payload.get("image_prompt") or "").strip()
            size = (payload.get("size") or "1536x1024").strip()

            if image_prompt:
                image_url, image_filename = generate_image_to_file(image_prompt, size)
            else:
                make_image = False
        # -------------------------------------------

        add_to_memory(prompt, reply) # memory saving

        logger.info(f"[BOT] {reply}")
        # ---------------------------
        return jsonify({
            "reply": reply,
            "image_url": image_url,
            "image_filename": image_filename
        })
        # ---------------------------
        # return jsonify({"reply": reply})
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return jsonify({"reply": "Error: OpenAI request failed."}), 200

@app.route("/api/memory", methods=["GET"])
def get_memory():
    logger.info("app.py 'get_memory()' was invoked")
    return jsonify(load_memory())


# ------------------- Generate IMG -----------------------
@app.post("/api/image")
def api_image():
    data = request.get_json(force=True) or {}
    prompt = (data.get("prompt") or "").strip()
    size = (data.get("size") or "1536x1024").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    url, filename = generate_image_to_file(prompt, size)
    return jsonify({"url": url, "filename": filename})


# ----------------- entry -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True) # flask 5004

# python app.py         port=5004

# python -m http.server 6004        index.html port=6004
