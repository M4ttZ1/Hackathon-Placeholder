import pandas as pd
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import TruncatedSVD # <-- NEW IMPORT
import joblib
import json

print("Starting HYBRID model training (Classifier + Faiss Index)...")

# --- 1. Load the pre-processed corpus ---
CORPUS_FILE = 'corpus.json'
try:
    df = pd.read_json(CORPUS_FILE)
    df.dropna(subset=['text', 'label'], inplace=True)
    print(f"Corpus loaded successfully. Found {len(df)} entries.")
except FileNotFoundError:
    print(f"\nFATAL ERROR: {CORPUS_FILE} not found! Run createcorpus.py first.\n")
    exit()

# --- 2. Train the Classifier (Logistic Regression) ---
print("\n--- Training Classifier ---")
df_classifier = df.copy()
df_classifier['label_numeric'] = df_classifier['label'].map({'phishing': 1, 'benign': 0})
X = df_classifier['text']
y = df_classifier['label_numeric'].astype(int)

vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
X_tfidf = vectorizer.fit_transform(X)
model = LogisticRegression(max_iter=1000)
model.fit(X_tfidf, y)
joblib.dump(vectorizer, 'vectorizer.joblib')
joblib.dump(model, 'model.joblib')
print("✅ Classifier and vectorizer saved.")

# --- 3. Build the Faiss Index with Dimensionality Reduction ---
print("\n--- Building Faiss Index ---")
# Vectorize the entire corpus for Faiss (using the same fitted vectorizer)
corpus_vectors_sparse = vectorizer.transform(df['text'])

# --- NEW: Dimensionality Reduction Step ---
# We will reduce the 10,000 features down to a dense 300-dimensional space.
# This is the key to solving the memory error.
N_COMPONENTS = 300
print(f"Reducing {corpus_vectors_sparse.shape[1]} sparse features to {N_COMPONENTS} dense components...")
svd = TruncatedSVD(n_components=N_COMPONENTS, random_state=42)
corpus_vectors_dense = svd.fit_transform(corpus_vectors_sparse).astype('float32')
print("Dimensionality reduction complete.")

# We must also save this SVD transformer to use in our API later
joblib.dump(svd, 'svd_transformer.joblib')
print("✅ SVD transformer saved.")

# L2 normalize the dense vectors for cosine similarity search
faiss.normalize_L2(corpus_vectors_dense)

# Create and save the Faiss index
index = faiss.IndexFlatL2(N_COMPONENTS) # The dimension is now N_COMPONENTS
index.add(corpus_vectors_dense)
faiss.write_index(index, 'faiss_index.bin')
print(f"Faiss index created with {index.ntotal} vectors.")

# Save the original texts and labels for lookup
corpus_lookup_data = df[['text', 'label']].to_dict('records')
with open('corpus_texts.json', 'w', encoding='utf-8') as f:
    json.dump(corpus_lookup_data, f)
print("✅ Faiss index and corpus lookup file saved.")
print("\nTraining complete. You can now run your FastAPI server.")
