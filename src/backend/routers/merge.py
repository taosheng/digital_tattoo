import os
import base64
import httpx
from fastapi import APIRouter, File, UploadFile, Depends, Form, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
import time

from src.backend.dependencies import db, verify_token
from src.backend.utils.vaultsage import get_or_create_directory, upload_file_to_vaultsage

router = APIRouter(prefix="/api/merge", tags=["merge"])

# Initialize AsyncOpenAI client
xai_client = None
if os.environ.get("XAI_API_KEY"):
    xai_client = AsyncOpenAI(
        base_url="https://api.x.ai/v1",
        api_key=os.environ.get("XAI_API_KEY")
    )

@router.post("/super_merge")
async def super_merge(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    aggressive: str = Form("false"),
    email: str = Depends(verify_token)
):
    if not db:
        raise HTTPException(status_code=500, detail="Database disabled.")
    if not xai_client:
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
    
    # 3. Call xAI
    is_aggressive = aggressive.lower() == "true"
    prompt = "Combine the subjects from these two images to create a brand new character. The new character should undergo a 'Saiyan Fusion', blending their hairstyles and facial features. The character must wear the classic Metamoran fusion dance outfit (black and blue vest, white baggy pants, and sash), in a high-quality modern anime style."
    
    if is_aggressive:
        prompt = "AGGRESSIVE FUSION: Combine the subjects from these two images to create an ultimate, highly detailed, dramatic brand new character. Extremely dynamic pose, intense aura and lighting, 'Saiyan Fusion' blending their hairstyles and facial features. The character must wear the classic Metamoran fusion dance outfit, in a high-quality modern anime style. Emphasize epic power!"

    try:
        response = await xai_client.images.generate(
            model="grok-imagine-image-quality",
            prompt=prompt,
            extra_body={
                "images": [
                    f"data:{file1.content_type};base64,{img1_base64}",
                    f"data:{file2.content_type};base64,{img2_base64}"
                ],
                "aspect_ratio": "1:1",
                "resolution": "1k" 
            }
        )
        merged_image_url = response.data[0].url
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
        
    # 4. Upload to Vaultsage
    try:
        # Download the result image first to upload it
        async with httpx.AsyncClient() as client:
            res_img = await client.get(merged_image_url, timeout=30.0)
            merged_content = res_img.content
            
        vaultsage_path = email.replace('@', '_at_').replace('.', '_')
        dir_id = get_or_create_directory(vaultsage_path)
        
        timestamp = int(time.time())
        upload_file_to_vaultsage(f"merge_in1_{timestamp}.jpg", content1, file1.content_type, dir_id)
        upload_file_to_vaultsage(f"merge_in2_{timestamp}.jpg", content2, file2.content_type, dir_id)
        upload_file_to_vaultsage(f"merge_result_{timestamp}.jpg", merged_content, "image/jpeg", dir_id)
    except Exception as ve:
        print("Vaultsage upload warning:", ve)
        # We don't fail the user request if vaultsage upload fails, we just log it
        
    # 5. Deduct points
    new_points = points - 1
    doc_ref.update({"points": new_points})
    
    return {
        "status": "success",
        "new_points": new_points,
        "merged_image_url": merged_image_url
    }
