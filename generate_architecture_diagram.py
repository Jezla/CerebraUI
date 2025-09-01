#!/usr/bin/env python3
"""
Generate PNG image from Mermaid architecture diagram
"""

import requests
import base64

def generate_architecture_png():
    """Generate PNG from Mermaid architecture diagram"""
    
    # Mermaid architecture diagram content
    mermaid_content = """graph TB
    subgraph "Frontend (SvelteKit)"
        A[User Interface] --> B[Components]
        B --> C[Stores & State Management]
        C --> D[API Layer]
        D --> E[WebSocket Client]
    end
    
    subgraph "Backend (FastAPI)"
        F[FastAPI Server] --> G[Authentication]
        F --> H[API Routes]
        F --> I[WebSocket Server]
        F --> J[Database Layer]
        F --> K[AI Services]
        F --> L[File Storage]
        F --> M[Vector Database]
    end
    
    subgraph "External Services"
        N[Ollama API] --> K
        O[OpenAI API] --> K
        P[LDAP Server] --> G
        Q[OAuth Providers] --> G
        R[Vector DB] --> M
    end
    
    subgraph "Infrastructure"
        S[PostgreSQL/MySQL] --> J
        T[Redis] --> I
        U[ChromaDB] --> M
        V[File System] --> L
    end
    
    subgraph "AI Models & Tools"
        W[LLM Models] --> K
        X[Embedding Models] --> K
        Y[Image Generation] --> K
        Z[Audio Processing] --> K
    end
    
    A -.->|HTTP/HTTPS| F
    D -.->|REST API| H
    E -.->|WebSocket| I
    
    style A fill:#e3f2fd
    style F fill:#f3e5f5
    style K fill:#e8f5e8
    style G fill:#fff3e0"""
    
    try:
        # Use Mermaid Live Editor API
        url = "https://mermaid.ink/img/"
        
        # Encode the Mermaid content
        encoded_content = base64.b64encode(mermaid_content.encode()).decode()
        
        # Create the full URL with larger dimensions for architecture diagram
        full_url = f"{url}{encoded_content}?type=png&theme=default"
        
        print("Generating architecture diagram PNG...")
        
        # Download the image
        response = requests.get(full_url, timeout=30)
        response.raise_for_status()
        
        # Save the image
        with open('website_architecture.png', 'wb') as f:
            f.write(response.content)
        
        print("✅ Architecture diagram PNG generated successfully: website_architecture.png")
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate PNG: {e}")
        return False

if __name__ == "__main__":
    generate_architecture_png()
