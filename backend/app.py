from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import base64
import os
import tempfile
import mimetypes
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

genai.configure(api_key=GEMINI_API_KEY)


@app.route("/")
def home():
    return jsonify({"status": "ReviseX backend online"})


@app.route("/generate", methods=["POST"])
def generate():
    if "file" not in request.files:
        return jsonify({"error": "File missing"}), 400

    file = request.files["file"]
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Read file bytes
        file_bytes = file.read()
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type is None:
            # Default to application/octet-stream if type can't be determined
            if file.filename.lower().endswith('.pdf'):
                mime_type = 'application/pdf'
            elif file.filename.lower().endswith(('.jpg', '.jpeg')):
                mime_type = 'image/jpeg'
            elif file.filename.lower().endswith('.png'):
                mime_type = 'image/png'
            else:
                mime_type = 'application/octet-stream'
        
        print(f"Processing file: {file.filename} with MIME type: {mime_type}")
        
        # Encode to base64
        b64_file = base64.standard_b64encode(file_bytes).decode('utf-8')
        
        # Prepare Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = (
            "You will receive a document file (PDF or Image). "
            "Extract clean question-answer pairs from the content. "
            "Respond ONLY in the following JSON format:\n"
            "[{\"q\": \"question\", \"a\": \"answer\"}]\n"
            "If no content is found, respond with an empty array: []"
        )

        # Use inline data format
        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": mime_type,
                    "data": b64_file
                }
            ]
        )

        output = response.text
        print(f"Response received: {output[:100]}...")
        
        return jsonify({"results": output})

    except Exception as e:
        print(f"Error in generate: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
