from pydantic import BaseModel
import json
import os

# Define the Profile Model
class UserProfile(BaseModel):
    business_name: str = "My Business"
    abn: str = ""
    gst_registered: bool = False
    logo_base64: str = "" # Storing as base64 for simplicity in MVP
    email: str = ""

# Storage File (Ephemeral in some cloud envs, but good for MVP)
PROFILE_FILE = "user_profile.json"

def save_profile(profile: UserProfile):
    """Saves the user profile to disk."""
    with open(PROFILE_FILE, "w") as f:
        f.write(profile.model_dump_json())

def get_profile() -> UserProfile:
    """Loads the user profile from disk, or returns default."""
    if not os.path.exists(PROFILE_FILE):
        return UserProfile()
    
    try:
        with open(PROFILE_FILE, "r") as f:
            data = json.load(f)
            return UserProfile(**data)
    except Exception:
        return UserProfile()
