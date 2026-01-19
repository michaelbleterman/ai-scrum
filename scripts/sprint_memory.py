"""
Long-term memory service for sprint framework.
Stores and retrieves task outcomes, patterns, and learnings across sprints.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Conditional imports to handle case where dependencies aren't installed yet (for initial load)
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
except ImportError:
    chromadb = None
    SentenceTransformer = None


@dataclass
class MemoryEntry:
    """Structured memory entry"""
    memory_id: str
    timestamp: str
    scope: str  # 'project', 'general', 'user'
    memory_type: str  # 'task_outcome', 'pattern', 'error_resolution', 'decision'
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


class SprintMemoryBank:
    """
    Long-term memory storage using ChromaDB vector database.
    Enables semantic search across past sprint experiences.
    """
    
    def __init__(self, project_root: str, enable_memory: bool = True):
        """
        Initialize memory bank for a specific project.
        
        Args:
            project_root: Root directory of the project
            enable_memory: Feature flag to enable/disable memory (default: True)
        """
        self.project_root = Path(project_root).resolve()
        self.enable_memory = enable_memory
        
        if not self.enable_memory:
            return
            
        if chromadb is None:
            print("WARNING: ChromaDB or SentenceTransformer not installed. Memory disabled.")
            self.enable_memory = False
            return
        
        # Memory storage location
        self.memory_dir = self.project_root / ".agent" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(self.memory_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create collection for project memories
        self.collection = self.client.get_or_create_collection(
            name="sprint_memories",
            metadata={"project": str(self.project_root)}
        )
        
        # Initialize embedding model (lightweight, fast)
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"WARNING: Failed to load embedding model: {e}. Memory disabled.")
            self.enable_memory = False
        
    def store(
        self,
        content: str,
        memory_type: str,
        scope: str = 'project',
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store a new memory entry.
        
        Args:
            content: The memory content (text)
            memory_type: Type of memory ('task_outcome', 'pattern', 'error_resolution', 'decision')
            scope: Memory scope ('project', 'general', 'user')
            metadata: Additional structured metadata
            
        Returns:
            memory_id: Unique identifier for the stored memory
        """
        if not self.enable_memory:
            return ""
        
        # Generate unique ID
        memory_id = f"{scope}_{memory_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Create embedding
            embedding = self.encoder.encode(content).tolist()
            
            # Prepare metadata (ensure flat structure for ChromaDB filtering if needed, 
            # though it supports dicts, flat is safer for metadata filtering logic usually.
            # Convert values to supported types (str, int, float, bool))
            clean_meta = {}
            if metadata:
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)

            full_metadata = {
                "timestamp": datetime.now().isoformat(),
                "scope": scope,
                "memory_type": memory_type,
                "project": str(self.project_root),
                **clean_meta
            }
            
            # Store in ChromaDB
            self.collection.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[full_metadata]
            )
            
            return memory_id
        except Exception as e:
            print(f"Error storing memory: {e}")
            return ""
    
    def recall(
        self,
        query: str,
        memory_type: Optional[str] = None,
        scope: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories using semantic search.
        
        Args:
            query: Search query (what you want to remember)
            memory_type: Filter by memory type
            scope: Filter by scope
            top_k: Number of results to return
            
        Returns:
            List of memory entries with relevance scores
        """
        if not self.enable_memory:
            return []
        
        try:
            # Build filter
            where_filter = {}
            if memory_type:
                where_filter["memory_type"] = memory_type
            if scope:
                where_filter["scope"] = scope
            
            # Check if collection is empty
            if self.collection.count() == 0:
                return []

            # Query with semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter if where_filter else None
            )
            
            # Format results
            memories = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    memories.append({
                        'memory_id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if results.get('distances') else 0.0
                    })
            
            return memories
        except Exception as e:
            print(f"Error recalling memory: {e}")
            return []
    
    def summarize_session(self, sprint_file: str) -> str:
        """
        Generate a concise summary of a sprint session for context injection.
        
        Args:
            sprint_file: Path to sprint markdown file
            
        Returns:
            Compressed summary of key decisions, blockers, and patterns
        """
        if not self.enable_memory:
            return ""
        
        try:
            if not os.path.exists(sprint_file):
                return ""

            # Read sprint file
            with open(sprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Simple heuristic extraction
            lines = content.split('\n')
            completed_tasks = [l.strip() for l in lines if '[x]' in l]
            blocked_tasks = [l.strip() for l in lines if '[!]' in l]
            
            # Extract just the descriptions
            completed_desc = [t.split(']', 1)[1].strip() for t in completed_tasks[:5]] # Limit to 5
            blocked_desc = [t.split(']', 1)[1].strip() for t in blocked_tasks[:5]]
            
            summary = f"""
Sprint Summary:
- Completed: {len(completed_tasks)} tasks
  {chr(10).join(['  * ' + c for c in completed_desc])}
- Blocked: {len(blocked_tasks)} tasks
  {chr(10).join(['  * ' + b for b in blocked_desc])}
            """.strip()
            
            return summary
        except Exception as e:
            print(f"Error summarizing session: {e}")
            return ""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory bank statistics"""
        if not self.enable_memory:
            return {"enabled": False}
        
        try:
            count = self.collection.count()
            
            # Get metadata stats (fetching all might be expensive for large dbs, but fine for now)
            all_items = self.collection.get()
            types = {}
            scopes = {}
            
            if all_items['metadatas']:
                for meta in all_items['metadatas']:
                    mem_type = meta.get('memory_type', 'unknown')
                    scope = meta.get('scope', 'unknown')
                    types[mem_type] = types.get(mem_type, 0) + 1
                    scopes[scope] = scopes.get(scope, 0) + 1
            
            return {
                "enabled": True,
                "total_memories": count,
                "by_type": types,
                "by_scope": scopes,
                "storage_path": str(self.memory_dir)
            }
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    # Simple test run
    memory = SprintMemoryBank(".", enable_memory=True)
    if memory.enable_memory:
        print("Memory system initialized successfully.")
        mid = memory.store("Test memory", "test")
        print(f"Stored memory: {mid}")
        print(f"Stats: {memory.get_statistics()}")
    else:
        print("Memory system disabled (dependencies missing?).")
