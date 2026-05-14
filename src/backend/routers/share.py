import os
import io
import httpx
from datetime import datetime
import string
import random
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from firebase_admin import firestore

# Import tattoo functions
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
import tattoo

from src.backend.dependencies import db, verify_token
from src.backend.utils.crypto import decrypt_data

router = APIRouter(tags=["share"])
VAULTSAGE_API_KEY = os.environ.get("VAULTSAGE_API_KEY")

@router.post("/api/tattoo/share/{tattoo_id}")
def generate_share_link(tattoo_id: str, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    doc_ref = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tattoo not found.")
    
    data = doc.to_dict()
    share_key = data.get("share_key")
    
    if not share_key:
        share_key = ''.join(random.choices(string.ascii_letters + string.digits, k=7))
        doc_ref.update({"share_key": share_key})
        db.collection(u'shares').document(share_key).set({
            "email": email,
            "tattoo_id": tattoo_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    # Return the domain logic will be handled by the frontend, so we just return the key
    return {"share_key": share_key}


@router.get("/api/tattoo/share_image/{share_key}")
def get_shared_image(share_key: str, key: str = None):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    share_doc = db.collection(u'shares').document(share_key).get()
    if not share_doc.exists:
        raise HTTPException(status_code=404, detail="Share not found.")
    
    share_data = share_doc.to_dict()
    email = share_data.get("email")
    tattoo_id = share_data.get("tattoo_id")
    
    doc = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tattoo not found.")
    
    t_data = doc.to_dict()
    if t_data.get("type") != "file":
        raise HTTPException(status_code=400, detail="Not a file tattoo.")
        
    is_encrypted = t_data.get("is_encrypted", False)
    stored_key = t_data.get("encryption_key")
    if is_encrypted:
        if not key or key != stored_key:
            raise HTTPException(status_code=403, detail="Invalid or missing decryption key")
            
    filename = t_data.get("filename")
    webp_filename = t_data.get("webp_filename")
    blockchain = t_data.get("blockchain", "solana")
    
    file_content = None
    
    # Try VaultSage first
    if VAULTSAGE_API_KEY:
        for try_name in [webp_filename, filename]:
            if not try_name or file_content:
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
            except Exception:
                pass

    if not file_content:
        # Fallback to blockchain
        signatures = t_data.get("signatures", [])
        try:
            if blockchain == "arweave":
                file_content = tattoo.ar_download_by_tx_ids(signatures)
            else:
                if signatures:
                    file_content = tattoo.download_by_signatures(signatures)
                else:
                    file_content = tattoo.download(tattoo_id, None, email)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch from blockchain.")
            
    if not file_content:
        raise HTTPException(status_code=404, detail="File not found anywhere.")
        
    if is_encrypted:
        try:
            file_content = decrypt_data(file_content, stored_key.encode('utf-8'))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Decryption failed: " + str(e))
        
    import mimetypes
    content_type = mimetypes.guess_type(webp_filename or filename)[0] or "application/octet-stream"
    return StreamingResponse(io.BytesIO(file_content), media_type=content_type)


@router.get("/tattoo/{share_key}", response_class=HTMLResponse)
def view_shared_tattoo(share_key: str, request: Request, key: str = None):
    if not db:
        return HTMLResponse("<h1>Database disabled.</h1>", status_code=500)
        
    share_doc = db.collection(u'shares').document(share_key).get()
    if not share_doc.exists:
        return HTMLResponse("<h1>Tattoo not found or share link invalid.</h1>", status_code=404)
        
    share_data = share_doc.to_dict()
    email = share_data.get("email")
    tattoo_id = share_data.get("tattoo_id")
    
    user_doc = db.collection(u'users').document(email).get()
    user_name = email
    if user_doc.exists:
        user_name = user_doc.to_dict().get("name", email)
    
    import html
    user_name = html.escape(user_name)
        
    doc = db.collection(u'users').document(email).collection(u'tattoos').document(tattoo_id).get()
    if not doc.exists:
        return HTMLResponse("<h1>Tattoo not found.</h1>", status_code=404)
        
    t_data = doc.to_dict()
    t_type = t_data.get("type")
    blockchain = t_data.get("blockchain", "solana")
    signatures = t_data.get("signatures", [])
    is_encrypted = t_data.get("is_encrypted", False)
    stored_key = t_data.get("encryption_key")
    
    if is_encrypted and (not key or key != stored_key):
        prompt_html = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>這是 {{user_name}} 的數位刺青!</title>
            <style>
                body {{ font-family: sans-serif; background-color: #f9f9f9; text-align: center; padding-top: 50px; }}
                input[type="text"], input[type="password"] {{ padding: 10px; font-size: 16px; border: 1px solid #ccc; border-radius: 4px; width: 300px; max-width: 80%; }}
                button {{ padding: 10px 20px; font-size: 16px; background-color: #8a2be2; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h2 style="color: #8a2be2;">這個數位刺青已被加密保護</h2>
            <p>請輸入解密金鑰以檢視內容</p>
            <form method="GET" action="/tattoo/{share_key}">
                <input type="password" name="key" placeholder="Enter decryption key..." required />
                <br>
                <button type="submit">解鎖 (Unlock)</button>
            </form>
        </body>
        </html>
        """
        return HTMLResponse(content=prompt_html)
    
    # Get tx link
    tx_link = "#"
    if blockchain == "arweave" and signatures:
        tx_link = f"https://viewblock.io/arweave/tx/{signatures[0]}"
    elif blockchain == "solana" and signatures:
        tx_link = f"https://explorer.solana.com/tx/{signatures[0]}?cluster=devnet"
        
    content_html = ""
    if t_type == "string":
        # fetch string content
        text = "Loading..."
        if blockchain == "arweave":
            try:
                res = tattoo.ar_download_by_tx_ids(signatures)
                if isinstance(res, bytes):
                    res = res.decode('utf-8')
                text = res or "Pending indexing on Arweave..."
            except:
                text = "Pending indexing on Arweave..."
        else:
            try:
                text = tattoo.download_by_signatures(signatures)
                if not text:
                    text = tattoo.download(tattoo_id, None, email)
            except:
                text = "Failed to fetch from Solana."
                
        if is_encrypted and text and "Pending indexing" not in text and "Failed to fetch" not in text:
            try:
                import base64
                ct_bytes = base64.b64decode(text)
                text = decrypt_data(ct_bytes, stored_key.encode('utf-8')).decode('utf-8')
            except Exception as e:
                text = "Decryption failed or data corrupted."
                
        # safe html escape
        import html
        text = html.escape(text)
        content_html = f'<textarea readonly style="width: 100%; height: 300px; padding: 15px; font-size: 1.2rem; color: black; background-color: #f0fff0; border-radius: 8px; border: 1px solid #ccc; resize: none;">{text}</textarea>'
    else:
        img_src = f"/api/tattoo/share_image/{share_key}"
        if key:
            import urllib.parse
            img_src += f"?key={urllib.parse.quote(key)}"
        content_html = f'<div style="text-align: center;"><img src="{img_src}" style="max-width: 100%; max-height: 70vh; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);" /></div>'
        
    base_url = str(request.base_url).rstrip('/')
    og_image_tag = ""
    if t_type == "file":
        img_src_og = f"{base_url}/api/tattoo/share_image/{share_key}"
        if key:
            import urllib.parse
            img_src_og += f"?key={urllib.parse.quote(key)}"
        og_image_tag = f'<meta property="og:image" content="{img_src_og}" />'
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>這是 {user_name} 的數位刺青!</title>
        <meta property="og:title" content="這是 {user_name} 的數位刺青!" />
        <meta property="og:description" content="數位刺青 無法刪除 無法修改 永遠存在於區塊鏈上" />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="{base_url}/tattoo/{share_key}" />
        {og_image_tag}
        <style>
            body {{ font-family: sans-serif; background-color: #f9f9f9; color: #333; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }}
            h1 {{ font-size: 2rem; color: #8a2be2; text-align: center; }}
            .section-1 {{ font-size: 0.9rem; text-align: center; color: #555; margin-bottom: 10px; font-weight: bold; }}
            .section-2 {{ font-size: 0.9rem; text-align: center; color: #666; margin-bottom: 30px; }}
            .section-2 a {{ color: #00d2ff; text-decoration: none; font-weight: bold; }}
            .content-box {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-bottom: 40px; }}
            .footer {{ text-align: center; font-size: 0.9rem; border-top: 1px solid #eee; padding-top: 20px; }}
            .footer a {{ color: #8a2be2; text-decoration: none; margin: 0 10px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h1>這是 {user_name} 的數位刺青!</h1>
        <div class="section-1">數位刺青 無法刪除 無法修改 永遠存在於區塊鏈上</div>
        <div class="section-2">
            這個刺青存在於{blockchain}區塊鏈，想自己取得區塊鏈刺青資訊？<a href="{tx_link}" target="_blank">請按這裡</a>
        </div>
        
        <div class="content-box">
            {content_html}
        </div>
        
        <div class="footer">
            <a href="/">登入數位刺青</a> | 
            <a href="https://www.5233.space/2026/05/tattoo.html" target="_blank">什麼是數位刺青</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
