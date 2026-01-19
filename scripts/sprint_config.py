import os
from dotenv import load_dotenv

# Load .env file
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

class SprintConfig:
    """Configuration for the Sprint Runner."""
    
    # Google Cloud Settings
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # Agent Settings
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.0-flash")
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
    def get_model_for_agent(cls, agent_name):
        """
        Get the optimal model for a specific agent based on their role.
        
        Args:
            agent_name: Name or role of the agent (e.g., 'orchestrator', 'Backend', 'QA_Engineer')
            
        Returns:
            str: Model name to use for this agent
            
        Environment Variable Overrides:
            MODEL_ORCHESTRATOR, MODEL_QA, MODEL_BACKEND, MODEL_FRONTEND,
            MODEL_DEVOPS, MODEL_SECURITY, MODEL_PM
        """
        # Check for agent-specific env override first
        env_key = f"MODEL_{agent_name.upper()}"
        env_override = os.getenv(env_key)
        if env_override:
            return env_override
        
        # Model mapping based on agent complexity and requirements
        model_mapping = {
            # High complexity - need advanced reasoning
            "orchestrator": os.getenv("MODEL_ORCHESTRATOR", "gemini-2.0-flash"),
            "qa_engineer": os.getenv("MODEL_QA", "gemini-2.0-flash"),
            "qa": os.getenv("MODEL_QA", "gemini-2.0-flash"),
            
            # Medium-high complexity - balanced performance
            "backend": os.getenv("MODEL_BACKEND", "gemini-2.0-flash"),
            "frontend": os.getenv("MODEL_FRONTEND", "gemini-2.0-flash"),
            "devops": os.getenv("MODEL_DEVOPS", "gemini-2.0-flash"),
            "security": os.getenv("MODEL_SECURITY", "gemini-2.0-flash"),
            "productmanager": os.getenv("MODEL_PM", "gemini-2.0-flash"),
            "pm": os.getenv("MODEL_PM", "gemini-2.0-flash"),
        }
        
        # Normalize agent name: lowercase, remove spaces and underscores
        normalized = agent_name.lower().replace(" ", "").replace("_", "")
        
        # Return matched model or fall back to global default
        return model_mapping.get(normalized, cls.MODEL_NAME)

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
