from neo4j import GraphDatabase
import time
import os
from dotenv import load_dotenv

print(f"📍 Current Working Directory: {os.getcwd()}")
print(f"📂 Files in this directory: {os.listdir('.')}")

# Check if .env is actually found
dotenv_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(dotenv_path):
    print("✅ .env file found!")
else:
    print("❌ .env file NOT FOUND at this path.")

load_dotenv()

class KickScoutDB:
    def __init__(self):
        # Fetch from environment variables
        
        uri = os.getenv("NEO4J_URI")
        print(f"DEBUG: {uri}")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def setup_schema(self):
        """Create constraints and indexes. Idempotent using IF NOT EXISTS."""
        with self.driver.session() as session:
            print("Setting up constraints and indexes...")
            session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
            session.run("CREATE CONSTRAINT brand_name IF NOT EXISTS FOR (b:Brand) REQUIRE b.name IS UNIQUE")
            session.run("CREATE INDEX product_name_idx IF NOT EXISTS FOR (p:Product) ON (p.name)")

    def load_data(self):
        """Execute the LOAD CSV command programmatically."""
        # This assumes products_cleaned.csv is in the /import directory of the container
        cypher_query = """
        LOAD CSV WITH HEADERS FROM 'file:///products_cleaned.csv' AS row
        MERGE (p:Product {id: row.id})
        SET p.name = row.productDisplayName,
            p.price = toInteger(row.id) % 500 + 50

        MERGE (b:Brand {name: row.brand})
        MERGE (c:Color {name: row.baseColour})
        MERGE (u:Usage {type: row.usage})
        MERGE (s:Silhouette {type: row.articleType})

        MERGE (p)-[:MANUFACTURED_BY]->(b)
        MERGE (p)-[:HAS_COLOR]->(c)
        MERGE (p)-[:SUITABLE_FOR]->(u)
        MERGE (p)-[:IS_STYLE]->(s)
        """
        with self.driver.session() as session:
            print("Ingesting data into the Style Graph... (this may take a minute)")
            result = session.run(cypher_query)
            summary = result.consume()
            print(f"Ingestion complete. Created {summary.counters.nodes_created} nodes and {summary.counters.relationships_created} relationships.")

if __name__ == "__main__":
    # Connect to the Docker container
    # 'bolt://localhost:7687' is the standard protocol for Neo4j drivers
    db = KickScoutDB()
    
    try:
        db.setup_schema()
        db.load_data()
    finally:
        db.close()