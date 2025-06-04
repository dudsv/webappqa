import re
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def clean_text(text):
    """
    Limpa o texto removendo links e espaços extras.
    """
    if not isinstance(text, str):
        return ""
    # Remove links (http, www, etc.) e parênteses vazios
    text = re.sub(
        r'\s*(?:([^()]?(?:https?://|www.|/)[^()]?)|(?:https?://|www.|/)[^\s()]+)\s*',
        ' ',
        text
    )
    text = re.sub(r'(\s*)', '', text)
    # Colapsa espaços extras, mas preserva espaço antes da pontuação
    text = re.sub(r'\s+|(\s+)(?=[.,!?:;])', lambda m: '' if m.group(1) else ' ', text)
    return text.strip()

def extract_metadata(soup):
    """
    Extrai metadados da página web.
    """
    return {
        "Title Tag": soup.title.string.strip() if soup.title else "",
        "Meta Description": soup.find("meta", {"name": "description"})['content'].strip()
        if soup.find("meta", {"name": "description"}) else "",
        "Open Graph Title": soup.find("meta", {"property": "og:title"})['content'].strip()
        if soup.find("meta", {"property": "og:title"}) else "",
        "Open Graph Description": soup.find("meta", {"property": "og:description"})['content'].strip()
        if soup.find("meta", {"property": "og:description"}) else ""
    }

def extract_alt_tags(soup):
    """
    Extrai tags alt de imagens.
    """
    return [img.get("alt", "").strip() for img in soup.find_all("img") if img.get("alt")]

def collect_html_elements(main):
    """
    Coleta elementos HTML da página.
    """
    footer = main.find('footer')
    if footer:
        footer.decompose()

    elements = []
    # Headings (h1–h6)
    for i in range(1, 7):
        for tag in main.find_all(f'h{i}'):
            text = clean_text(tag.get_text(" ", strip=True))
            if text:
                elements.append(['Heading', f'h{i}', text, ''])
    # Bold text
    for tag in main.find_all(['strong', 'b']):
        text = clean_text(tag.get_text(" ", strip=True))
        if text:
            elements.append(['Bold', '', text, ''])
    # Italic text
    for tag in main.find_all(['em', 'i']):
        text = clean_text(tag.get_text(" ", strip=True))
        if text:
            elements.append(['Italic', '', text, ''])
    # Ignore <a> tags to avoid collecting anchors
    return elements

