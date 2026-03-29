import os
import datetime
import markdown
import re
import pdfkit
import base64

# ПУТЬ К ПРОГРАММЕ
path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# ПУТИ ХРАНИЛИЩА
OUTPUT_DIR = os.getcwd() 
VAULT_PATH = os.path.dirname(OUTPUT_DIR)

# Исключаем системные папки
EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', '.git', 'Obsidian RSS'}

def translit(text):
    cyr = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    lat = 'abvgdeezzijklmnoprstufhzcss_y_eua_'
    table = str.maketrans(cyr, lat)
    res = text.lower().translate(table)
    return re.sub(r'[^a-z0-9_]', '', res.replace(' ', '_'))

def get_image_base64(img_name):
    """Находит картинку и превращает её в base64 код для вставки в HTML"""
    img_name = img_name.strip()
    for root, dirs, files in os.walk(VAULT_PATH):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        if img_name in files:
            img_path = os.path.join(root, img_name)
            try:
                with open(img_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    ext = os.path.splitext(img_name)[1].lower().replace('.', '')
                    if ext == 'jpg': ext = 'jpeg'
                    return f"data:image/{ext};base64,{encoded_string}"
            except Exception as e:
                print(f"      [!] Не удалось прочитать картинку {img_name}: {e}")
    return None

def process_content(content):
    # 1. СНАЧАЛА ОБРАБОТКА КАРТИНОК ![[image.png]]
    def replace_image(match):
        img_name = match.group(1).split('|')[0]
        base64_data = get_image_base64(img_name)
        if base64_data:
            return f'<div style="text-align:center;"><img src="{base64_data}" style="max-width: 90%; height: auto; margin: 20px 0;"></div>'
        return f'<p style="color:red; text-align:center;">[Картинка не найдена: {img_name}]</p>'

    content = re.sub(r'!\[\[(.*?)\]\]', replace_image, content)
    
    # 2. Стандартные Markdown картинки ![desc](path)
    def replace_std_image(match):
        img_path = match.group(2)
        img_name = os.path.basename(img_path)
        base64_data = get_image_base64(img_name)
        if base64_data:
            return f'<div style="text-align:center;"><img src="{base64_data}" style="max-width: 90%; height: auto;"></div>'
        return match.group(0)

    content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_std_image, content)

    # 3. ТОЛЬКО ПОТОМ Убираем вики-ссылки [[link|text]] -> текст
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    
    return content

def generate_pdf():
    print(f"--- Генерация PDF (Фикс порядка обработки) ---")
    
    if not os.path.exists(path_to_wkhtmltopdf):
        print(f"[!] ОШИБКА: wkhtmltopdf не найден: {path_to_wkhtmltopdf}")
        return

    items = os.listdir(VAULT_PATH)
    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]

    for folder in top_folders:
        folder_path = os.path.join(VAULT_PATH, folder)
        all_notes_html = ""
        count = 0
        
        print(f"[*] Категория: {folder}")
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            text = f.read()
                        if text.strip():
                            title = os.path.splitext(file)[0]
                            clean_text = process_content(text)
                            html_content = markdown.markdown(clean_text, extensions=['fenced_code', 'tables'])
                            
                            all_notes_html += f"""
                            <div class="note" style="page-break-after: always; margin-bottom: 40px;">
                                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">{title}</h2>
                                <div class="note-content">{html_content}</div>
                            </div>
                            """
                            count += 1
                    except Exception as e:
                        print(f"    [!] Ошибка в {file}: {e}")

        if count == 0: continue

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: "Arial", sans-serif; padding: 20px; font-size: 14px; }}
                pre {{ background: #f8f9fa; padding: 10px; border: 1px solid #eee; white-space: pre-wrap; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                img {{ display: block; margin-left: auto; margin-right: auto; }}
            </style>
        </head>
        <body>
            <h1 style="text-align:center; color: #7f8c8d;">{folder}</h1>
            <p style="text-align:center;">Всего заметок: {count} | Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}</p>
            <hr>
            {all_notes_html}
        </body>
        </html>
        """

        out_name = f"{translit(folder)}.pdf"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        
        try:
            pdfkit.from_string(full_html, out_path, configuration=config, options={'encoding': "UTF-8", 'quiet': ''})
            print(f"    [OK] Создан {out_name}")
        except Exception as e:
            print(f"    [!] Ошибка PDF {folder}: {e}")

if __name__ == "__main__":
    generate_pdf()
