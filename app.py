import os
from flask import Flask, request
from controllers.index_controller import index, handle_upload_auto
from controllers.association_controller import handle_association
from controllers.output_controller import output
from controllers.recommendation_controller import recommendation

# Inisialisasi Flask app
app = Flask(__name__)
app.secret_key = 'skripsi_fariz'

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Buat folder upload jika belum ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Routing untuk halaman utama (upload file)
@app.route('/', methods=['GET', 'POST'])
def route_index():
    if request.method == 'POST':
        return handle_upload_auto(request, app)
    else:
        return index()

# Routing untuk halaman asosiasi
@app.route('/association', methods=['GET', 'POST'])
def route_association():
    return handle_association(request)

# Routing untuk halaman output
@app.route('/output')
def route_output():
    return output()

# Routing untuk halaman rekomendasi
@app.route('/recommendation')
def route_recommendation():
    return recommendation()

# Menjalankan aplikasi (hanya saat development)
if __name__ == '__main__':
    app.run(debug=True)
