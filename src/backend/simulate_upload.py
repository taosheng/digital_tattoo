import os
import io
import asyncio
import sys

# Ensure imports work from the scripts directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import process_file_upload_worker, db
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("=== File Upload Background Worker Simulator ===\n")
    if not db:
        print("Error: Database not initialized. Please check your credentials.")
        return
        
    email = input("Enter your email (e.g., taosheng.chen@gmail.com): ").strip()
    filepath = input("Enter path to file (e.g., ../test.jpg): ").strip()
    
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return
        
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        content = f.read()
        
    # Simple content type guesser
    ext = filename.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg']:
        content_type = "image/jpeg"
    elif ext == 'png':
        content_type = "image/png"
    elif ext == 'gif':
        content_type = "image/gif"
    else:
        content_type = "application/octet-stream"
        
    original_size = len(content)
    
    # Check User
    doc_ref = db.collection(u'users').document(email)
    doc = doc_ref.get()
    if not doc.exists:
        print(f"Error: User {email} not found in Firestore.")
        return
        
    user_data = doc.to_dict()
    latest_id = user_data.get("latest_ID", 99)
    new_tattoo_id = str(latest_id + 1)
    
    # Pre-allocate exactly like create_file_tattoo API
    print(f"\n[1] Pre-allocating Firestore record with ID {new_tattoo_id} and status 'starting'...")
    doc_ref.update({"latest_ID": latest_id + 1})
    t_ref = doc_ref.collection(u'tattoos').document(new_tattoo_id)
    t_ref.set({
        "tattoo_id": new_tattoo_id,
        "type": "file",
        "original_filename": filename,
        "uploading_status": "starting",
    })
    
    print(f"\n[2] Triggering process_file_upload_worker()...\n")
    
    # Trigger the synchronous worker directly
    process_file_upload_worker(
        content=content,
        filename=filename,
        content_type=content_type,
        original_size=original_size,
        email=email,
        new_tattoo_id=new_tattoo_id,
        doc_ref=doc_ref
    )
    
    print("\n=== Simulation Complete ===")
    print(f"Check your Firestore dashboard for ID {new_tattoo_id} to see the final status and signatures.")

if __name__ == "__main__":
    asyncio.run(main())
