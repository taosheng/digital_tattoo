import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import credentials, firestore, initialize_app

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

security = HTTPBearer()

def get_db():
    return db

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    # Simple check for our JWT which we are returning directly. In production, sign cookies.
    # For simplicity, our frontend uses the user email as the sessionToken mock if we bypass complex signing.
    token = credentials.credentials
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return token
