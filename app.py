import os
import shutil
import zipfile
from flask import Flask, request, redirect, url_for, render_template, flash, send_file
import pandas as pd
import logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flashing messages

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def rename_files(directory, excel_file):
    # Set up logging
    logging.basicConfig(filename='rename_files.log', level=logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

    # Read the Excel file
    df = pd.read_excel(excel_file, header=None)

    # Loop over the rows in the DataFrame
    for _, row in df.iterrows():
        new_base_name = str(row[4])  # Convert to string
        count = 0

        for old_name in row[:4]:
            if pd.notna(old_name):
                count += 1
                new_name = f"{new_base_name}-{count}" if count > 1 else new_base_name
                old_path = os.path.join(directory, old_name + '.jpg')
                new_path = os.path.join(directory, new_name + '.jpg')
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed file {old_name}.jpg to {new_name}.jpg")
                else:
                    logging.warning(f"File {old_name}.jpg does not exist")

def zip_renamed_images(directory):
    zip_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'renamed_images.zip')
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, dirs, files in os.walk(directory):
            for file in files:
                zipf.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                           os.path.join(directory, '..')))
    return zip_filename

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'images' not in request.files or 'excel' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        image_files = request.files.getlist('images')
        excel_file = request.files['excel']
        
        if not image_files or not excel_file:
            flash('No selected file')
            return redirect(request.url)
        
        image_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'images')
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], 'mapping.xlsx')
        
        # Clear the upload directory
        if os.path.exists(image_folder):
            shutil.rmtree(image_folder)
        os.makedirs(image_folder, exist_ok=True)
        
        for file in image_files:
            file.save(os.path.join(image_folder, file.filename))
        
        excel_file.save(excel_path)
        
        rename_files(image_folder, excel_path)
        
        zip_path = zip_renamed_images(image_folder)
        
        flash('Files successfully renamed. Click the link below to download the renamed images.')
        return render_template('index.html', download_link=url_for('download_file', filename='renamed_images.zip'))
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
