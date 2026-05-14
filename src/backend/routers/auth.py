import os
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from src.backend.dependencies import db

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    token: str

@router.post("/google")
def auth_google(req: LoginRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            req.token, 
            google_requests.Request(), 
            os.environ.get("VITE_GOOGLE_CLIENT_ID")
        )
        email = idinfo['email']
        name = idinfo.get('name', 'User')
        
        # Check Firestore
        points = 5
        if db:
            doc_ref = db.collection(u'users').document(email)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                points = data.get('points', 0)
                doc_ref.update({"last_login": datetime.utcnow().isoformat()})
                if "latest_ID" not in data:
                    doc_ref.update({"latest_ID": 99})
            else:
                doc_ref.set({
                    "email": email,
                    "name": name,
                    "google_id": idinfo['sub'],
                    "points": points,
                    "latest_ID": 99,
                    "first_signup": datetime.utcnow().isoformat(),
                    "last_login": datetime.utcnow().isoformat()
                })
                
        return {
            "session_token": email, # Using email as mock token
            "user": {
                "name": name,
                "email": email,
                "points": points
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Token: {str(e)}")
