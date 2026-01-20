import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import openai
from backend.user_service import UserProfile, save_profile, get_profile
from backend.invoice_generator import generate_invoice
import os
import uuid

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
    description: str = "Item"
    quantity: float = 1.0
    unit_price: float = 0.0
    total: float = 0.0

class QuoteData(BaseModel):
    customer_name: str = "Valued Customer"
    items: List[LineItem] = []
    total_amount: float = 0.0
    notes: str = ""
    upsell_opportunity: bool = False

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
        
        Strictly output a SINGLE flattened JSON object matching this schema (do not nest under 'quote_details'):
        {
            "customer_name": "string (infer or use 'Valued Customer')",
            "items": [
                {
                    "description": "string", 
                    "quantity": number, 
                    "unit_price": number (infer if missing), 
                    "total": number (quantity * unit_price)
                }
            ],
            "total_amount": number (sum of item totals),
            "notes": "string (summary of work)",
            "upsell_opportunity": boolean
        }

        Rules:
        1. If price is missing, estimate a reasonable trade price.
        2. Calculate totals accurately.
        3. If the total value > $10,000, set 'upsell_opportunity' to true.
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
        content = completion.choices[0].message.content
        print(f"DEBUG: OpenAI Raw Response: {content}") # Log for debugging 500s
        
        result_json = json.loads(content)
        return result_json

    except Exception as e:
        print(f"ERROR: {str(e)}") # Log stack trace to stdout
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/profile")
def save_user_profile(profile: UserProfile):
    """Saves the user business details."""
    save_profile(profile)
    return {"message": "Profile saved successfully"}

@app.get("/api/profile", response_model=UserProfile)
def get_user_profile():
    """Returns the current user profile."""
    return get_profile()

class InvoiceRequest(BaseModel):
    quote_data: QuoteData

@app.post("/api/generate-invoice")
def create_invoice(request: InvoiceRequest):
    """Generates a PDF invoice based on quote data and stored profile."""
    try:
        profile = get_profile()
        # Create a unique filename
        filename = f"invoice_{uuid.uuid4()}.pdf"
        filepath = os.path.join("backend", filename) # Save in backend dir temporarily
        # For Heroku/DigitalOcean ephemeral FS, we should clean this up or stream it.
        # But for request/response cycle, saving then sending FileResponse is okay.
        
        # Convert QuoteData Pydantic model to dict
        quote_dict = request.quote_data.model_dump()
        
        generate_invoice(filepath, quote_dict, profile)
        
        # Return the file
        return FileResponse(filepath, filename=filename, media_type='application/pdf')
        
    except Exception as e:
         print(f"PDF Error: {str(e)}")
         import traceback
         traceback.print_exc()
         raise HTTPException(status_code=500, detail=f"Failed to generate invoice: {str(e)}")

# Serve Frontend (Place this AFTER API routes so they take precedence)
# html=True allows serving index.html at root "/"
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
