from flask import Flask, redirect, request, send_file, render_template
import os
import traceback

from PIL import Image, ExifTags
from PIL.ExifTags import TAGS

app=Flask(__name__)
if not os.path.exists("files"):
    os.makedirs("files")
@app.route('/')
def index():
    print("GET /")

    index_html = """
    <!doctype html>
    <html>
    <head>
        <title>File Upload</title>
    </head>

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
        # Ensure image files are correctly recognized
        if file.lower().endswith(('.jpg', '.jpeg')):
            index_html += f"""
            <li>
                <a href="/files/{file}">{file}</a><br>
                <img src="/files/{file}" width="200" height="auto"">
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
    try:
        print("POST /upload")
        file = request.files.get('form_file')
        if file:
            file_path = os.path.join("files", os.path.basename(file.filename))
            file.save(file_path)
            print(f"File saved to {file_path}")
        else:
            print("No file uploaded")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

    return redirect('/')

@app.route('/files')
def list_files():
    print("GET /files")

    files = os.listdir("./files")
    jpegs = [file for file in files if file.endswith(".jpeg") or file.endswith(".jpg")]

    print(jpegs)
    return jpegs



@app.route('/files/<filename>')
def get_file(filename):
     print("GET /files/"+filename)
     
     
    # Initialize an empty HTML string
     image_html = "<h2>" +filename+ "</h2>"

    # Insert the image tag
     image_html += '<img src="/image/' + filename + '" width="500" height="333">'

    # Open the image and retrieve its EXIF metadata
     image = Image.open(os.path.join("./files", filename))
     exifdata = image._getexif()
     # extract other basic metadata
     info_dict = {
    "Filename": image.filename,
      "Image Size": image.size,
      "Image Height": image.height,
      "Image Width": image.width,
      "Image Format": image.format,
      "Image Mode": image.mode,
      "Image is Animated": getattr(image, "is_animated", False),
      "Frames in Image": getattr(image, "n_frames", 1)
}
     image_html += '<table border="1" width="500">'

     for label,value in info_dict.items():
      image_html += '<tr><td>' + label + '</td><td>' + str(value) + '</td></tr>'
      print(f"{label:25}: {value}")
    # Create an HTML table

    # Iterate through EXIF tags and display them in the table
     if exifdata is not None:
      for tagid, value in exifdata.items():
        tagname = ExifTags.TAGS.get(tagid, tagid)
        image_html += '<tr><td>' + tagname + '</td><td>' + str(value) + '</td></tr>'
      else:
       image_html += '<tr><td>EXIF data not available</td></tr>'

    # Close the table
     image_html += "</table>"

    # Add a "Back" link to return to the root
     image_html += '<br><a href="/">Back</a>'

    # Return the generated HTML
     return image_html


@app.route('/image/<filename>')
def get_image(filename):
     print('GET /image/'+filename)

     return send_file(os.path.join("./files",filename))



@app.route('/signin')
def signin():
    return render_template('signin.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/reset_password')
def reset_password():
    return render_template('reset_password.html')
    
if __name__ == "__main__":
    print("Starting Flask application...")
    app.run(debug=True)
