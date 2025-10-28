# .gitignore Explanation

This document explains what files are ignored by Git and why.

## ✅ What's Tracked (in Git)

### Core Code
- ✅ `backend/*.py` - All Python modules (intel.py, scoring_engine.py, etc.)
- ✅ `backend/tests/` - All test files (important for CI/CD)
- ✅ `backend/run_all_tests.py` - Master test runner
- ✅ `backend/requirements.txt` - Python dependencies
- ✅ `backend/build_index.py` - Script to rebuild FAISS index

### Documentation
- ✅ `backend/ORGANIZATION_SUMMARY.md` - Project structure docs
- ✅ `backend/env.example` - Environment variable template (NO real keys)
- ✅ `README.md` - Project README

### Frontend
- ✅ `frontend/src/` - All React source code
- ✅ `frontend/package.json` - NPM dependencies
- ✅ `frontend/.gitignore` - Frontend-specific ignores

---

## 🚫 What's Ignored (NOT in Git)

### 🔐 Sensitive Information
```gitignore
.env                        # Contains ACTUAL API keys
.env.local                  # Local environment overrides
backend/docs/               # Contains API key examples & setup info
```

**Why:** These contain real API keys and sensitive configuration. Never commit these!

**What to do:** 
- Copy `backend/env.example` to `backend/.env`
- Fill in your actual API keys
- See `backend/docs/SETUP_API_KEYS.md` for instructions (local only)

---

### 📦 Large Data Files
```gitignore
backend/Phishing_Email.csv  # 52MB unused CSV (NOT in create_corpus.py)
backend/corpus.json         # ~200MB corpus file
backend/corpus_meta.json    # Large metadata
backend/corpus.faiss        # FAISS index binary
*.faiss                     # All FAISS index files
```

**Why:** These are huge files (100MB+) that would bloat the repository.

**Important:** The 4 datasets we ACTUALLY use are **tracked** (not ignored):
- ✅ `backend/datasets/Enron.csv`
- ✅ `backend/datasets/phishing_legit_dataset_KD_10000.csv`
- ✅ `backend/datasets/SpamAssasin.csv`
- ✅ `backend/datasets/SMSSpamCollection`

**How to rebuild FAISS:**
```bash
cd backend
python create_corpus.py  # Creates corpus.json from the 4 datasets
python build_index.py    # Creates corpus.faiss from corpus.json
```

---

### 💾 Cache Files
```gitignore
backend/intel_cache.json    # Cached VirusTotal/URLHaus responses
*_cache.json                # All test/API caches
```

**Why:** Caches are user-specific and constantly changing. Each developer should build their own cache.

**What happens:** Cache is created automatically on first API call.

---

### 📦 Dependencies
```gitignore
node_modules/               # JavaScript packages (~200MB)
.venv/                      # Python virtual environment
venv/
env/
```

**Why:** These are downloaded, not created by us. Recreate with:
```bash
# Python
pip install -r backend/requirements.txt

# JavaScript
cd frontend && npm install
```

---

### 🗑️ Generated Files
```gitignore
__pycache__/                # Python bytecode
*.pyc
dist/                       # Built frontend
.pytest_cache/              # Test cache
*.log                       # Log files
```

**Why:** These are auto-generated and differ per machine.

---

### 🛠️ IDE & OS Files
```gitignore
.vscode/                    # VS Code settings
.idea/                      # PyCharm settings
.DS_Store                   # macOS junk
Thumbs.db                   # Windows junk
```

**Why:** Developer preference files shouldn't be forced on others.

---

## 📋 Summary Table

| File/Folder | Tracked? | Why Ignored? | How to Get? |
|-------------|----------|--------------|-------------|
| `backend/docs/` | ❌ | Contains API keys in examples | Local documentation only |
| `backend/Phishing_Email.csv` | ❌ | 52MB unused file | Not needed |
| `backend/datasets/` | ✅ | **4 datasets ARE tracked!** | Already in Git |
| `backend/corpus.faiss` | ❌ | 100MB+ binary file | Run `python build_index.py` |
| `backend/corpus.json` | ❌ | 200MB+ corpus data | Run `python create_corpus.py` |
| `backend/intel_cache.json` | ❌ | API response cache | Auto-created on first use |
| `backend/.env` | ❌ | **Contains REAL API keys** | Copy from `env.example` |
| `backend/tests/` | ✅ | **Tests are important!** | Tracked in Git |
| `backend/intel.py` | ✅ | Core code | Tracked in Git |
| `node_modules/` | ❌ | 200MB+ dependencies | Run `npm install` |

---

## 🚨 Important Notes

### About `backend/tests/`
**Tests ARE tracked in Git** because:
- ✅ Important for collaboration
- ✅ Enable CI/CD pipelines
- ✅ Document expected behavior
- ✅ Catch regressions

**Never ignore test files!**

### About `backend/docs/`
**Docs ARE ignored** because:
- ❌ Contains API key examples (even fake ones can be security risks)
- ❌ Contains sensitive setup instructions
- ❌ May contain cached credentials

**Local documentation only!** Share setup info through README or wiki instead.

---

## 🔧 Setup for New Developers

1. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd OmniLensCopy
   ```

2. **Setup backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env and add your API keys
   python build_index.py  # Rebuild FAISS index
   ```

3. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   cp .env.example .env  # If exists
   # Edit .env if needed
   ```

4. **Run tests:**
   ```bash
   cd backend
   python run_all_tests.py
   ```

---

## 🤔 What If I Need a File That's Ignored?

### For `backend/docs/`:
Ask the project maintainer for local access, or check if there's a public wiki/README with the info.

### For `.env`:
Copy `env.example` and fill in your own API keys from:
- VirusTotal: https://www.virustotal.com/gui/my-apikey
- URLHaus: https://urlhaus.abuse.ch/api/#account

### For large data files:
Run the rebuild scripts:
```bash
python build_index.py     # Rebuilds FAISS
python create_corpus.py   # Rebuilds corpus
```

---

**Last Updated:** 2025-10-27

