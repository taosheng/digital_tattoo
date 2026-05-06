import os
import io
import time
import httpx
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Security
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv
from PIL import Image

# For importing tattoo functions cleanly, regardless of run directory
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
import tattoo

load_dotenv()

# Initialize Firebase via Service Account (saltycat.json)
cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "saltycat.json")
try:
    cred = credentials.Certificate(cred_path)
    initialize_app(cred)
    from google.cloud import firestore as gc_firestore
    # Explicitly connect to the 'tattoo' database instead of '(default)'
    db = gc_firestore.Client(database="tattoo", project=cred.project_id)
except Exception as e:
    print(f"Warning: Failed to initialize Firestore from {cred_path}. Emulating db. {e}")
    db = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

VAULTSAGE_API_KEY = os.environ.get("VAULTSAGE_API_KEY")

class LoginRequest(BaseModel):
    token: str

class StringTattooRequest(BaseModel):
    string_data: str

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    # Simple check for our JWT which we are returning directly. In production, sign cookies.
    # For simplicity, our frontend uses the user email as the sessionToken mock if we bypass complex signing.
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token

@app.post("/api/auth/google")
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

@app.get("/api/tattoo/list")
def get_tattoo_list(email: str = Depends(verify_token)):
    tattoos = []
    if db:
        docs = db.collection(u'users').document(email).collection(u'tattoos').order_by(u'timestamp', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            tattoos.append(doc.to_dict())
    return {"tattoos": tattoos}

@app.post("/api/tattoo/string")
def create_string_tattoo(req: StringTattooRequest, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    doc_ref = db.collection(u'users').document(email)
    user_data = doc_ref.get().to_dict()
    points = user_data.get('points', 0)
    latest_id = user_data.get("latest_ID", 99)
    if points <= 0:
        raise HTTPException(status_code=403, detail="Insufficient Points")
    
    new_tattoo_id = str(latest_id + 1)
    
    try:
        signatures = tattoo.upload_string(req.string_data, new_tattoo_id, email)
        new_points = points - 1
        doc_ref.update({"points": new_points, "latest_ID": latest_id + 1})
        
        t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
        t_ref.set({
            "tattoo_id": new_tattoo_id,
            "type": "string",
            "preview": req.string_data[:20] + ("..." if len(req.string_data) > 20 else ""),
            "signatures": signatures,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"success": True, "new_points": new_points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tattoo/file")
async def create_file_tattoo(file: UploadFile = File(...), email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
        
    doc_ref = db.collection(u'users').document(email)
    user_data = doc_ref.get().to_dict()
    points = user_data.get('points', 0)
    latest_id = user_data.get("latest_ID", 99)
    if points <= 0:
        raise HTTPException(status_code=403, detail="Insufficient Points")
        
    new_tattoo_id = str(latest_id + 1)
        
    content = await file.read()
    original_size = len(content)
    
    # 1. Check size limit
    if original_size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 2MB limit.")
    
    webp_content = None
    webp_filename = None
    is_image = file.content_type.startswith("image/")
    
    if is_image:
        print("Processing image: converting to WebP and compressing...")
        img = Image.open(io.BytesIO(content))
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        quality = 90
        # Iterate to compress under 64KB
        while True:
            out_io = io.BytesIO()
            img.save(out_io, format="WEBP", quality=quality)
            temp_webp = out_io.getvalue()
            
            if len(temp_webp) <= 65536 or quality <= 10:
                webp_content = temp_webp
                break
            quality -= 10
            
        # If still over 64KB at quality 10, resize the image dimensions
        if len(webp_content) > 65536:
            while len(webp_content) > 65536:
                width, height = img.size
                img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
                out_io = io.BytesIO()
                img.save(out_io, format="WEBP", quality=10)
                webp_content = out_io.getvalue()
                
        webp_filename = f"{new_tattoo_id}_compressed.webp"
        
    # The file we actually tattoo on Solana
    tattoo_content = webp_content if is_image else content
    
    # Write to temp file for the native utility processing
    tmp_path = f"/tmp/tattoo_{new_tattoo_id}"
    with open(tmp_path, "wb") as f:
        f.write(tattoo_content)
        
    try:
        tattoo.upload(tmp_path, new_tattoo_id, email)
        
        vaultsage_files = []
        original_unique_filename = f"{new_tattoo_id}_{file.filename}"
        
        # Attempt Vaultsage Backup
        if VAULTSAGE_API_KEY:
            files_map = []
            files_map.append(('files', (original_unique_filename, content, file.content_type)))
            vaultsage_files.append(original_unique_filename)
            
            if is_image and webp_content:
                files_map.append(('files', (webp_filename, webp_content, "image/webp")))
                vaultsage_files.append(webp_filename)
                
            try:
                hx = httpx.post(
                    "https://api.vaultsage.ai/api/v1/files/",
                    headers={"X-Api-Key": VAULTSAGE_API_KEY},
                    files=files_map,
                    timeout=30.0
                )
                print("VaultSage Backup status:", hx.status_code)
            except Exception as ve:
                print("Failed to backup to Vaultsage:", ve)
                
        new_points = points - 1
        doc_ref.update({"points": new_points, "latest_ID": latest_id + 1})
        
        t_data = {
            "tattoo_id": new_tattoo_id,
            "type": "file",
            "filename": original_unique_filename if VAULTSAGE_API_KEY else file.filename,
            "original_filename": file.filename,
            "original_size": original_size,
            "timestamp": datetime.utcnow().isoformat()
        }
        if is_image:
            t_data["webp_filename"] = webp_filename
            t_data["webp_size"] = len(webp_content)
        if VAULTSAGE_API_KEY:
            t_data["vaultsage_files"] = vaultsage_files
            
        t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
        t_ref.set(t_data)
        
        return {"success": True, "new_points": new_points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/api/tattoo/read/{tattoo_id}")
def read_tattoo(tattoo_id: str, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    t_ref = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id)
    doc = t_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tattoo not found")
        
    t_data = doc.to_dict()
    t_type = t_data.get("type")
    
    if t_type == "string":
        # Check if we have signatures stored for quick retrieval
        signatures = t_data.get("signatures", [])
        if signatures:
            try:
                text = tattoo.download_by_signatures(signatures)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Solana Retrieval Error: {str(e)}")
        else:
            # Fallback to the old method (scanning the blockchain)
            text = tattoo.download(tattoo_id, None, email)
            
        if not text:
            raise HTTPException(status_code=404, detail="Failed to retrieve string tattoo from Solana")
        return {"type": "string", "content": text}
        
    elif t_type == "file":
        # File path from vaultsage
        filename = t_data.get("filename")
        if not VAULTSAGE_API_KEY:
            raise HTTPException(status_code=501, detail="File tattoos require Vaultsage API Key to be configured on the server to download.")
            
        # Search Vaultsage for the file
        try:
            hx = httpx.get(
                f"https://api.vaultsage.ai/api/v1/files/search?keyword={filename}",
                headers={"X-Api-Key": VAULTSAGE_API_KEY},
                timeout=10.0
            )
            if hx.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to search Vaultsage")
            res_data = hx.json()
            items = res_data.get("items", [])
            if not items:
                raise HTTPException(status_code=404, detail="File could not be found in Vaultsage backups.")
            file_id = items[0]["file_id"]
            
            # Request download URL or binary
            dl = httpx.post(
                "https://api.vaultsage.ai/api/v1/files/download",
                headers={"X-Api-Key": VAULTSAGE_API_KEY},
                json={"file_ids": [file_id]},
                timeout=30.0
            )
            if dl.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch file from Vaultsage")
                
            file_content = dl.content
            final_filename = filename.split('_', 1)[-1] if '_' in filename else filename
            return StreamingResponse(io.BytesIO(file_content), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{final_filename}"'})
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


# Mount static frontend for production serving
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def no_frontend():
         return {"message": "Frontend static files not built yet. Access /api endpoint directly or run Vite."}
