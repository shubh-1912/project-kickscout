#!/bin/bash
set -e

echo "🚀 Starting KickScout Professional Setup..."

# 1. Create the Virtual Environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment using Python 3.14..."
    # We use python3 here just to create the initial bubble
    python3 -m venv venv
fi

# 2. Define the internal paths
# Once the venv exists, these are the ONLY executables that matter
VENV_PYTHON="./venv/bin/python"
VENV_PIP="./venv/bin/pip"

# 3. Install Dependencies
echo "📦 Installing requirements into venv..."
$VENV_PIP install --upgrade pip
$VENV_PIP install -r requirements.txt

# 4. Start Infrastructure
echo "📦 Spinning up Neo4j via Docker..."
docker-compose up -d

# 5. Wait for Neo4j (using a simple python check for portability)
echo "⏳ Waiting for Neo4j to be ready..."
$VENV_PYTHON -c "
import socket
import time
while True:
    try:
        with socket.create_connection(('localhost', 7687), timeout=1):
            break
    except:
        time.sleep(1)
"
echo "✅ Neo4j is up!"

# 6. Execute the Data Pipeline
echo "📥 Ingesting Data..."
$VENV_PYTHON ingest.py

echo "🏗️  Setting up Database..."
$VENV_PYTHON setup_db.py

echo "🤖 Generating AI Embeddings..."
$VENV_PYTHON generate_embeddings.py

echo "✨ Setup Complete! Your environment is locked and loaded."