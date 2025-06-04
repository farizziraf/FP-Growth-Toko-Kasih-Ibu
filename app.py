import subprocess
import sys
import os
from flask import Flask, request, flash, redirect, url_for
from controllers.index_controller import index, handle_upload_auto
from controllers.association_controller import association
from controllers.output_controller import output
from controllers.recommendation_controller import recommendation

# Install dependencies secara otomatis
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

app = Flask(__name__)
app.secret_key = 'skripsi_fariz'

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def route_index():
    if request.method == 'POST':
        return handle_upload_auto(request, app)
    else:
        return index()

@app.route('/association', methods=['GET', 'POST'])
def route_association():
    from controllers.association_controller import handle_association
    return handle_association(request)

@app.route('/output')
def route_output():
    return output()

@app.route('/recommendation')
def route_recommendation():
    return recommendation()

if __name__ == '__main__':
    app.run(debug=True)
