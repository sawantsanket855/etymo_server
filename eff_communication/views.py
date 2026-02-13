# Firebase initialization (runs once)
from . import firebase_config

from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from firebase_admin import firestore

from vosk import Model, KaldiRecognizer

import wave
import json
import difflib
import re
import requests
import subprocess
import os
import uuid


# =====================================================
# 🔥 GLOBAL INITIALIZATION (LOAD ONCE ONLY)
# =====================================================

db = firestore.client()

MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "eff_communication",
    "vosk-model-small-en-us-0.15"
)

print("Loading Vosk model...")
VOSK_MODEL = Model(MODEL_PATH)
print("Vosk model loaded successfully!")


# =====================================================
# SAMPLE API
# =====================================================

@api_view(['GET'])
def sample_api(request):
    return Response({
        "status": "success",
        "message": "API from new_app",
    })


# =====================================================
# MAIN API
# =====================================================

@api_view(['POST'])
def update_mistakes_recording_api(request):
    try:
        print('update_mistakes_recording')
        result = update_mistakes_recording(request.data)

        return Response({
            "success": result == "success"
        })

    except Exception as e:
        print("API ERROR:", e)
        return Response(
            {"error": "server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =====================================================
# FIRESTORE UPDATE LOGIC
# =====================================================

def update_mistakes_recording(data):

    userId = data["userId"]
    courseId = data["courseId"]
    dayId = data["dayId"]
    taskId = data["taskId"]

    doc_ref = (
        db.collection("UserData")
        .document(userId)
        .collection("Courses")
        .document(courseId)
        .collection("DayWiseData")
        .document(dayId)
        .collection("Task")
        .document(taskId)
    )

    doc = doc_ref.get()
    if not doc.exists:
        return "error"

    task_data = doc.to_dict()

    documentId = task_data.get("documentId")
    taskType = task_data.get("taskType")
    firebaseRecordingUrl = task_data.get("recording")

    doc_ref = db.collection(taskType).document(documentId)

    doc = doc_ref.get()
    if not doc.exists:
        return "error"

    actual_content = doc.to_dict().get("content")

    result = getMistakes(firebaseRecordingUrl, actual_content)
    if not result:
        return "error"

    # Update Firestore
    (
        db.collection("UserData")
        .document(userId)
        .collection("Courses")
        .document(courseId)
        .collection("DayWiseData")
        .document(dayId)
        .collection("Task")
        .document(taskId)
    ).update({
        "mistakes": result[0],
        "errorCount": result[1],
        "accuracy": result[2],
        "isMistakesAvailable": True,
        "spokenText": result[3]
    })

    return "success"


# =====================================================
# SPEECH TO TEXT
# =====================================================

def getSpokenTextFromFirebaseUrl(firebase_url):

    uid = str(uuid.uuid4())
    M4A_FILE = f"{uid}.m4a"
    WAV_FILE = f"{uid}.wav"

    try:
        # DOWNLOAD AUDIO
        response = requests.get(firebase_url, stream=True)
        response.raise_for_status()

        with open(M4A_FILE, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # CONVERT TO WAV
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", M4A_FILE,
            "-ac", "1",
            "-ar", "16000",
            "-sample_fmt", "s16",
            WAV_FILE
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        wf = wave.open(WAV_FILE, "rb")

        rec = KaldiRecognizer(VOSK_MODEL, wf.getframerate())
        rec.SetWords(False)

        result_text = []

        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result_text.append(json.loads(rec.Result()).get("text", ""))

        result_text.append(json.loads(rec.FinalResult()).get("text", ""))
        wf.close()
        return " ".join(result_text)

    finally:
        # CLEAN TEMP FILES
        if os.path.exists(M4A_FILE):
            os.remove(M4A_FILE)
        if os.path.exists(WAV_FILE):
            os.remove(WAV_FILE)


# =====================================================
# TOKENIZER
# =====================================================

def tokenize_with_index(text):
    tokens = []
    for m in re.finditer(r"\b\w+\b", text.lower()):
        tokens.append({
            "word": m.group(),
            "start": m.start(),
            "end": m.end()
        })
    return tokens


# =====================================================
# MISTAKE DETECTION
# =====================================================

def getMistakes(firebase_url, original_text):

    final_text = getSpokenTextFromFirebaseUrl(firebase_url)

    orig_tokens = tokenize_with_index(original_text)
    spok_tokens = tokenize_with_index(final_text)

    orig_words = [t["word"] for t in orig_tokens]
    spok_words = [t["word"] for t in spok_tokens]

    matcher = difflib.SequenceMatcher(None, orig_words, spok_words)

    mistakes = []
    insertedCount = 0
    missingCount = 0
    replacedCount = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "delete":
            for idx in range(i1, i2):
                t = orig_tokens[idx]
                mistakes.append({
                    "tag": "delete",
                    "expected": {"start": t["start"], "end": t["end"]},
                })
                missingCount += 1

        elif tag == "insert":
            for idx in range(j1, j2):
                t = spok_tokens[idx]
                mistakes.append({
                    "tag": "insert",
                    "spoken": {"start": t["start"], "end": t["end"]},
                    "position": orig_tokens[i1]["start"]
                })
                insertedCount += 1

        elif tag == "replace":
            mistakes.append({
                "tag": "replace",
                "expected": {
                    "start": orig_tokens[i1]["start"],
                    "end": orig_tokens[i2-1]["end"]
                },
                "spoken": {
                    "start": spok_tokens[j1]["start"],
                    "end": spok_tokens[j2-1]["end"]
                },
            })
            replacedCount += (i2 - i1)

    total_mistake_count = replacedCount + insertedCount + missingCount
    accuracy = int(100 - (total_mistake_count / len(orig_tokens) * 100))
    print(mistakes,accuracy,final_text)
    return (
        mistakes,
        {
            "replacedCount": replacedCount,
            "insertedCount": insertedCount,
            "missingCount": missingCount
        },
        accuracy,
        final_text
    )
