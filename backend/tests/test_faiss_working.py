#!/usr/bin/env python3
"""
Test FAISS is actually working with real corpus samples
"""
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

print("="*60)
print("FAISS + TRANSFORMERS VERIFICATION TEST")
print("="*60)

# Load everything
print("\n[1] Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("   Model loaded!")

print("\n[2] Loading FAISS index...")
index = faiss.read_index("corpus.faiss")
print(f"   Index loaded: {index.ntotal} vectors")

print("\n[3] Loading corpus metadata...")
with open("corpus_meta.json", 'r', encoding='utf-8') as f:
    corpus_meta = json.load(f)
print(f"   Metadata loaded: {len(corpus_meta)} entries")

# Test 1: Get a real phishing sample from corpus
print("\n" + "="*60)
print("TEST 1: Search with ACTUAL phishing from corpus")
print("="*60)

# Find a phishing sample
phishing_samples = [item for item in corpus_meta if item.get('label') == 'phishing'][:5]
if phishing_samples:
    sample = phishing_samples[0]
    print(f"\nOriginal phishing sample:")
    print(f"  Label: {sample['label']}")
    print(f"  Text: {sample['text'][:200]}...")
    
    # Search for it
    embedding = model.encode([sample['text']])
    distances, indices = index.search(np.array(embedding, dtype='float32'), k=5)
    
    print(f"\n  Top 5 matches:")
    for i in range(5):
        idx = indices[0][i]
        similarity = 1 / (1 + distances[0][i])
        match = corpus_meta[idx]
        print(f"    {i+1}. Similarity: {similarity:.3f} | Label: {match['label']} | Text: {match['text'][:80]}...")

# Test 2: Search with modified phishing text
print("\n" + "="*60)
print("TEST 2: Search with MODIFIED phishing text")
print("="*60)

test_texts = [
    "Urgent: Your PayPal account has been suspended. Click here to verify immediately.",
    "Your bank account needs verification. Click this link now or we will close it.",
    "Congratulations! You won $1000 gift card. Claim now by clicking here.",
    "ALERT: Unusual activity on your Microsoft account. Verify your identity now.",
]

for test_text in test_texts:
    print(f"\nTest: {test_text}")
    
    embedding = model.encode([test_text])
    distances, indices = index.search(np.array(embedding, dtype='float32'), k=3)
    
    print("  Top 3 matches:")
    for i in range(3):
        idx = indices[0][i]
        similarity = 1 / (1 + distances[0][i])
        match = corpus_meta[idx]
        if similarity > 0.65:  # Threshold used in main.py
            print(f"    [MATCH] {similarity:.3f} | {match['label']} | {match['text'][:60]}...")
        else:
            print(f"    [LOW] {similarity:.3f} (below 0.65 threshold) | {match['label']}")

# Test 3: Benign text (should have low similarity)
print("\n" + "="*60)
print("TEST 3: Benign text (should NOT match phishing)")
print("="*60)

benign_texts = [
    "Hey, how are you doing today? Want to grab coffee?",
    "The meeting is scheduled for 3pm tomorrow in conference room B.",
    "Thanks for your help with the project. I really appreciate it.",
]

for test_text in benign_texts:
    print(f"\nTest: {test_text}")
    
    embedding = model.encode([test_text])
    distances, indices = index.search(np.array(embedding, dtype='float32'), k=1)
    
    idx = indices[0][0]
    similarity = 1 / (1 + distances[0][0])
    match = corpus_meta[idx]
    
    if similarity > 0.65:
        print(f"  [WARN] UNEXPECTED: {similarity:.3f} | {match['label']} (should be low!)")
    else:
        print(f"  [GOOD] {similarity:.3f} | {match['label']} (correctly low)")

# Test 4: Check corpus distribution
print("\n" + "="*60)
print("TEST 4: Corpus statistics")
print("="*60)

labels = {}
for item in corpus_meta[:1000]:  # Sample first 1000
    label = item.get('label', 'unknown')
    labels[label] = labels.get(label, 0) + 1

print("\nLabel distribution (first 1000):")
for label, count in sorted(labels.items(), key=lambda x: x[1], reverse=True):
    print(f"  {label}: {count}")

print("\n" + "="*60)
print("[PASS] TEST COMPLETE")
print("="*60)
print("\nIf you see high similarity scores (>0.65) for phishing texts,")
print("FAISS is working correctly!")

