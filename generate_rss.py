import os
import datetime
import markdown
import re

# Пути
OUTPUT_DIR = os.getcwd() 
VAULT_PATH = os.path.dirname(OUTPUT_DIR)

def translit(text):
    cyr = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    lat = 'abvgdeezzijklmnoprstufhzcss_y_eua_'
    table = str.maketrans(cyr, lat)
    res = text.lower().translate(table)
    return re.sub(r'[^a-z0-9_]', '', res.replace(' ', '_'))

EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', 'rss', '_rss_output', '.git', 'attachments', 'Obsidian RSS'}

def clean_markdown(content):
    # Убираем вики-ссылки [[link|text]] -> текст
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    # Убираем картинки
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_html_files():
    print(f"--- Генерация HTML для NotebookLM ---")
    items = os.listdir(VAULT_PATH)
    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]

    for folder in top_folders:
        folder_path = os.path.join(VAULT_PATH, folder)
        all_notes_html = ""
        count = 0
        
        # Собираем все заметки из папки в один HTML
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if content.strip():
                            title = os.path.splitext(file)[0]
                            clean_text = clean_markdown(content)
                            html_content = markdown.markdown(clean_text)
                            
                            # Каждая заметка - это отдельный блок <article>
                            all_notes_html += f"""
                            <article style="margin-bottom: 50px; border-bottom: 1px solid #ccc; padding-bottom: 20px;">
                                <h1 style="color: #2c3e50;">{title}</h1>
                                <div class="content">
                                    {html_content}
                                </div>
                            </article>
                            """
                            count += 1
                    except Exception: pass

        if count == 0: continue

        # Собираем финальный файл
        full_html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Obsidian: {folder}</title>
            <style>
                body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 40px auto; padding: 20px; color: #333; }}
                h1 {{ border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }}
                code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
                pre {{ background: #f4f4f4; padding: 15px; overflow-x: auto; border-radius: 5px; }}
                blockquote {{ border-left: 5px solid #ccc; margin: 0; padding-left: 20px; font-style: italic; }}
            </style>
        </head>
        <body>
            <header>
                <h1>Категория: {folder}</h1>
                <p>Всего заметок: {count} | Обновлено: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </header>
            <hr>
            {all_notes_html}
        </body>
        </html>
        """

        english_name = translit(folder)
        out_path = os.path.join(OUTPUT_DIR, f"{english_name}.html")
        with open(out_path, "w", encoding='utf-8') as f:
            f.write(full_html)
        print(f"    [OK] Создан: {english_name}.html")

if __name__ == "__main__":
    generate_html_files()
