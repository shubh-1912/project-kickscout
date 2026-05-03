import os
import io
import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="KickScout AI Vibe API", version="1.0.0")

# Setup Device (Will fallback to CPU in Docker, MPS locally)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🚀 API Engine booting up on {device.upper()}...")
model = SentenceTransformer('clip-ViT-B-32', device=device)

class KickScoutDB:
    def __init__(self):
        # We fetch the URI from the environment, defaulting to localhost for safety
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

        if not password:
            raise ValueError("NEO4J_PASSWORD is not set in the environment!")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def search_similar(self, vector, limit=5):
        query = """
        CALL db.index.vector.queryNodes('product_embeddings', $limit, $embedding)
        YIELD node, score
        RETURN node.id AS id, node.name AS name, node.price AS price, score
        """
        with self.driver.session() as session:
            result = session.run(query, limit=limit, embedding=vector)
            return [{"id": r["id"], "name": r["name"], "price": r["price"], "score": r["score"]} for r in result]

db = KickScoutDB()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "KickScout API"}

@app.post("/api/search/image")
async def search_image(image: UploadFile = File(...)):
    """Accepts an image, calculates the vector, and searches the graph."""
    if not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be an image.")

    try:
        # Read file into memory
        contents = await image.read()
        img = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # 1. AI Layer: Convert image to Vibe Vector
        embedding = model.encode(img).tolist()
        
        # 2. Database Layer: Find the 5 closest matches in Neo4j
        matches = db.search_similar(embedding)
        
        return {
            "message": "Vibe match successful", 
            "results": matches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")