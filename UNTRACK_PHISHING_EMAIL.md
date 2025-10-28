# ⚠️ IMPORTANT: Untrack Phishing_Email.csv

## Problem

`backend/Phishing_Email.csv` is **already tracked in Git** from previous commits. 

Adding it to `.gitignore` only prevents NEW files from being tracked. It doesn't remove files already tracked.

---

## Solution

Run these commands to remove it from Git tracking (but keep the file locally):

```bash
# Remove from Git tracking but keep local file
git rm --cached backend/Phishing_Email.csv

# Now it's ignored (gitignore will take effect)
git status
# Should NOT show Phishing_Email.csv anymore

# Commit the removal
git commit -m "chore: Remove unused Phishing_Email.csv from tracking"
```

---

## ⚠️ WARNING

**Do NOT run `git rm` without `--cached`!**
- ❌ `git rm backend/Phishing_Email.csv` - DELETES the file!
- ✅ `git rm --cached backend/Phishing_Email.csv` - Keeps file, just untracks it

---

## Verification

After running the commands:

```bash
# Should NOT show up:
git ls-files | grep Phishing_Email
# (empty output = success)

# Should still exist locally:
ls backend/Phishing_Email.csv
# Should show the file
```

---

## Why Keep It Locally?

Even though we don't use it in `create_corpus.py`, you might want to keep it for reference or future use. That's why we use `--cached` to untrack it without deleting it.

---

**Status:** Ready to untrack  
**Run:** `git rm --cached backend/Phishing_Email.csv`

