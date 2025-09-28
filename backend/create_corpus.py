# backend/create_corpus.py
import csv
import json
import sys
import uuid
import os

# --- Dedicated, Corrected Parsing Functions for Each Dataset ---

csv.field_size_limit(500000)

def parse_enron_csv(filepath):
    """Parses the Enron.csv file using its specific format."""
    print(f"Processing: {os.path.basename(filepath)}")
    config = {
        'text_column': 'body',
        'label_column': 'label',
        'label_map': {'1': 'phishing', '0': 'benign'}
    }
    return _process_generic_csv(filepath, config)

def parse_phishing_legit_kd(filepath):
    """Parses the phishing_legit_dataset_KD_10000.csv file."""
    print(f"Processing: {os.path.basename(filepath)}")
    config = {
        'text_column': 'text',
        'label_column': 'label',
        'label_map': {'1': 'phishing', '0': 'benign'}
    }
    return _process_generic_csv(filepath, config)

def parse_spamassassin_csv(filepath):
    """Parses the SpamAssasin.csv file."""
    print(f"Processing: {os.path.basename(filepath)}")
    config = {
        'text_column': 'body',
        'label_column': 'label',
        'label_map': {'1': 'phishing', '0': 'benign'}
    }
    return _process_generic_csv(filepath, config)

def parse_uci_sms(filepath):
    """Processes the special tab-separated UCI SMS Spam Collection dataset."""
    print(f"Processing: {os.path.basename(filepath)}")
    entries = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                if len(row) == 2:
                    label_raw, text = row
                    label = 'phishing' if label_raw.lower() == 'spam' else 'benign'
                    entries.append({"id": str(uuid.uuid4()), "text": text.strip(), "label": label})
    except FileNotFoundError:
        print(f"  -> ERROR: File not found: {filepath}")
    return entries

# Helper function for standard CSV files
def _process_generic_csv(filepath, config):
    entries = []
    try:
        with open(filepath, 'r', encoding='latin-1', errors='ignore') as f: # Using latin-1 for broader compatibility
            reader = csv.DictReader(f)
            for row in reader:
                text = row.get(config['text_column'], '').strip()
                label_raw = row.get(config['label_column'], '').strip()
                label = config['label_map'].get(label_raw)
                if text and label:
                    entries.append({"id": str(uuid.uuid4()), "text": text, "label": label})
    except FileNotFoundError:
        print(f"  -> ERROR: File not found: {filepath}")
    except KeyError as e:
         print(f"  -> ERROR: A required column was not found in {os.path.basename(filepath)}. Missing column: {e}.")
    return entries

# --- Main Script Logic ---
if __name__ == "__main__":
    all_corpus_entries = []
    base_path = 'datasets'

    # Call each dedicated parsing function with the specified filenames
    print("Starting corpus creation...")
    all_corpus_entries.extend(parse_enron_csv(os.path.join(base_path, 'Enron.csv')))
    all_corpus_entries.extend(parse_phishing_legit_kd(os.path.join(base_path, 'phishing_legit_dataset_KD_10000.csv')))
    all_corpus_entries.extend(parse_spamassassin_csv(os.path.join(base_path, 'SpamAssasin.csv')))
    all_corpus_entries.extend(parse_uci_sms(os.path.join(base_path, 'SMSSpamCollection')))

    # --- Final Step ---
    print(f"\nTotal entries processed for corpus: {len(all_corpus_entries)}")
    output_path = 'corpus.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_corpus_entries, f, indent=2)

    print(f"✅ corpus.json created successfully with {len(all_corpus_entries)} entries.")