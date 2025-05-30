import os
from flask import render_template, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
import pandas as pd

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def delete_uploaded_file():
    filepath = session.get('uploaded_file', None)
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f'Error menghapus file: {e}')
    session.pop('uploaded_file', None)

def index():
    # Hapus file upload yang lama saat kembali atau refresh ke index
    delete_uploaded_file()
    return render_template('index.html')

def handle_upload_auto(request, app):
    if 'file_upload' not in request.files:
        flash('Tidak ada file yang dipilih')
        return redirect(url_for('route_index'))

    file = request.files['file_upload']

    if file.filename == '':
        flash('Tidak ada file yang dipilih')
        return redirect(url_for('route_index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Hapus semua file yang ada di folder uploads sebelum menyimpan file baru
        for existing_file in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, existing_file)
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f'Gagal menghapus file lama {file_path}: {e}')

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Simpan path file di session
        session['uploaded_file'] = filepath

        flash(f'File {filename} berhasil diupload dan disimpan.')
        return redirect(url_for('route_association'))
    else:
        flash('Format file tidak diizinkan, harus .xlsx atau .csv')
        return redirect(url_for('route_index'))