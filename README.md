# KickScout: Visual Similarity Graph API

KickScout is a machine learning-powered backend application that allows users to find visually similar footwear. Instead of relying purely on text metadata, KickScout uses a Contrastive Language-Image Pre-training (CLIP) model to map images into a 512-dimensional latent space. These vectors are stored and queried using a Neo4j graph database utilizing HNSW vector indexing.

## Architecture & Tech Stack

* **API Framework:** FastAPI, Uvicorn
* **Database:** Neo4j (Dockerized)
* **Machine Learning:** PyTorch, SentenceTransformers (CLIP-ViT-B-32)
* **Data Processing:** Pandas, KaggleHub
* **Hardware Acceleration:** Native support for Apple Metal Performance Shaders (MPS)

## Prerequisites

* Python 3.14
* Docker and Docker Compose
* Git

## Local Development Setup

### 1. Environment Configuration
Clone the repository and set up your local environment file.

```bash
git clone https://github.com/shubh-1912/project-kickscout
cd project-kickscout
```

Create a `.env` file in the root directory with the following database credentials:

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

### 2. Infrastructure & Data Pipeline
Run the automated setup script. This script handles the creation of the isolated virtual environment, installs dependencies, spins up the Neo4j database via Docker, downloads the Kaggle dataset, and executes the AI embedding generation.

```bash
chmod +x env_setup.sh
./env_setup.sh
```

Note: The embedding generation automatically engages the macOS MPS GPU for hardware acceleration.

## Running the API

Once the setup script finishes and the vector index is created, start the FastAPI server natively to utilize local hardware acceleration for real-time inference.

```bash
source venv/bin/activate
python3 -m uvicorn main:app --reload
```

The server will be available at `http://localhost:8000`.

## API Documentation & Usage

FastAPI automatically generates interactive API documentation. Navigate to `http://localhost:8000/docs` in your browser.

### Primary Endpoint: `POST /api/search/image`
Accepts a multipart form data image upload and returns the top 5 visually similar products from the database.

**Request:**
* Content-Type: `multipart/form-data`
* Body: `image` (File)

**Response:**
```json
{
  "message": "Vibe match successful",
  "results": [
    {
      "id": "1591",
      "name": "Canvas Sneaker",
      "price": 120,
      "score": 0.942
    }
  ]
}
```

## Data Source
The dataset utilized for this project is the Fashion Product Images dataset, retrieved via the Kaggle API. Data integrity is maintained via a Python validation layer prior to database ingestion.