from flask import Flask, redirect, request, send_file, render_template
import os
import traceback
from google.cloud import storage
import io
import google.generativeai as genai
import json
import base64

app = Flask(__name__)

api_key = os.environ.get('GEMINI_API_KEY')



genai.configure(api_key=api_key)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

def upload_to_gemini(image_bytes, mime_type=None):
    """Uploads the image content to Gemini API and returns the response with a title and description."""
    try:
        chat_session = model.start_chat()

        encoded_image = base64.b64encode(image_bytes).decode('utf-8')

        message = {
            "parts": [
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": encoded_image
                    }
                },
                {
                    "text": "Please provide a title and description for the image."
                }
            ]
        }

        response = chat_session.send_message(message)

        print("Response from Gemini API:", response.text)
        return response.text

    except Exception as e:
        print(f"Error uploading to Gemini: {e}")
        return None

def parse_gemini_response(response_text):
    """Parses the plain text response from Gemini API to extract title and description."""
    try:
        lines = response_text.split("\n")
        title = ""
        description = ""

        for line in lines:
            if line.startswith("**Title:**"):
                title = line.replace("**Title:**", "").strip()
            elif line.startswith("**Description:**"):
                description = line.replace("**Description:**", "").strip()

        if not title:
            title = "Unknown Title"
        if not description:
            description = "No description available."

        return title, description
    except Exception as e:
        print(f"Error while parsing response: {e}")
        return "Unknown Title", "No description available."

def save_text_to_bucket(bucket, text, filename):
    """Saves the caption and description as a .txt file in the bucket."""
    try:
        blob = bucket.blob(filename)
        blob.upload_from_string(text, content_type='text/plain')
        print(f"Text file '{filename}' saved to bucket '{bucket_name}'")
    except Exception as e:
        print(f"Error uploading text file to bucket: {e}")

def retrieve_text_from_bucket(text_file):
    """Retrieve the title and description from the .txt file in the bucket."""
    try:
        blob = bucket.blob(text_file)
        text_content = blob.download_as_text()
        lines = text_content.splitlines()
        title = lines[0].replace("Title: ", "") if lines else "Unknown Title"
        description = lines[1].replace("Description: ", "") if len(lines) > 1 else "No description available."
        return title, description
    except Exception as e:
        print(f"Error retrieving text from bucket: {e}")
        return "Unknown Title", "No description available."

client = storage.Client()
bucket_name = 'cndbucket-2'
bucket = client.bucket(bucket_name)

@app.route('/')
def index():
    """Display the home page with file upload and management functionality."""
    index_html = """
    <!doctype html>
    <html>
    <head>
        <title>File Upload</title>
        <style>
            body {
                background-color: blue;
                color: white; 
                font-family: Arial, sans-serif;
            }
            h1, h2 {
                text-align: center;
            }
            form {
                margin: 20px;
                text-align: center;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                margin: 10px 0;
                text-align: center;
            }
            img {
                border: 2px solid white; 
            }
            button {
                background-color: red;
                color: white;
                border: none;
                padding: 5px 10px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>Upload and View Images</h1>
        <form method="post" enctype="multipart/form-data" action="/upload">
            <div>
                <label for="file">Choose file to upload</label>
                <input type="file" id="file" name="form_file" accept="image/jpeg,image/jpg" />
            </div>
            <div>
                <button type="submit">Submit</button>
            </div>
        </form>
        <h2>Uploaded Files</h2>
        <ul>
    """
    for file in list_files():
        if file.lower().endswith(('.jpg', '.jpeg')):
            # Retrieve title and description
            text_file = f"{os.path.splitext(file)[0]}.txt"
            title, description = retrieve_text_from_bucket(text_file)
            index_html += f"""
            <li>
                <a href="/files/{file}" style="color: white;">{file}</a><br>
                <img src="/image/{file}" width="200" height="auto"><br>
                <strong>Title:</strong> {title}<br>
                <strong>Description:</strong> {description}<br>
                <form method="post" action="/delete/{file}" style="display:inline;">
                    <button type="submit">Delete</button>
                </form>
            </li>
            """
    index_html += """
        </ul>
    </body>
    </html>
    """
    return index_html

@app.route("/upload", methods=['POST'])
def upload():
    """Handle image upload and process it using Gemini API."""
    try:
        file = request.files.get('form_file')
        if file:
            blob = bucket.blob(file.filename)
            blob.upload_from_file(file, content_type=file.content_type)
            print(f"File uploaded to {bucket_name} as {file.filename}")

            file.seek(0)
            image_bytes = file.read()

            response_text = upload_to_gemini(image_bytes, mime_type=file.content_type)
            if response_text:
                title, description = parse_gemini_response(response_text)

                text_filename = f"{os.path.splitext(file.filename)[0]}.txt"
                save_text_to_bucket(bucket, f"Title: {title}\nDescription: {description}", text_filename)

        else:
            print("No file uploaded")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

    return redirect('/')

@app.route('/files')
def list_files():
    """List all uploaded image files."""
    blobs = client.list_blobs(bucket_name)
    files = [blob.name for blob in blobs if blob.name.lower().endswith(('.jpg', '.jpeg'))]
    return files

@app.route('/files/<filename>')
def get_file(filename):
    """Serve the file."""
    blob = bucket.blob(filename)
    file_data = blob.download_as_bytes()

    file_html = f"""
    <!doctype html>
    <html>
    <head>
        <title>{filename}</title>
        <style>
            body {{
                background-color: blue;
                color: white;
                font-family: Arial, sans-serif;
            }}
            h2 {{
                text-align: center;
            }}
            a {{
                color: white;
                text-decoration: none;
            }}
            img {{
                display: block;
                margin: 0 auto;
                border: 2px solid white;
            }}
        </style>
    </head>
    <body>
        <h2>{filename}</h2>
        <img src="/image/{filename}" width="500" height="auto">
        <br><a href="/">Back</a>
    </body>
    </html>
    """
    return file_html

@app.route('/image/<filename>')
def get_image(filename):
    """Serve the image file."""
    blob = bucket.blob(filename)
    file_data = blob.download_as_bytes()
    return send_file(io.BytesIO(file_data), mimetype='image/jpeg')

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    """Delete the image and its associated .txt file."""
    try:
        blob = bucket.blob(filename)
        blob.delete()
        print(f"Deleted {filename} from bucket {bucket_name}")
        
        # Delete associated text file
        text_file = f"{os.path.splitext(filename)[0]}.txt"
        text_blob = bucket.blob(text_file)
        text_blob.delete()
        print(f"Deleted {text_file} from bucket {bucket_name}")
    except Exception as e:
        print(f"Error deleting file: {e}")
    
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
