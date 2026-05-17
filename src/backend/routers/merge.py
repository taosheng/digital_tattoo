import os
import base64
import httpx
from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
import uuid
import string
import random
import io

from src.backend.dependencies import db, verify_token
from src.backend.utils.vaultsage import get_or_create_directory, upload_file_to_vaultsage

router = APIRouter(prefix="/api/merge", tags=["merge"])

class ShareRequest(BaseModel):
    password: str = None

@router.post("/super_merge")
async def super_merge(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    email: str = Depends(verify_token)
):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="XAI API Key is missing. Cannot perform merge.")

    # 1. Verify User points
    doc_ref = db.collection(u'users').document(email)
    user_data = doc_ref.get().to_dict()
    points = user_data.get('points', 0)
    
    if points <= 0:
        raise HTTPException(status_code=403, detail="Insufficient Points. Super Merge costs 1 point.")
        
    # 2. Read Files and convert to base64
    content1 = await file1.read()
    content2 = await file2.read()
    
    if len(content1) > 10 * 1024 * 1024 or len(content2) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Files must be smaller than 10MB")
        
    img1_base64 = base64.b64encode(content1).decode("utf-8")
    img2_base64 = base64.b64encode(content2).decode("utf-8")
    
    # 3. Call xAI (Two-Step Process via pure HTTP requests)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 3.1: Analyze BOTH images to create a perfect fusion prompt
        try:
            vision_payload = {
                "model": "grok-4.3",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "I am providing two images. \n"
                                    "Image 1 (Base): Provides the exact body, clothing, pose, lighting, and background.\n"
                                    "Image 2 (Face): Provides the exact facial features, hair, and head structure.\n\n"
                                    "Your task: Write an extremely detailed, cohesive, and highly descriptive prompt for an image generation AI. "
                                    "This prompt must describe a single, photorealistic photograph. "
                                    "The photograph MUST perfectly recreate the scene, clothing, posture, and background of Image 1. "
                                    "However, the person in the photograph MUST have their face and head described exactly as the person in Image 2. "
                                    "Be very specific about the face structure, eye shape/color, nose, mouth, skin tone, hair style, and facial expression from Image 2. "
                                    "Be very specific about the clothing style, colors, pose, lighting, and background setting from Image 1. "
                                    "Output ONLY the final image generation prompt, nothing else. Do not add conversational text."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{file1.content_type};base64,{img1_base64}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{file2.content_type};base64,{img2_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            vision_res = await client.post("https://api.x.ai/v1/chat/completions", headers=headers, json=vision_payload)
            vision_res.raise_for_status()
            vision_data = vision_res.json()
            fusion_prompt = vision_data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            err_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                err_detail += f" - Response: {e.response.text}"
            raise HTTPException(status_code=500, detail=f"Failed to analyze images and create prompt: {err_detail}")

        # Step 3.2: Generate the merged image using the AI-generated fusion prompt
        final_prompt = fusion_prompt
        
        try:
            imagine_payload = {
                "model": "grok-imagine-image-quality",
                "prompt": final_prompt,
                "image": f"data:{file1.content_type};base64,{img1_base64}", # Pass left image as a structural reference
                "aspect_ratio": "1:1",
                "resolution": "1k" 
            }
            
            imagine_res = await client.post("https://api.x.ai/v1/images/generations", headers=headers, json=imagine_payload)
            imagine_res.raise_for_status()
            imagine_data = imagine_res.json()
            merged_image_url = imagine_data["data"][0]["url"]
        except Exception as e:
            err_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                err_detail += f" - Response: {e.response.text}"
            raise HTTPException(status_code=500, detail=f"AI generation failed: {err_detail}")
        
    # 4. Upload to Vaultsage and Save to Firestore
    try:
        # Download the result image first to upload it
        async with httpx.AsyncClient() as client:
            res_img = await client.get(merged_image_url, timeout=30.0)
            merged_content = res_img.content
            
        vaultsage_path = email.replace('@', '_at_').replace('.', '_')
        dir_id = get_or_create_directory(vaultsage_path)
        
        timestamp = int(time.time())
        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        filename1 = f"merge_in1_{timestamp}_{rand_str}.jpg"
        filename2 = f"merge_in2_{timestamp}_{rand_str}.jpg"
        filename_res = f"merge_result_{timestamp}_{rand_str}.jpg"
        
        upload_file_to_vaultsage(filename1, content1, file1.content_type, dir_id)
        upload_file_to_vaultsage(filename2, content2, file2.content_type, dir_id)
        upload_file_to_vaultsage(filename_res, merged_content, "image/jpeg", dir_id)
        
        # Save to user's merges collection
        merge_id = f"m_{timestamp}"
        db.collection(u'users').document(email).collection(u'merges').document(merge_id).set({
            "timestamp": timestamp,
            "filename_left": filename1,
            "filename_right": filename2,
            "filename_result": filename_res,
            "owner_email": email,
            "owner_name": user_data.get("name", "Unknown")
        })
        
    except Exception as ve:
        print("Vaultsage upload warning:", ve)
        merge_id = None
        # We don't fail the user request if vaultsage upload fails, we just log it
        
    # 5. Deduct points
    new_points = points - 1
    doc_ref.update({"points": new_points})
    
    return {
        "status": "success",
        "new_points": new_points,
        "merged_image_url": merged_image_url,
        "merge_id": merge_id
    }

@router.post("/share/{merge_id}")
def generate_merge_share_link(merge_id: str, req: ShareRequest, email: str = Depends(verify_token)):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    doc_ref = db.collection(u'users').document(email).collection(u'merges').document(merge_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Merge record not found.")
    
    # Generate unique share key
    share_key = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    share_data = {
        "email": email,
        "merge_id": merge_id,
        "timestamp": int(time.time()),
        "password": req.password if req.password else None
    }
    
    db.collection(u'merge_shares').document(share_key).set(share_data)
    
    return {"status": "success", "share_key": share_key}


@router.get("/share_info/{share_key}")
def get_merge_share_info(share_key: str, password: str = None):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    
    share_doc = db.collection(u'merge_shares').document(share_key).get()
    if not share_doc.exists:
        raise HTTPException(status_code=404, detail="Share link not found.")
    
    share_data = share_doc.to_dict()
    
    has_password = bool(share_data.get("password"))
    if has_password and share_data.get("password") != password:
        return {"status": "locked", "requires_password": True}
        
    email = share_data.get("email")
    merge_id = share_data.get("merge_id")
    
    merge_doc = db.collection(u'users').document(email).collection(u'merges').document(merge_id).get()
    if not merge_doc.exists:
        raise HTTPException(status_code=404, detail="Merge record missing.")
        
    m_data = merge_doc.to_dict()
    
    return {
        "status": "success",
        "requires_password": False,
        "owner_name": m_data.get("owner_name", "Unknown"),
        "timestamp": m_data.get("timestamp"),
        "share_key": share_key
    }


@router.get("/share_image/{share_key}/{side}")
async def get_merge_share_image(share_key: str, side: str, password: str = Query(None)):
    if side not in ["left", "right", "result"]:
        raise HTTPException(status_code=400, detail="Invalid side parameter.")
        
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
        
    VAULTSAGE_API_KEY = os.environ.get("VAULTSAGE_API_KEY")
    if not VAULTSAGE_API_KEY:
        raise HTTPException(status_code=500, detail="VaultSage not configured.")
        
    share_doc = db.collection(u'merge_shares').document(share_key).get()
    if not share_doc.exists:
        raise HTTPException(status_code=404, detail="Share link not found.")
        
    share_data = share_doc.to_dict()
    if share_data.get("password") and share_data.get("password") != password:
        raise HTTPException(status_code=403, detail="Invalid password.")
        
    email = share_data.get("email")
    merge_id = share_data.get("merge_id")
    
    merge_doc = db.collection(u'users').document(email).collection(u'merges').document(merge_id).get()
    if not merge_doc.exists:
        raise HTTPException(status_code=404, detail="Merge record missing.")
        
    m_data = merge_doc.to_dict()
    
    filename = None
    if side == "left":
        filename = m_data.get("filename_left")
    elif side == "right":
        filename = m_data.get("filename_right")
    elif side == "result":
        filename = m_data.get("filename_result")
        
    if not filename:
        raise HTTPException(status_code=404, detail="Image not found in record.")
        
    # Download from Vaultsage
    try:
        async with httpx.AsyncClient() as client:
            hx = await client.get(
                f"https://api.vaultsage.ai/api/v1/files/search?keyword={filename}",
                headers={"X-Api-Key": VAULTSAGE_API_KEY},
                timeout=10.0
            )
            if hx.status_code == 200:
                res_data = hx.json()
                files_list = res_data.get("files", [])
                if files_list:
                    file_id = files_list[0]["id"]
                    dl = await client.post(
                        "https://api.vaultsage.ai/api/v1/files/download",
                        headers={"X-Api-Key": VAULTSAGE_API_KEY},
                        json={"file_ids": [file_id]},
                        timeout=30.0
                    )
                    if dl.status_code == 200 and dl.content:
                        return StreamingResponse(io.BytesIO(dl.content), media_type="image/jpeg")
    except Exception as e:
        print(f"Failed to fetch image from VaultSage: {e}")
        
    raise HTTPException(status_code=404, detail="Could not retrieve image from storage.")
