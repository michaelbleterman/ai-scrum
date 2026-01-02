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
    
    # Project Root - can be set dynamically at runtime
    PROJECT_ROOT = None
    
    # Sprint Directory - defaults to CWD/project_tracking if PROJECT_ROOT not set
    SPRINT_DIR = None
    
    @classmethod
    def set_project_root(cls, project_root):
        """Set the project root directory dynamically."""
        cls.PROJECT_ROOT = os.path.abspath(project_root)
        cls.SPRINT_DIR = os.path.join(cls.PROJECT_ROOT, "project_tracking")
    
    @classmethod
    def get_sprint_dir(cls):
        """Get the sprint directory, using PROJECT_ROOT or falling back to env/default."""
        if cls.SPRINT_DIR:
            return cls.SPRINT_DIR
        # Fallback to environment variable or default
        return os.getenv("SPRINT_DIR", os.path.join(cls.PARENT_DIR, "project_tracking"))
    
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
