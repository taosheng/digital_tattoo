import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from src.backend.routers import auth, tattoo, share, merge

app = FastAPI()
app.include_router(auth.router)
app.include_router(tattoo.router)
app.include_router(share.router)
app.include_router(merge.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend for production serving
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    @app.get("/")
    def no_frontend():
         return {"message": "Frontend static files not built yet. Access /api endpoint directly or run Vite."}
