from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import platform

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

ascii_chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

def get_system_font():
    """Get an appropriate system font based on the operating system."""
    system = platform.system()
    if system == "Windows":
        font_paths = [
            "C:\\Windows\\Fonts\\lucon.ttf",  # Lucida Console
            "C:\\Windows\\Fonts\\consola.ttf",  # Consolas
            "C:\\Windows\\Fonts\\cour.ttf",    # Courier New
        ]
    elif system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/Monaco.ttf",
            "/Library/Fonts/Courier New.ttf",
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            return font_path
    return None

def enhance_colors(img):
    """Aumenta a saturação e o brilho das cores."""
    img_float = img.astype(np.float32) / 255.0
    
    # Aumenta o contraste
    img_float = np.clip((img_float - 0.5) * 1.5 + 0.5, 0, 1)
    
    # Aumenta a saturação e brilho
    hsv = cv2.cvtColor(img_float, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = hsv[:, :, 1] * 1.5  # Saturação
    hsv[:, :, 2] = np.clip(hsv[:, :, 2] * 1.3, 0, 1)  # Valor/Brilho
    img_enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    return (np.clip(img_enhanced, 0, 1) * 255).astype(np.uint8)

def get_image_dimensions(image_path):
    """Obtém as dimensões originais da imagem."""
    with Image.open(image_path) as img:
        return img.size

def calculate_font_size(image_width, image_height, target_width=None):
    """Calcula o tamanho ideal da fonte baseado nas dimensões da imagem."""
    if target_width is None:
        target_width = image_width
    
    # Começamos com um tamanho de fonte pequeno
    font_size = 4
    
    # Encontra o maior tamanho de fonte que mantenha a proporção
    font_path = get_system_font()
    while True:
        try:
            font = ImageFont.truetype(font_path, size=font_size) if font_path else ImageFont.load_default()
            char_width, char_height = font.getbbox("W")[2:]
            
            chars_per_line = target_width // char_width
            lines = image_height // char_height
            
            # Se o próximo tamanho de fonte seria muito grande, use o atual
            if chars_per_line < 50 or lines < 50:
                font_size = max(4, font_size - 1)
                break
                
            font_size += 1
        except:
            font_size = max(4, font_size - 1)
            break
    
    return font_size

def image_to_ascii(image_path):
    # Obtém as dimensões originais
    orig_width, orig_height = get_image_dimensions(image_path)
    
    # Calcula o tamanho da fonte ideal
    font_size = calculate_font_size(orig_width, orig_height)
    
    # Carrega e processa a imagem
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Obtém as dimensões baseadas no tamanho da fonte
    font_path = get_system_font()
    try:
        font = ImageFont.truetype(font_path, size=font_size) if font_path else ImageFont.load_default()
        char_width, char_height = font.getbbox("W")[2:]
    except:
        font = ImageFont.load_default()
        char_width, char_height = 8, 16
    
    # Calcula o número de caracteres necessários
    num_cols = orig_width // char_width
    num_rows = orig_height // char_height
    
    # Redimensiona a imagem para corresponder exatamente ao grid de caracteres
    image = cv2.resize(image, (num_cols, num_rows), interpolation=cv2.INTER_LANCZOS4)
    
    # Melhora as cores
    image = enhance_colors(image)
    
    # Gera a arte ASCII
    ascii_str = ""
    color_data = []
    
    for i in range(num_rows):
        line = ""
        line_colors = []
        for j in range(num_cols):
            pixel = image[i, j]
            r, g, b = [int(x) for x in pixel]
            
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            ascii_idx = int((brightness * (len(ascii_chars) - 1)) / 255)
            ascii_char = ascii_chars[ascii_idx]
            
            line += ascii_char
            line_colors.append((r, g, b))
        
        ascii_str += line + "\n"
        color_data.append(line_colors)
    
    return ascii_str, color_data, font_size

def ascii_to_image(ascii_art, color_data, font_size, output_path):
    lines = ascii_art.split("\n")
    line_length = max(len(line) for line in lines if line)
    
    # Configura a fonte
    font_path = get_system_font()
    try:
        font = ImageFont.truetype(font_path, size=font_size) if font_path else ImageFont.load_default()
        char_width, char_height = font.getbbox("W")[2:]
    except:
        font = ImageFont.load_default()
        char_width, char_height = 8, 16
    
    # Cria a imagem
    width = char_width * line_length
    height = char_height * len(color_data)
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    
    # Desenha os caracteres
    for y, (line, colors) in enumerate(zip(lines, color_data)):
        for x, (char, color) in enumerate(zip(line, colors)):
            pos_x = x * char_width
            pos_y = y * char_height
            draw.text((pos_x, pos_y), char, fill=color, font=font)
    
    # Salva a imagem
    image.save(output_path, quality=95)

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
        
        # Converte para ASCII com cores
        ascii_art, color_data, font_size = image_to_ascii(file_path)
        
        # Cria a imagem ASCII colorida
        ascii_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ascii_art_colored.png')
        ascii_to_image(ascii_art, color_data, font_size, ascii_image_path)
        
        return render_template('index.html', ascii_art=ascii_art, ascii_image='ascii_art_colored.png')

@app.route('/static/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)