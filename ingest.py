import kagglehub
import pandas as pd
import os
import shutil

def setup_project_data():
    # 1. Download the latest version of the dataset
    print("Downloading dataset via kagglehub...")
    path = kagglehub.dataset_download("paramaggarwal/fashion-product-images-small")
    
    # 2. Identify file paths
    # Kagglehub downloads to a central cache; we'll point to it or move files
    csv_path = os.path.join(path, 'styles.csv')
    images_dir = os.path.join(path, 'images')
    
    print(f"Dataset downloaded to: {path}")

    # 3. Load and Clean Data
    df = pd.read_csv(csv_path, on_bad_lines='skip')

    critical_columns = ['usage', 'baseColour', 'articleType', 'productDisplayName']
    df = df.dropna(subset=critical_columns)
    
    # Feature Engineering: Extract Brand and sanitize names
    df['brand'] = df['productDisplayName'].str.split().str[0]
    df['id'] = df['id'].astype(str) # Ensure IDs are strings for path matching
    
    # Filter for items that actually have images in the downloaded folder
    available_images = set([f.split('.')[0] for f in os.listdir(images_dir)])
    df = df[df['id'].isin(available_images)]
    
    # 4. Export for Neo4j
    # We move the cleaned CSV to the Neo4j import folder
    os.makedirs('neo4j/import', exist_ok=True)
    target_csv = 'neo4j/import/products_cleaned.csv'
    df.to_csv(target_csv, index=False)
    
    print(f"Successfully processed {len(df)} products.")
    print(f"Cleaned CSV saved to: {target_csv}")

if __name__ == "__main__":
    setup_project_data()