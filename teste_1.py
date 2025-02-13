from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import csv
from datetime import datetime

def setup_driver():
    # Configurar opções do Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Executa em segundo plano
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Inicializar o driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_aoty_ratings(url, filter_rating=None):
    driver = setup_driver()
    albums_data = []
    
    try:
        print("Acessando a página...")
        driver.get(url)
        
        # Espera os elementos carregarem
        time.sleep(5)
        
        # Encontra todos os blocos de álbum
        album_blocks = driver.find_elements(By.CLASS_NAME, 'albumBlock')
        
        print(f"Encontrados {len(album_blocks)} álbuns. Processando...")
        
        for block in album_blocks:
            try:
                # Encontra os elementos dentro do bloco
                artist = block.find_element(By.CSS_SELECTOR, 'a[href*="/artist/"]').text.strip()
                album = block.find_element(By.CSS_SELECTOR, 'a[href*="/album/"]').text.strip()
                rating = block.find_element(By.CLASS_NAME, 'rating').text.strip()
                
                # Se um filtro de nota foi especificado, só adiciona se a nota corresponder
                if filter_rating is None or rating == str(filter_rating):
                    albums_data.append([artist, album, rating])
                    
            except Exception as e:
                print(f"Erro ao processar um álbum: {e}")
                continue
                
    except Exception as e:
        print(f"Erro durante o scraping: {e}")
    
    finally:
        driver.quit()
    
    return albums_data

def save_to_csv(albums_data, filter_rating=None):
    # Cria um nome de arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if filter_rating:
        filename = f'aoty_ratings_nota_{filter_rating}_{timestamp}.csv'
    else:
        filename = f'aoty_ratings_todos_{timestamp}.csv'
    
    try:
        # Salva os dados em CSV
        with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            # Escreve o cabeçalho
            writer.writerow(['Artista', 'Album', 'Nota'])
            # Escreve os dados
            writer.writerows(albums_data)
        
        print(f"\nArquivo CSV criado com sucesso: {filename}")
        print(f"Total de álbuns salvos: {len(albums_data)}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo CSV: {e}")

if __name__ == "__main__":
    url = "https://www.albumoftheyear.org/user/whocareeeees/ratings/"
    
    print("Iniciando o script...")
    
    # Coleta apenas álbuns com nota 100
    filter_rating = 100
    print(f"\nBuscando álbuns com nota {filter_rating}...")
    
    albums_data = scrape_aoty_ratings(url, filter_rating=filter_rating)
    
    if albums_data:
        print("\nDados coletados com sucesso!")
        print("\nPrimeiros álbuns encontrados:")
        # Mostra os primeiros 5 álbuns
        for i, (artist, album, rating) in enumerate(albums_data[:5]):
            print(f"{artist} - {album} ({rating})")
        
        # Salva em CSV
        save_to_csv(albums_data, filter_rating)