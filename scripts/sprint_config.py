import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class SprintConfig:
    """Configuration for the Sprint Runner."""
    
    # Google Cloud Settings
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Agent Settings
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3-flash-preview")
    CONCURRENCY_LIMIT = int(os.getenv("CONCURRENCY_LIMIT", "3"))
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(BASE_DIR)
    PROMPT_BASE_DIR = os.getenv("PROMPT_BASE_DIR", os.path.join(PARENT_DIR, "prompts"))
    SPRINT_DIR = os.getenv("SPRINT_DIR", os.path.join(PARENT_DIR, "project_tracking"))
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        if not cls.GOOGLE_API_KEY:
             print("WARNING: GOOGLE_API_KEY not found in environment.")

    @classmethod
    def get_role_map(cls):
        return {
            "Backend": "agent_backend.md",
            "Frontend": "agent_frontend.md",
            "DevOps": "agent_devops.md",
            "QA": "agent_qa.md",
            "Security": "agent_security.md",
            "PM": "agent_product_management.md"
        }
