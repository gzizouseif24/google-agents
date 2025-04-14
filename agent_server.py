from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
from pathlib import Path
import logging
import os
import sys
from multi_tool_agent.agent import root_agent, Runner, InMemorySessionService
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check required environment variables
required_env_vars = [
    'GOOGLE_API_KEY',
    'OPENWEATHERMAP_API_KEY',
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    print("Error: Missing required environment variables:")
    for var in missing_vars:
        print(f"- {var}")
    print("\nPlease set these environment variables before starting the server.")
    print("You can set them using:")
    print("  export VARIABLE=value  # On Linux/Mac")
    print("  set VARIABLE=value     # On Windows")
    print("Or by providing them in docker-compose:")
    print("  docker-compose run -e GOOGLE_API_KEY=your_key -e OPENWEATHERMAP_API_KEY=your_key weather-chat")
    sys.exit(1)

app = FastAPI(title="Multi-Tool Agent Chat Interface")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create templates directory if it doesn't exist
templates_dir = Path("templates")
templates_dir.mkdir(exist_ok=True)

# Mount the templates directory
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Initialize session service and runner
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="multi_tool_agent",
    session_service=session_service
)

class ChatMessage(BaseModel):
    message: str
    session_id: str = "s_00001"  # Default session ID

class SessionPreferences(BaseModel):
    temperature_unit: str = "Celsius"
    default_city: str = "Tunis"
    language: str = "English"

class SessionCreate(BaseModel):
    session_name: str
    preferences: SessionPreferences

class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    message: str

# Store session mappings (name -> id)
session_mappings: Dict[str, str] = {"default": "s_00001"}

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"s_{str(uuid.uuid4())[:8]}"

@app.on_event("startup")
async def startup_event():
    """Create the default session when the API starts"""
    try:
        # Create default session
        create_default_session()
        logger.info("Successfully created initial session")
        
        # Log environment configuration
        logger.info("Environment configuration:")
        logger.info(f"- GOOGLE_GENAI_USE_VERTEXAI: {os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'Not set')}")
        logger.info(f"- MODEL_GEMINI_2_0_FLASH: {os.getenv('MODEL_GEMINI_2_0_FLASH', 'Not set')}")
        logger.info("- API keys configured: ✓")
        
    except Exception as e:
        logger.error(f"Failed to create initial session: {str(e)}")

def create_default_session():
    """Create the default session with initial state"""
    initial_state = {
        "user_preference_temperature_unit": "Celsius",
        "user_preference_city": "Tunis",
        "user_preference_language": "English"
    }
    
    session_service.create_session(
        app_name="multi_tool_agent",
        user_id="u_00001",
        session_id="s_00001",
        state=initial_state
    )

@app.get("/")
async def read_root():
    """Serve the HTML interface"""
    return FileResponse("templates/index.html")

@app.get("/health")
async def health_check():
    """Check if the service is healthy and environment is configured"""
    return {
        "status": "healthy",
        "environment_configured": all(os.getenv(var) for var in required_env_vars),
        "google_ai_configured": bool(os.getenv('GOOGLE_API_KEY')),
        "weather_api_configured": bool(os.getenv('OPENWEATHERMAP_API_KEY')),
        "active_sessions": len(session_mappings)
    }

@app.post("/session/", response_model=SessionResponse)
async def create_session(session_req: SessionCreate):
    """Create a new chat session with custom preferences"""
    try:
        # Generate new session ID
        session_id = generate_session_id()
        
        # Create initial state from preferences
        initial_state = {
            "user_preference_temperature_unit": session_req.preferences.temperature_unit,
            "user_preference_city": session_req.preferences.default_city,
            "user_preference_language": session_req.preferences.language
        }
        
        # Create session
        session_service.create_session(
            app_name="multi_tool_agent",
            user_id="u_00001",
            session_id=session_id,
            state=initial_state
        )
        
        # Store session mapping
        session_mappings[session_req.session_name] = session_id
        
        return SessionResponse(
            session_id=session_id,
            session_name=session_req.session_name,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/")
async def chat(message: ChatMessage):
    """Process a chat message through the multi-tool agent"""
    try:
        # Create message content
        from google.genai import types
        content = types.Content(
            role='user',
            parts=[types.Part(text=message.message)]
        )

        # Process message through agent
        final_response = None
        async for event in runner.run_async(
            user_id="u_00001",
            session_id=message.session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                break

        if final_response:
            return {"response": final_response}
        else:
            return {"response": "I'm sorry, I couldn't process your request."}

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 