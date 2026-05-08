import os
import io
import time
import httpx
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Security, BackgroundTasks, BackgroundTasks
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
    
    if len(req.string_data) > 1000:
        raise HTTPException(status_code=400, detail="String exceeds 1000 character limit.")
    
    doc_ref = db.collection(u'users').document(email)
    user_data = doc_ref.get().to_dict()
    points = user_data.get('points', 0)
    latest_id = user_data.get("latest_ID", 99)
    if points <= 0:
        raise HTTPException(status_code=403, detail="Insufficient Points")
    
    new_tattoo_id = str(latest_id + 1)
    
    try:
        signatures = tattoo.ar_upload_string(req.string_data, new_tattoo_id, email)
        new_points = points - 1
        doc_ref.update({"points": new_points, "latest_ID": latest_id + 1})
        
        t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
        t_ref.set({
            "tattoo_id": new_tattoo_id,
            "type": "string",
            "blockchain": "arweave",
            "preview": req.string_data[:20] + ("..." if len(req.string_data) > 20 else ""),
            "signatures": signatures,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {"success": True, "new_points": new_points}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_file_upload_worker(
    content: bytes,
    filename: str,
    content_type: str,
    original_size: int,
    email: str,
    new_tattoo_id: str,
    doc_ref
):
    t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
    tmp_path = f"/tmp/tattoo_{new_tattoo_id}"
    try:
        webp_content = None
        webp_filename = None
        is_image = content_type.startswith("image/")
        
        if is_image:
            t_ref.update({"uploading_status": "build webp"})
            print("Processing image: converting to WebP and compressing...")
            img = Image.open(io.BytesIO(content))
            if img.mode != "RGB":
                img = img.convert("RGB")
                print("Converted image to RGB")
                
            WEBP_TARGET_SIZE = 150 * 1024  # 150KB target for WebP
            quality = 90
            print(f"Original image size: {original_size} bytes")
            # Iterate to compress under 150KB
            while True:
                out_io = io.BytesIO()
                img.save(out_io, format="WEBP", quality=quality)
                temp_webp = out_io.getvalue()
                print(f"Compressed image size: {len(temp_webp)} bytes")
                
                if len(temp_webp) <= WEBP_TARGET_SIZE or quality <= 10:
                    webp_content = temp_webp
                    break
                quality -= 10
                
            # If still over target at quality 10, resize the image dimensions
            if len(webp_content) > WEBP_TARGET_SIZE:
                print(f"resizing...")
                while len(webp_content) > WEBP_TARGET_SIZE:
                    width, height = img.size
                    img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
                    out_io = io.BytesIO()
                    img.save(out_io, format="WEBP", quality=10)
                    webp_content = out_io.getvalue()
                    print(f"Resized image size: {len(webp_content)} bytes")
                    
            webp_filename = f"{filename}_.webp"
            
        # The file we actually tattoo on Arweave (use original file, not WebP)
        # Arweave supports up to 6MB per TX, no chunking needed
        tattoo_content = content
        
        with open(tmp_path, "wb") as f:
            f.write(tattoo_content)
            print(f"Saved temporary file to {tmp_path}")

        vaultsage_files = []
        
        vaultsage_path = ""
        if VAULTSAGE_API_KEY:
            print(f"Uploading to Vaultsage...")
            t_ref.update({"uploading_status": "upload to vaultsage"})
            
            vaultsage_path = email.replace('@', '_at_').replace('.', '_')
            target_directory_id = None
            
            try:
                # 1. Fetch directories
                dirs_res = httpx.get(
                    "https://api.vaultsage.ai/api/v1/directories/",
                    headers={"X-Api-Key": VAULTSAGE_API_KEY},
                    timeout=30.0
                )
                if dirs_res.status_code == 200:
                    dirs_data = dirs_res.json().get("data", [])
                    for d in dirs_data:
                        if d.get("directory_name") == vaultsage_path:
                            target_directory_id = d.get("directory_id")
                            break
                            
                # 2. Create if not found
                if not target_directory_id:
                    create_res = httpx.post(
                        "https://api.vaultsage.ai/api/v1/directories/",
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        json={"directory_name": vaultsage_path},
                        timeout=30.0
                    )
                    if create_res.status_code == 200:
                        target_directory_id = create_res.json().get("directory_id")
            except Exception as e:
                print("Failed to get or create VaultSage directory:", e)

            try:
                upload_url = "https://api.vaultsage.ai/api/v1/files/"
                if target_directory_id:
                    upload_url += f"?directory_id={target_directory_id}"
                    
                # Upload original file
                hx1 = httpx.post(
                    upload_url,
                    headers={"X-Api-Key": VAULTSAGE_API_KEY},
                    files=[('files', (filename, content, content_type))],
                    timeout=360.0
                )
                print("VaultSage Original File Backup status:", hx1.status_code)
                vaultsage_files.append(filename)
                
                # Upload webp file individually if it's an image
                if is_image and webp_content:
                    hx2 = httpx.post(
                        upload_url,
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        files=[('files', (webp_filename, webp_content, "image/webp"))],
                        timeout=360.0
                    )
                    print("VaultSage WebP File Backup status:", hx2.status_code)
                    vaultsage_files.append(webp_filename)
                    
            except Exception as ve:
                print("Failed to backup to Vaultsage:", ve)
                
        t_ref.update({"uploading_status": "tattoo to blockchain"})
        signatures = tattoo.ar_upload(tmp_path, new_tattoo_id, email)
        
        t_data_updates = {
            "uploading_status": "done",
            "blockchain": "arweave",
            "filename": filename,
            "original_filename": filename,
            "original_size": original_size,
            "signatures": signatures
        }
        if is_image:
            t_data_updates["webp_filename"] = webp_filename
            t_data_updates["webp_size"] = len(webp_content)
        if VAULTSAGE_API_KEY and vaultsage_path:
            t_data_updates["vaultsage_path"] = vaultsage_path
            t_data_updates["vaultsage_files"] = vaultsage_files
            t_data_updates["vaultsage_original_path"] = f"{vaultsage_path}/{filename}"
            if is_image and webp_filename:
                t_data_updates["vaultsage_webp_path"] = f"{vaultsage_path}/{webp_filename}"
            
        t_ref.update(t_data_updates)
        print(f"File tattoo {new_tattoo_id} background processing completed successfully.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        t_ref.update({"uploading_status": f"error: {str(e)}"})
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/tattoo/file")
async def create_file_tattoo(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    email: str = Depends(verify_token)
):
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
    
    # 1. Check size limit and file type (10MB for Arweave)
    if original_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds the 10MB limit.")
        
    valid_image_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    if file.content_type not in valid_image_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type ({file.content_type}). Only images are allowed.")
    
    # Pre-allocate the record and deduct points
    new_points = points - 1
    doc_ref.update({"points": new_points, "latest_ID": latest_id + 1})
    
    t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
    t_ref.set({
        "tattoo_id": new_tattoo_id,
        "type": "file",
        "blockchain": "arweave",
        "original_filename": file.filename,
        "uploading_status": "starting",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Spawn background task
    background_tasks.add_task(
        process_file_upload_worker,
        content,
        file.filename,
        file.content_type,
        original_size,
        email,
        new_tattoo_id,
        doc_ref
    )
        
    return {"success": True, "new_points": new_points, "tattoo_id": new_tattoo_id}


@app.get("/api/tattoo/read/{tattoo_id}")
def read_tattoo(tattoo_id: str, fallback_solana: bool = False, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    t_ref = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id)
    doc = t_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tattoo not found")
        
    t_data = doc.to_dict()
    t_type = t_data.get("type")
    blockchain = t_data.get("blockchain", "solana")  # default to solana for old records
    
    if t_type == "string":
        signatures = t_data.get("signatures", [])
        if not signatures:
            raise HTTPException(status_code=404, detail="No signatures found for this tattoo.")
        
        try:
            if blockchain == "arweave":
                text = tattoo.ar_download_by_tx_ids(signatures)
                if isinstance(text, bytes):
                    text = text.decode('utf-8')
            else:
                # Legacy Solana tattoos
                text = tattoo.download_by_signatures(signatures)
                if not text:
                    text = tattoo.download(tattoo_id, None, email)
        except Exception as e:
            err_msg = str(e)
            # Arweave TX may not be indexed yet
            if blockchain == "arweave" and ("404" in err_msg or "Not Found" in err_msg or "failed" in err_msg.lower()):
                return {"type": "string", "content": None, "pending": True}
            raise HTTPException(status_code=500, detail=f"Blockchain Retrieval Error: {err_msg}")
            
        if not text:
            if blockchain == "arweave":
                return {"type": "string", "content": None, "pending": True}
            raise HTTPException(status_code=404, detail="Failed to retrieve string tattoo.")
        return {"type": "string", "content": text}
        
    elif t_type == "file":
        filename = t_data.get("filename")
        webp_filename = t_data.get("webp_filename")
        
        vaultsage_success = False
        file_content = None
        download_filename = webp_filename or filename
        
        # Try VaultSage first — try WebP, then fall back to original file
        if VAULTSAGE_API_KEY and not fallback_solana:
            # Attempt 1: try the WebP (reduced size) version
            for try_name in [webp_filename, filename]:
                if not try_name or vaultsage_success:
                    continue
                try:
                    hx = httpx.get(
                        f"https://api.vaultsage.ai/api/v1/files/search?keyword={try_name}",
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        timeout=10.0
                    )
                    if hx.status_code == 200:
                        res_data = hx.json()
                        files_list = res_data.get("files", [])
                        if files_list:
                            file_id = files_list[0]["id"]
                            dl = httpx.post(
                                "https://api.vaultsage.ai/api/v1/files/download",
                                headers={"X-Api-Key": VAULTSAGE_API_KEY},
                                json={"file_ids": [file_id]},
                                timeout=30.0
                            )
                            if dl.status_code == 200:
                                file_content = dl.content
                                vaultsage_success = True
                                download_filename = try_name
                                print(f"VaultSage download success: {try_name}")
                except Exception as e:
                    print(f"VaultSage search/download failed for {try_name}:", e)

        # Fallback to blockchain if VaultSage failed
        if not vaultsage_success:
            if not fallback_solana:
                return JSONResponse(status_code=202, content={"fallback_needed": True})
            
            print(f"Falling back to blockchain ({blockchain}) for tattoo {tattoo_id}")
            signatures = t_data.get("signatures", [])
            try:
                if blockchain == "arweave":
                    file_content_bytes = tattoo.ar_download_by_tx_ids(signatures)
                else:
                    # Legacy Solana tattoos
                    if signatures:
                        file_content_bytes = tattoo.download_by_signatures(signatures)
                    else:
                        file_content_bytes = tattoo.download(tattoo_id, None, email)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Blockchain retrieval error: {str(e)}")
                
            if not file_content_bytes:
                raise HTTPException(status_code=404, detail="Failed to retrieve file tattoo from blockchain")
            file_content = file_content_bytes
            download_filename = webp_filename or filename
            
            # Cache to VaultSage for next time
            if VAULTSAGE_API_KEY and file_content:
                try:
                    vaultsage_path = email.replace('@', '_at_').replace('.', '_')
                    target_directory_id = None
                    dirs_res = httpx.get(
                        "https://api.vaultsage.ai/api/v1/directories/",
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        timeout=30.0
                    )
                    if dirs_res.status_code == 200:
                        for d in dirs_res.json().get("data", []):
                            if d.get("directory_name") == vaultsage_path:
                                target_directory_id = d.get("directory_id")
                                break
                    if not target_directory_id:
                        cr = httpx.post(
                            "https://api.vaultsage.ai/api/v1/directories/",
                            headers={"X-Api-Key": VAULTSAGE_API_KEY},
                            json={"directory_name": vaultsage_path},
                            timeout=30.0
                        )
                        if cr.status_code == 200:
                            target_directory_id = cr.json().get("directory_id")
                    
                    upload_url = "https://api.vaultsage.ai/api/v1/files/"
                    if target_directory_id:
                        upload_url += f"?directory_id={target_directory_id}"
                    
                    cache_res = httpx.post(
                        upload_url,
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        files=[('files', (download_filename, file_content, "application/octet-stream"))],
                        timeout=120.0
                    )
                    print(f"Cached to VaultSage: {download_filename}, status: {cache_res.status_code}")
                except Exception as cache_err:
                    print(f"Failed to cache to VaultSage: {cache_err}")
            
        return StreamingResponse(io.BytesIO(file_content), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{download_filename}"'})


# Mount static frontend for production serving
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def no_frontend():
         return {"message": "Frontend static files not built yet. Access /api endpoint directly or run Vite."}
