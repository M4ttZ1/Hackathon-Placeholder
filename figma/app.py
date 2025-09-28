"""How the Code Works
Multiple Input Modes: The main /analyze function is a router. It first checks if a file was uploaded. If not, it assumes the request contains JSON and reads the inputType field ('text' or 'url') to decide which helper function to call.

File Uploads: The parse_eml function uses Python's standard email library to robustly parse .eml files. It extracts key headers and the plain text body, then passes the body to the text analysis function.

Phone Number Checks & Better Visuals: The prepare_visuals_from_text function is the core of the text analysis.

It uses a single, powerful regular expression to find URLs, emails, and phone numbers simultaneously.

Instead of just returning a list of findings, it breaks the entire text into a sequence of "tokens" (e.g., {"type": "plain", "content": "..."} or {"type": "url", "content": "..."}).

This tokenized structure is ideal for a frontend, which can simply loop through the list and render each token with the appropriate styling (e.g., plain text normally, URLs in red).

URL Analysis for Visuals: The analyze_url function shows how you can prepare data for a map. It gets the IP address of the domain and returns mock latitude/longitude data that a mapping library (like Leaflet or Mapbox) could use to drop a pin on a world map"""

import re
import email
import socket
from email import policy
from email.parser import BytesParser
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Initialize Flask App ---
app = Flask(__name__)
# CORS allows your web frontend to make requests to this backend
CORS(app)


# === 1. LOGIC FOR FILE UPLOADS (.eml Parsing) ===
def parse_eml(file_storage):
    """
    Parses an uploaded .eml file object and extracts its content.
    """
    try:
        # Read file content as bytes
        file_content = file_storage.read()
        msg = BytesParser(policy=policy.default).parsebytes(file_content)

        # Extract headers
        headers = {
            "subject": msg.get("subject", "N/A"),
            "from": msg.get("from", "N/A"),
            "to": msg.get("to", "N/A"),
            "date": msg.get("date", "N/A"),
        }

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                # Get the plain text part, ignore attachments
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            # Not a multipart message, just get the payload
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

        # Run text analysis on the extracted body for visuals
        visual_analysis = prepare_visuals_from_text(body)

        return {
            "status": "success",
            "type": "email_file",
            "headers": headers,
            "visual_body": visual_analysis,
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to parse .eml file: {str(e)}"}


# === 2. LOGIC FOR PHONE NUMBER & VISUALS ===
def prepare_visuals_from_text(text):
    """
    Analyzes text to find phone numbers, URLs, and emails,
    then structures the data for easy frontend highlighting.
    """
    # Regex for URLs, emails, and phone numbers
    # This pattern combines all three checks
    pattern = re.compile(
        r'((?:https?://|www\.)[^\s/$.?#].[^\s]*)'  # URLs
        r'|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'  # Emails
        r'|(\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b)'  # NA Phone Numbers
    )
    
    tokens = []
    last_end = 0
    found_items = {"urls": [], "emails": [], "phones": []}

    for match in pattern.finditer(text):
        start, end = match.span()
        # Add the plain text before the match
        if start > last_end:
            tokens.append({"type": "plain", "content": text[last_end:start]})
        
        # Determine the type of match and add it as a token
        url, email, phone = match.groups()
        if url:
            token_type = "url"
            content = url
            found_items["urls"].append(content)
        elif email:
            token_type = "email"
            content = email
            found_items["emails"].append(content)
        elif phone:
            token_type = "phone"
            content = phone
            found_items["phones"].append(content)
        
        tokens.append({"type": token_type, "content": content, "is_suspicious": True}) # Default to suspicious
        last_end = end
    
    # Add any remaining plain text after the last match
    if last_end < len(text):
        tokens.append({"type": "plain", "content": text[last_end:]})

    return {
        "summary": found_items,
        "segmented_text": tokens if tokens else [{"type": "plain", "content": text}] # Handle case with no matches
    }


# === 3. LOGIC FOR OTHER INPUT MODES (e.g., URL) ===
def analyze_url(url):
    """
    Performs basic analysis on a URL, like finding its IP and simulating geolocation.
    """
    try:
        # Remove common prefixes for domain extraction
        domain = re.sub(r'^https?://', '', url).split('/')[0]
        ip_address = socket.gethostbyname(domain)
        
        # In a real app, you would use a geolocation API (e.g., ip-api.com) with the IP
        # For this example, we'll return mock data
        geolocation = {"lat": 33.42, "lon": -111.94} # Mock location (Tempe, AZ)

        return {
            "status": "success",
            "type": "url_analysis",
            "url": url,
            "domain": domain,
            "ip_address": ip_address,
            "map_data": geolocation
        }

    except socket.gaierror:
        return {"status": "error", "message": f"Could not resolve domain: {domain}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# === 4. MAIN ROUTE TO HANDLE ALL INPUT MODES ===
@app.route('/analyze', methods=['POST'])
def analyze_router():
    """
    Main endpoint to route requests based on input type.
    """
    # --- A. Handle File Uploads (Multipart Form) ---
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400
        if file and file.filename.endswith('.eml'):
            result = parse_eml(file)
            return jsonify(result)
        else:
            return jsonify({"status": "error", "message": "Invalid file type. Please upload a .eml file."}), 400

    # --- B. Handle JSON-based Inputs (Text, URL) ---
    data = request.get_json()
    if not data or 'inputType' not in data:
        return jsonify({"status": "error", "message": "Missing 'inputType' in JSON payload"}), 400

    input_type = data['inputType']
    input_data = data.get('data', '')

    if input_type == 'text':
        result = prepare_visuals_from_text(input_data)
        return jsonify({
            "status": "success",
            "type": "text_analysis",
            "analysis": result,
        })
    
    elif input_type == 'url':
        result = analyze_url(input_data)
        return jsonify(result)

    else:
        return jsonify({"status": "error", "message": f"Unsupported inputType: '{input_type}'"}), 400


# --- Run the application ---
if __name__ == '__main__':
    # Runs on http://127.0.0.1:5000
    app.run(debug=True, port=5000)