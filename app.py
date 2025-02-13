from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import platform
from colorsys import rgb_to_hsv, hsv_to_rgb

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

# Caracteres ASCII mais densos para melhor definição
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
    # Converte para float32
    img_float = img.astype(np.float32) / 255.0
    
    # Aumenta o contraste
    img_float = np.clip((img_float - 0.5) * 1.5 + 0.5, 0, 1)
    
    # Aumenta a saturação
    hsv = cv2.cvtColor(img_float, cv2.COLOR_RGB2HSV)
    hsv[:, :, 1] = hsv[:, :, 1] * 1.5  # Aumenta saturação
    hsv[:, :, 2] = hsv[:, :, 2] * 1.2  # Aumenta valor (brilho)
    img_enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    return (np.clip(img_enhanced, 0, 1) * 255).astype(np.uint8)

def calculate_image_size(original_image, max_width=200):
    """Calcula o tamanho ideal mantendo a proporção."""
    height, width = original_image.shape[:2]
    aspect_ratio = height / width
    
    # Se a imagem for muito grande, redimensiona mantendo a proporção
    if width > max_width:
        new_width = max_width
        new_height = int(max_width * aspect_ratio)
    else:
        new_width = width
        new_height = height
        
    # Garante que a altura não fique muito grande
    max_height = 200
    if new_height > max_height:
        new_height = max_height
        new_width = int(max_height / aspect_ratio)
    
    return new_width, new_height

def image_to_ascii(image_path):
    # Carrega a imagem em cores
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Calcula o tamanho ideal
    target_width, target_height = calculate_image_size(image)
    
    # Redimensiona a imagem
    image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)
    
    # Melhora as cores
    image = enhance_colors(image)
    
    # Prepara as strings para arte ASCII e informações de cor
    ascii_str = ""
    color_data = []
    
    height, width = image.shape[:2]
    
    for i in range(height):
        line = ""
        line_colors = []
        for j in range(width):
            pixel = image[i, j]
            r, g, b = [int(x) for x in pixel]
            
            # Calcula o brilho usando uma fórmula mais precisa
            brightness = (0.299 * r + 0.587 * g + 0.114 * b)
            ascii_idx = int((brightness * (len(ascii_chars) - 1)) / 255)
            ascii_char = ascii_chars[ascii_idx]
            
            line += ascii_char
            line_colors.append((r, g, b))
        
        ascii_str += line + "\n"
        color_data.append(line_colors)
    
    return ascii_str, color_data

def ascii_to_image(ascii_art, color_data, output_path):
    lines = ascii_art.split("\n")
    line_length = max(len(line) for line in lines if line)
    
    # Configura a fonte com tamanho menor para maior resolução
    font_path = get_system_font()
    font_size = 8  # Tamanho menor da fonte para maior resolução
    
    try:
        font = ImageFont.truetype(font_path, size=font_size) if font_path else ImageFont.load_default()
        char_width, char_height = font.getbbox("A")[2:]
    except:
        font = ImageFont.load_default()
        char_width, char_height = 6, 8
    
    # Cria a imagem com fundo preto
    width = char_width * line_length
    height = char_height * len(color_data)
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)
    
    # Desenha os caracteres coloridos
    for y, (line, colors) in enumerate(zip(lines, color_data)):
        for x, (char, color) in enumerate(zip(line, colors)):
            # Posição precisa para cada caractere
            pos_x = x * char_width
            pos_y = y * char_height
            
            # Desenha o caractere com a cor correspondente
            draw.text(
                (pos_x, pos_y),
                char,
                fill=color,
                font=font
            )
    
    # Salva a imagem com alta qualidade
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
        ascii_art, color_data = image_to_ascii(file_path)
        
        # Cria a imagem ASCII colorida
        ascii_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'ascii_art_colored.png')
        ascii_to_image(ascii_art, color_data, ascii_image_path)
        
        return render_template('index.html', ascii_art=ascii_art, ascii_image='ascii_art_colored.png')

@app.route('/static/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)