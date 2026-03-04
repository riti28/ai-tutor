from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import google.generativeai as genai
from gtts import gTTS
import os
import re
import time

# =============================
# GEMINI API KEY
# =============================

genai.configure(api_key="AIzaSyC0hrITcIyeA7JOlpVqHsWE9hMTmnd115I")

# =============================
# FASTAPI SETUP
# =============================

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="."), name="static")

# =============================
# REQUEST MODEL
# =============================

class StudentQuestion(BaseModel):
    grade: str
    subject: str
    textbook: str
    language: str
    question: str

# =============================
# LOAD TEXTBOOK
# =============================

def load_textbook(grade, subject, textbook):

    path = f"textbooks/{grade}/{subject}/{textbook}.txt"

    if os.path.exists(path):

        with open(path, "r", encoding="utf-8") as f:
            return f.read(), True

    return "", False

# =============================
# CLEAN TEXT
# =============================

def clean_text(text):

    text = re.sub(r"\*+", "", text)
    text = re.sub(r"#", "", text)
    text = re.sub(r"\n+", " ", text)

    return text.strip()

# =============================
# AI ANSWER
# =============================

def get_ai_answer(question, grade, subject, language, textbook):

    content, found = load_textbook(grade, subject, textbook)

    model = genai.GenerativeModel("gemini-flash-lite-latest")

    try:

        # TEXTBOOK EXISTS
        if found:

            prompt = f"""
You are a helpful school teacher.

A student from {grade} asked a question in {subject}.

Use the textbook content if it contains the answer.
If the textbook does NOT contain the answer, explain using your own knowledge.

Textbook content:
{content}

Student question:
{question}

Explain clearly for a {grade} student.
Answer in {language}.
"""

            response = model.generate_content(prompt)

            message = "📘 Answer generated using the selected textbook when possible."

            return clean_text(response.text), message


        # TEXTBOOK NOT FOUND
        else:

            prompt = f"""
You are a friendly teacher.

Explain the following question clearly for a {grade} student.

Question:
{question}

Answer in {language}.
Explain in simple words.
"""

            response = model.generate_content(prompt)

            message = "⚠️ The selected textbook is not available in the system yet. The answer below is generated using the AI tutor's general knowledge."

            return clean_text(response.text), message


    except Exception:

        return "⏳ The AI tutor is currently busy due to usage limits. Please wait a moment and try again.", ""

# =============================
# TEXT TO SPEECH
# =============================

def make_voice(text, language):

    lang_map = {
        "English": "en",
        "Hindi": "hi",
        "Kannada": "kn",
        "Tamil": "ta",
        "Telugu": "te"
    }

    lang_code = lang_map.get(language, "en")

    filename = "answer.mp3"

    tts = gTTS(text=text, lang=lang_code)

    tts.save(filename)

    return filename

# =============================
# RATE LIMIT CONTROL
# =============================

last_request_time = 0

# =============================
# MAIN ENDPOINT
# =============================

@app.post("/ask")

def ask_question(data: StudentQuestion):

    global last_request_time

    current_time = time.time()

    if current_time - last_request_time < 2:

        return {
            "text": "Please wait a few seconds before asking another question.",
            "message": "",
            "audio_file": ""
        }

    last_request_time = current_time

    answer, message = get_ai_answer(
        data.question,
        data.grade,
        data.subject,
        data.language,
        data.textbook
    )

    audio_file = make_voice(answer, data.language)

    return {
        "text": answer,
        "message": message,
        "audio_file": "http://127.0.0.1:8000/static/" + audio_file
    }

# =============================
# TEST ROUTE
# =============================

@app.get("/")

def home():

    return {"message": "AI Tutor server running successfully"}