# In app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import our Pydantic contract and the RAG "brain"
from .models import MemoRequest
from . import rag_logic

# Load .env variables *before* initializing rag_logic
load_dotenv()

app = FastAPI(title="Tax Memo RAG API", version="1.0.0")

# --- SETUP CORS MIDDLEWARE ---
# This is critical for the React frontend to be able to call the API
origins = [
    "http://localhost:3000",  # Local React dev server
    "https://project-sunny-eggplant-664.magicpatterns.app",  # The MagicPatterns UI
    # "https://your-production-frontend-domain.com",  # Add your real domain later
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (POST, GET, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- API ENDPOINTS ---


@app.get("/", tags=["Health"])
def read_root():
    """A simple health check endpoint."""
    return {"status": "Tax Memo API is running"}


@app.post("/generate_memo", tags=["Memo Generation"])
async def generate_memo_endpoint(request: MemoRequest):
    """
    Accepts the complete user profile from the 5-step UI
    and kicks off the "Memo Orchestrator" to generate a structured JSON response.
    """
    
    # 1. 'request' is now a fully validated Pydantic model
    # 2. Call the main orchestrator function from rag_logic.py
    memo_json_response = rag_logic.run_memo_orchestrator(request)
    
    # 3. Return the final structured JSON to the React app
    return memo_json_response
