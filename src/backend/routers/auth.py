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

class LineLoginRequest(BaseModel):
    code: str
    redirect_uri: str

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

@router.post("/line")
async def auth_line(req: LineLoginRequest):
    import httpx
    import jwt
    
    client_id = os.environ.get("VITE_LINE_CLIENT_ID")
    client_secret = os.environ.get("LINE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="LINE credentials not configured on server")
        
    async with httpx.AsyncClient() as client:
        # 1. Exchange auth code for access token and id_token
        token_resp = await client.post(
            "https://api.line.me/oauth2/v2.1/token",
            data={
                "grant_type": "authorization_code",
                "code": req.code,
                "redirect_uri": req.redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to get LINE token: {token_resp.text}")
            
        token_data = token_resp.json()
        id_token_str = token_data.get("id_token")
        
        if not id_token_str:
            raise HTTPException(status_code=400, detail="No id_token received from LINE")
            
        # 2. Decode the JWT id_token to get user profile and email (if available)
        try:
            # We skip signature verification here since we just received it over HTTPS directly from LINE
            decoded = jwt.decode(id_token_str, options={"verify_signature": False})
        except jwt.DecodeError:
            raise HTTPException(status_code=400, detail="Invalid id_token from LINE")
            
        line_id = decoded.get("sub")
        name = decoded.get("name", "LINE User")
        email = decoded.get("email")
        
        # 3. Handle users without an email
        if not email:
            # Create a deterministic mock email based on their LINE ID
            email = f"{line_id}@line.user"
            
        points = sync_user_to_db(email, name, line_id, "line")
        
        return {
            "session_token": email,
            "user": {
                "name": name,
                "email": email,
                "points": points
            }
        }

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
