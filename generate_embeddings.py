import os
import torch
from PIL import Image
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
from dotenv import load_dotenv
from tqdm import tqdm
import kagglehub

# 1. Load environment variables (.env)
load_dotenv()

# 2. Setup Hardware Acceleration (Mac GPU)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"🚀 Using hardware acceleration: {device.upper()}")

# 3. Load the CLIP Model
print("📥 Loading CLIP model (this might take a minute the first time)...")
model = SentenceTransformer('clip-ViT-B-32', device=device)

class KickScoutAI:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"), 
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
        )

    def get_unprocessed_products(self):
        """Find products in Neo4j that don't have an AI vector yet."""
        with self.driver.session() as session:
            query = """
            MATCH (p:Product)-[:IS_STYLE]->(s:Silhouette)
            WHERE p.embedding IS NULL 
              AND (toLower(s.type) CONTAINS 'shoe' 
                   OR toLower(s.type) CONTAINS 'sneaker'
                   OR toLower(s.type) CONTAINS 'boot')
            RETURN p.id AS id
            """
            result = session.run("MATCH (p:Product) WHERE p.embedding IS NULL RETURN p.id AS id")
            return [row["id"] for row in result]

    def update_embedding(self, product_id, vector):
        """Save the 512-dimensional array back to the specific Product node."""
        with self.driver.session() as session:
            session.run(
                "MATCH (p:Product {id: $id}) SET p.embedding = $vector",
                id=product_id, vector=vector
            )

    def create_vector_index(self):
        """Create the index for fast similarity searching (Neo4j 5.12 compatible)."""
        with self.driver.session() as session:
            try:
                # The legacy procedure call for older 5.x databases
                session.run("CALL db.index.vector.createNodeIndex('product_embeddings', 'Product', 'embedding', 512, 'cosine')")
                print("✅ Vector Index created.")
            except Exception as e:
                # If you run the script twice, it safely catches the "already exists" error
                if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                    print("✅ Vector Index verified (already exists).")
                else:
                    print(f"⚠️ Index notification: {e}")

def run_day_2():
    ai = KickScoutAI()
    
    # Locate the images downloaded yesterday
    dataset_path = kagglehub.dataset_download("paramaggarwal/fashion-product-images-small")
    image_dir = os.path.join(dataset_path, "images")

    product_ids = ai.get_unprocessed_products()
    
    if not product_ids:
        print("💡 All products already have embeddings!")
        return

    test_batch = product_ids
    print(f"🧠 Generating embeddings for {len(test_batch)} products...")
    
    for pid in tqdm(test_batch):
        img_path = f"{image_dir}/{pid}.jpg"
        if os.path.exists(img_path):
            try:
                # Open image, convert to vector, save to DB
                img = Image.open(img_path).convert("RGB")
                embedding = model.encode(img).tolist()
                ai.update_embedding(pid, embedding)
            except Exception as e:
                print(f"Skipped {pid}: {e}")
                continue 

    ai.create_vector_index()
    ai.driver.close()

if __name__ == "__main__":
    run_day_2()