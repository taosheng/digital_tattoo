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

def sync_user_to_db(email, name, provider_id, provider_name):
    """Helper to sync user info to Firestore and return current points."""
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
                f"{provider_name}_id": provider_id,
                "points": points,
                "latest_ID": 99,
                "first_signup": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat()
            })
    return points

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
        
        points = sync_user_to_db(email, name, idinfo['sub'], "google")
                
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

@router.post("/facebook")
async def auth_facebook(req: LoginRequest):
    import httpx
    async with httpx.AsyncClient() as client:
        # Verify token with Facebook Graph API
        resp = await client.get(
            "https://graph.facebook.com/me",
            params={
                "access_token": req.token,
                "fields": "id,name,email"
            }
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Facebook Token")
        
        fb_data = resp.json()
        fb_id = fb_data.get('id')
        email = fb_data.get('email')
        if not email:
            # Fallback if email is not provided
            email = f"{fb_id}@facebook.com"
            
        name = fb_data.get('name', 'Facebook User')
        
        points = sync_user_to_db(email, name, fb_id, "facebook")
        
        return {
            "session_token": email,
            "user": {
                "name": name,
                "email": email,
                "points": points
            }
        }