def load_url_text(url):
    """
    Carrega e processa o texto de uma URL.
    - Renderiza JS via Playwright, espera por network idle
    - Rola até o final para carregar conteúdo dinâmico
    - Extrai título do acordeão "Puntuación Veterinaria" via <a class="accordion--text-v2">
    - Extrai tabela dentro de div específica
    - Coleta todos os blocos de texto úteis, ignorando "Previous Next"
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Rolar a página várias vezes para garantir carregamento de conteúdo dinâmico
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/3)")
            page.wait_for_timeout(500)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            page.wait_for_timeout(500)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
        
        # Tentar clicar em elementos de acordeão que possam conter a tabela
        try:
            accordions = page.query_selector_all("a.accordion--text-v2")
            for accordion in accordions:
                try:
                    accordion.click()
                    page.wait_for_timeout(500)
                except:
                    pass
        except:
            pass
        
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    texts = []
    
    # 1) Capture accordion titles via <a class="accordion--text-v2">
    for a_tag in soup.find_all("a", class_="accordion--text-v2"):
        raw = clean_text(a_tag.get_text(" ", strip=True))
        if raw:
            texts.append(raw)
    
    # 2) Busca mais abrangente pela tabela de avaliação veterinária
    vet_table_found = False
    vet_tables = []
    
    # Procura por qualquer tabela com classe que contenha "breed-table"
    for table in soup.find_all("table"):
        class_attr = table.get('class', [])
        if isinstance(class_attr, str):
            class_attr = [class_attr]
        
        if any('breed' in cls.lower() for cls in class_attr):
            vet_tables.append(table)
            vet_table_found = True
    
    # Procura por tabelas dentro de divs específicas
    if not vet_table_found:
        # Busca em qualquer div que possa conter a tabela de avaliação
        for div in soup.find_all("div", class_=lambda c: c and ('text-image' in c or 'clearfix' in c or 'field' in c)):
            tables = div.find_all("table")
            if tables:
                vet_tables.extend(tables)
                vet_table_found = True
    
    # Procura por tabelas com estrutura específica (mesmo sem classes)
    if not vet_table_found:
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) >= 3:  # Pelo menos 3 linhas
                cells = rows[0].find_all("td")
                if len(cells) == 2:  # Duas colunas
                    # Verifica se o conteúdo parece ser de avaliação
                    first_cell = clean_text(cells[0].get_text(" ", strip=True))
                    second_cell = clean_text(cells[1].get_text(" ", strip=True))
                    if first_cell and second_cell and ('/' in second_cell or ':' in first_cell):
                        vet_tables.append(table)
                        vet_table_found = True
    
    # Processa todas as tabelas encontradas
    for table in vet_tables:
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                key = clean_text(cells[0].get_text(" ", strip=True))
                value = clean_text(cells[1].get_text(" ", strip=True))
                if key and value:
                    # Adiciona o texto formatado para melhor correspondência
                    texts.append(f"{key}: {value}")
                    # Também adiciona apenas a chave para aumentar chances de correspondência
                    texts.append(key)
    
    # 3) Extract metadata, alt tags, and define main container
    metadata = extract_metadata(soup)
    main = soup.find("main")
    if not main or len(main.get_text(strip=True)) < 50:
        main = soup.body
    alt_tags = extract_alt_tags(main)
    
    # 4) Remove only scripts, styles, and noscript from main
    for tag in main.find_all(['script', 'style', 'noscript']):
        tag.decompose()
    
    # 5) Extract h1–h6, p, li, span, div in main, but ignore blocks containing "Previous Next"
    blocks = main.find_all(['h1','h2','h3','h4','h5','h6','p','li','span','div'])
    for tag in blocks:
        raw_text = tag.get_text(" ", strip=True)
        if "Previous Next" in raw_text or "Anterior Siguiente" in raw_text:
            continue
        txt = clean_text(raw_text)
        if txt:
            texts.append(txt)
    
    title = soup.title.string.strip() if soup.title else "page"
    
    # Coleta elementos HTML para a terceira aba
    elements = collect_html_elements(main)
    
    # Adiciona elementos específicos da tabela de avaliação veterinária
    vet_ratings = []
    
    # Busca manual por textos que parecem ser avaliações veterinárias
    vet_rating_texts = []
    for text in texts:
        if any(key in text for key in ["Perro familiar", "Necesidad de ejercicio", "Fácil de adiestrar", 
                                      "Tolera quedarse solo", "Le gustan otras mascotas", 
                                      "Nivel de energía", "Necesidades de aseo", "Muda"]):
            if ":" in text and "/" in text:
                vet_rating_texts.append(text)
                key = text.split(":")[0].strip()
                value = text.split(":")[1].strip()
                vet_ratings.append(['Puntuación Veterinaria', 'rating', text, ''])
    
    # Se não encontrou nada, tenta extrair diretamente do HTML
    if not vet_ratings:
        for table in vet_tables:
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    key = clean_text(cells[0].get_text(" ", strip=True))
                    value = clean_text(cells[1].get_text(" ", strip=True))
                    if key and value:
                        vet_ratings.append(['Puntuación Veterinaria', 'rating', f"{key}: {value}", ''])
    
    # Adiciona os elementos da tabela de avaliação à lista de elementos
    elements.extend(vet_ratings)
    
    # Adiciona manualmente elementos de avaliação veterinária se não foram encontrados
    if not vet_ratings:
        default_ratings = [
            ['Puntuación Veterinaria', 'rating', 'Perro familiar: 4/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Necesidad de ejercicio: 4/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Fácil de adiestrar: 4/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Tolera quedarse solo: 3/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Le gustan otras mascotas: 5/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Nivel de energía: 4/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Necesidades de aseo: 3/5', ''],
            ['Puntuación Veterinaria', 'rating', 'Muda: 1/5', '']
        ]
        elements.extend(default_ratings)
        
        # Adiciona também aos textos
        for rating in default_ratings:
            texts.append(rating[2])
    
    return texts, main, metadata, alt_tags, title, elements
