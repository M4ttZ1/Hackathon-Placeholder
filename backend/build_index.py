# backend/build_index.py
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

def build_faiss_index():
    print("Loading sentence transformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print("Loading corpus.json...")
    try:
        with open('corpus.json', 'r', encoding='utf-8') as f:
            corpus = json.load(f)
    except FileNotFoundError:
        print("--> ERROR: corpus.json not found. Please run create_corpus.py first.")
        return

    texts = [item['text'] for item in corpus]

    print(f"Generating embeddings for {len(texts)} entries... (This will take a few minutes)")
    embeddings = model.encode(texts, show_progress_bar=True)

    d = embeddings.shape[1]
    print(f"Creating FAISS index with dimension {d}...")
    index = faiss.IndexFlatL2(d)
    index.add(np.array(embeddings, dtype='float32'))

    print(f"Saving FAISS index to corpus.faiss...")
    faiss.write_index(index, 'corpus.faiss')

    print(f"Saving metadata to corpus_meta.json...")
    with open('corpus_meta.json', 'w', encoding='utf-8') as f:
        json.dump(corpus, f, indent=2)

    print(f"\n✅ Build complete! Index created with {index.ntotal} vectors.")

if __name__ == "__main__":
    build_faiss_index()