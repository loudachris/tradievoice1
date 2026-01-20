import os
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import openai

# --- Configuration ---
# ideally load from env vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
client = openai.Client(api_key=OPENAI_API_KEY)

app = FastAPI(title="TradieVoice Pro API")

# Allow CORS for PWA
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---
# Note: User request placeholder "[Paste the JSON Schema from Section 5 of the Spec]"
# I am implementing a robust default schema based on the domain.
class LineItem(BaseModel):
    description: string
    quantity: float
    unit_price: float
    total: float

class QuoteData(BaseModel):
    customer_name: str
    items: List[LineItem]
    total_amount: float
    notes: str
    upsell_opportunity: bool # Derived field for logic

# --- Endpoints ---

@app.post("/api/transcribe", response_model=QuoteData)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Hybrid Audio Architecture - Walkthrough Mode Endpoint
    1. Receives Audio Blob (MediaRecorder)
    2. Transcribes using Whisper API
    3. Extracts structured JSON using GPT-4o
    """
    if not OPENAI_API_KEY:
         raise HTTPException(status_code=500, detail="OpenAI API Key not configured")

    try:
        # 1. Save temp file for Whisper
        # In a real app, might stream or handle in memory, but saving is safer for basic setup
        temp_filename = f"temp_{file.filename}"
        with open(temp_filename, "wb") as f:
            f.write(await file.read())

        # 2. Transcribe with Whisper
        audio_file = open(temp_filename, "rb")
        transcript_response = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        transcript_text = transcript_response.text
        
        # Clean up temp file
        audio_file.close()
        os.remove(temp_filename)

        # 3. Extract JSON with GPT-4o
        system_prompt = """
        You are an AI assistant for a Tradie App. 
        Extract quote details from the transcription.
        Strictly follow this JSON schema.
        If the total value (sum of items) is greater than $10,000, set 'upsell_opportunity' to true.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcription: {transcript_text}"}
            ],
            response_format={ "type": "json_object" }
        )
        
        # Parse result
        import json
        result_json = json.loads(completion.choices[0].message.content)
        
        return result_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "TradieVoice Pro Backend Online"}
