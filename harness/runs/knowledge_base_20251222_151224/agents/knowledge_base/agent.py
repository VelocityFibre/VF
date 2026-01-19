import os
import sys

# Explicit path to shared directory
SHARED_DIR = '/home/louisdup/Agents/claude/harness/shared'
if SHARED_DIR not in sys.path:
    sys.path.insert(0, SHARED_DIR)

from base_agent import BaseAgent
from typing import List, Dict, Any
import json

class KnowledgeBaseAgent(BaseAgent):
    """
    Knowledge Base Agent specialized for managing and querying information repositories
    
    Inherits from BaseAgent with specialized knowledge management capabilities
    """

    def __init__(self, anthropic_api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Initialize KnowledgeBaseAgent with base agent initialization
        
        :param anthropic_api_key: Anthropic API key for Claude interactions
        :param model: Claude model to use, defaults to haiku
        """
        super().__init__(anthropic_api_key, model)
        
        # Agent-specific initialization for knowledge base
        self._documents_directory = os.path.join(
            os.path.expanduser('~/velocity-fibre-knowledge'), 
            'documents'
        )
        os.makedirs(self._documents_directory, exist_ok=True)

    def define_tools(self) -> List[Dict[str, Any]]:
        """
        Define tools specific to knowledge base management
        
        :return: List of tool definitions for knowledge base operations
        """
        return [
            {
                "name": "list_documents",
                "description": "List all documents in the knowledge base",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string", 
                            "description": "Optional category to filter documents"
                        }
                    }
                }
            },
            {
                "name": "add_document",
                "description": "Add a new document to the knowledge base",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "category": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["filename", "content"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute knowledge base specific tools
        
        :param tool_name: Name of the tool to execute
        :param tool_input: Input parameters for the tool
        :return: JSON string with execution result
        """
        try:
            if tool_name == "list_documents":
                category = tool_input.get("category")
                documents = os.listdir(self._documents_directory)
                if category:
                    documents = [doc for doc in documents if category in doc]
                return json.dumps({"documents": documents})
            
            elif tool_name == "add_document":
                filename = tool_input.get("filename")
                content = tool_input.get("content")
                category = tool_input.get("category", "uncategorized")
                
                filepath = os.path.join(self._documents_directory, 
                                        f"{category}_{os.path.basename(filename)}")
                
                with open(filepath, 'w') as f:
                    f.write(content)
                
                return json.dumps({
                    "status": "success", 
                    "filepath": filepath,
                    "filename": os.path.basename(filename)
                })
            
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_system_prompt(self) -> str:
        """
        Generate system prompt for knowledge base interactions
        
        :return: System prompt tailored to knowledge base agent
        """
        return """You are a FibreFlow Knowledge Base Agent.

Your primary responsibilities:
- Manage and organize documents
- Retrieve and list documents
- Add new documents to the knowledge base
- Categorize and tag documents efficiently

Available tools:
- list_documents: List documents, optionally filtered by category
- add_document: Add a new document to the knowledge base

Use these tools to help users manage and interact with their knowledge repository.
"""

    def create_app_docs(self, app_name: str = "fibreflow", sections: List[str] = None) -> Dict[str, str]:
        """
        Generate comprehensive application documentation.

        :param app_name: Name of the application to document
        :param sections: List of sections to generate. Options: ["architecture", "api", "deployment", "env-vars"]
        :return: Dictionary of generated markdown documentation
        """
        if not sections:
            sections = ["architecture", "api", "deployment", "env-vars"]

        docs = {}

        if "architecture" in sections:
            docs["architecture"] = f"""# {app_name.capitalize()} Architecture

## Overview
{app_name.capitalize()} is a key component of the Velocity Fibre ecosystem.

### System Components
- **Backend**: Python-based microservices
- **Frontend**: TypeScript/React
- **Database**: Neon PostgreSQL
- **Authentication**: Clerk

### Key Design Principles
- Microservices architecture
- Event-driven design
- Scalable and modular
"""

        if "api" in sections:
            docs["api"] = f"""# {app_name.capitalize()} API Endpoints

## Authentication Routes
- `POST /api/auth/login`: User authentication
- `POST /api/auth/register`: User registration
- `POST /api/auth/reset-password`: Password reset

## Core Functionality Routes
- `GET /api/resources`: List available resources
- `POST /api/resources`: Create new resource
- `PUT /api/resources/:id`: Update resource
- `DELETE /api/resources/:id`: Delete resource

## Example Request/Response
```python
# Example API Call
response = requests.get('/api/resources')
```
"""

        if "deployment" in sections:
            docs["deployment"] = f"""# {app_name.capitalize()} Deployment Procedures

## Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Docker (optional)

## Deployment Steps
1. Clone repository
```bash
git clone https://github.com/velocityfibre/{app_name}
cd {app_name}
```

2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure environment
```bash
cp .env.example .env
# Edit .env with your configurations
```

4. Run migrations
```bash
python manage.py migrate
```

5. Start application
```bash
python manage.py runserver
```

## Deployment Targets
- Local development
- Staging server
- Production VF Server

## Deployment Checklist
- [ ] Backup database
- [ ] Pull latest code
- [ ] Install dependencies
- [ ] Run database migrations
- [ ] Restart services
- [ ] Verify deployment
"""

        if "env-vars" in sections:
            docs["env-vars"] = f"""# {app_name.capitalize()} Environment Variables

## Required Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Django secret key
- `DEBUG`: Enable debug mode (true/false)

## Optional Variables
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `SENTRY_DSN`: Error tracking endpoint
- `CACHE_BACKEND`: Redis/Memcached configuration

## Example .env File
```bash
DATABASE_URL=postgresql://user:pass@localhost/fibreflow
SECRET_KEY=randomlongstring
DEBUG=false
ALLOWED_HOSTS=app.fibreflow.app,localhost
```
"""

        # Automatically add to documents using existing tool
        for section, content in docs.items():
            self.execute_tool("add_document", {
                "filename": f"{app_name}_{section}.md",
                "category": "apps",
                "content": content
            })

        return docs