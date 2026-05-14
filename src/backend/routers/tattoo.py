import os
import io
import time
import httpx
from datetime import datetime
import string
import random
import base64
from PIL import Image
from pydantic import BaseModel
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from firebase_admin import firestore

# Import tattoo functions
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
import tattoo

from src.backend.dependencies import db, verify_token
from src.backend.utils.crypto import generate_aes_key, encrypt_data, decrypt_data

router = APIRouter(prefix="/api/tattoo", tags=["tattoo"])
VAULTSAGE_API_KEY = os.environ.get("VAULTSAGE_API_KEY")

class StringTattooRequest(BaseModel):
    string_data: str
    encrypt: bool = False

@router.get("/list")
def get_tattoo_list(email: str = Depends(verify_token)):
    tattoos = []
    if db:
        docs = db.collection(u'users').document(email).collection(u'tattoos').order_by(u'timestamp', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            tattoos.append(doc.to_dict())
    return {"tattoos": tattoos}

@router.post("/string")
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
        aes_key_str = None
        upload_data = req.string_data
        if req.encrypt:
            aes_key_str = generate_aes_key()
            aes_key = aes_key_str.encode('utf-8')
            encrypted_bytes = encrypt_data(req.string_data.encode('utf-8'), aes_key)
            upload_data = base64.b64encode(encrypted_bytes).decode('utf-8')

        signatures = tattoo.ar_upload_string(upload_data, new_tattoo_id, email)
        new_points = points - 1
        doc_ref.update({"points": new_points, "latest_ID": latest_id + 1})
        
        t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
        t_ref.set({
            "tattoo_id": new_tattoo_id,
            "type": "string",
            "blockchain": "arweave",
            "preview": req.string_data[:20] + ("..." if len(req.string_data) > 20 else ""),
            "signatures": signatures,
            "timestamp": datetime.utcnow().isoformat(),
            "is_encrypted": req.encrypt,
            "encryption_key": aes_key_str
        })
        return {"success": True, "new_points": new_points, "encryption_key": aes_key_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def process_file_upload_worker(
    content: bytes,
    filename: str,
    content_type: str,
    original_size: int,
    email: str,
    new_tattoo_id: str,
    doc_ref,
    encrypt: bool = False,
    aes_key_str: str = None
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
                
            WEBP_TARGET_SIZE = 99 * 1024  # 99KB target for WebP (ArDrive Turbo Free Tier <100KB)
            quality = 90
            print(f"Original image size: {original_size} bytes")
            # Iterate to compress under 99KB
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
            
        # The file we actually tattoo on Arweave: use WebP (≤99KB) for images, original for others
        tattoo_content = webp_content if is_image else content
        # Use a .webp extension for images so mimetypes.guess_type() works correctly on-chain
        tattoo_tmp_path = f"{tmp_path}.webp" if is_image else tmp_path
        
        if encrypt and aes_key_str:
            aes_key = aes_key_str.encode('utf-8')
            tattoo_content = encrypt_data(tattoo_content, aes_key)
        
        with open(tattoo_tmp_path, "wb") as f:
            f.write(tattoo_content)
            print(f"Saved temporary file to {tattoo_tmp_path}")

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
                    
                vs_content = content
                vs_webp_content = webp_content
                if encrypt and aes_key_str:
                    aes_key = aes_key_str.encode('utf-8')
                    vs_content = encrypt_data(content, aes_key)
                    if is_image and webp_content:
                        vs_webp_content = encrypt_data(webp_content, aes_key)
                    
                # Upload original file
                hx1 = httpx.post(
                    upload_url,
                    headers={"X-Api-Key": VAULTSAGE_API_KEY},
                    files=[('files', (filename, vs_content, content_type))],
                    timeout=360.0
                )
                print("VaultSage Original File Backup status:", hx1.status_code)
                vaultsage_files.append(filename)
                
                # Upload webp file individually if it's an image
                if is_image and webp_content:
                    hx2 = httpx.post(
                        upload_url,
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        files=[('files', (webp_filename, vs_webp_content, "image/webp"))],
                        timeout=360.0
                    )
                    print("VaultSage WebP File Backup status:", hx2.status_code)
                    vaultsage_files.append(webp_filename)
                    
            except Exception as ve:
                print("Failed to backup to Vaultsage:", ve)
                
        t_ref.update({"uploading_status": "tattoo to blockchain"})
        signatures = tattoo.ar_upload(tattoo_tmp_path, new_tattoo_id, email)
        
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
        cleanup_path = locals().get('tattoo_tmp_path', tmp_path)
        if os.path.exists(cleanup_path):
            os.remove(cleanup_path)

@router.post("/file")
async def create_file_tattoo(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    encrypt: str = Form("false"),
    email: str = Depends(verify_token)
):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
        
    is_encrypt = encrypt.lower() == "true"
        
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
    
    aes_key_str = None
    if is_encrypt:
        aes_key_str = generate_aes_key()
    
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
        "timestamp": datetime.utcnow().isoformat(),
        "is_encrypted": is_encrypt,
        "encryption_key": aes_key_str
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
        doc_ref,
        is_encrypt,
        aes_key_str
    )
        
    return {"success": True, "new_points": new_points, "tattoo_id": new_tattoo_id, "encryption_key": aes_key_str}

@router.get("/read/{tattoo_id}")
def read_tattoo(tattoo_id: str, fallback_solana: bool = False, decryption_key: str = None, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    t_ref = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id)
    doc = t_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tattoo not found")
        
    t_data = doc.to_dict()
    t_type = t_data.get("type")
    blockchain = t_data.get("blockchain", "solana")  # default to solana for old records
    is_encrypted = t_data.get("is_encrypted", False)
    stored_key = t_data.get("encryption_key")
    
    if is_encrypted:
        if not decryption_key or decryption_key != stored_key:
            raise HTTPException(status_code=400, detail="Invalid decryption key")
    
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
            
        if is_encrypted:
            try:
                ct_bytes = base64.b64decode(text)
                text = decrypt_data(ct_bytes, stored_key.encode('utf-8')).decode('utf-8')
            except Exception as e:
                raise HTTPException(status_code=500, detail="Decryption failed: " + str(e))
                
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
            
            # Cache to VaultSage for next time (cache the encrypted payload)
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
                    
        # Now we have file_content from either VaultSage or Blockchain, decrypt if needed
        if is_encrypted:
            try:
                file_content = decrypt_data(file_content, stored_key.encode('utf-8'))
            except Exception as e:
                raise HTTPException(status_code=500, detail="Decryption failed: " + str(e))
            
        return StreamingResponse(io.BytesIO(file_content), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{download_filename}"'})
