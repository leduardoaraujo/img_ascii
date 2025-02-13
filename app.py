from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

def image_to_ascii(image_path):
    # Escala de tons de cinza, do mais denso para o mais claro
    ascii_chars = "@%#*+=-:. "

    # Carrega a imagem em escala de cinza
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Ajusta o tamanho para uma melhor visualização
    image = cv2.resize(image, (100, 50))

    # Converte pixels para ASCII
    pixels = np.array(image)
    ascii_str = ""
    for row in pixels:
        line = "".join(ascii_chars[pixel // (256 // len(ascii_chars))] for pixel in row)
        ascii_str += line + "\n"

    return ascii_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        ascii_art = image_to_ascii(file_path)
        return render_template('index.html', ascii_art=ascii_art)

if __name__ == '__main__':
    app.run(debug=True)
