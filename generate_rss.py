import os
import datetime
import PyRSS2Gen
import markdown
import re
from urllib.parse import quote

# Сохраняем прямо в ту папку, где лежит скрипт (в корень репозитория)
OUTPUT_DIR = os.getcwd() 
# Базовая папка Обсидиана (на уровень выше)
VAULT_PATH = os.path.dirname(OUTPUT_DIR)

# Транслитерация для имен файлов
def translit(text):
    cyr = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    lat = 'abvgdeezzijklmnoprstufhzcss_y_eua_'
    table = str.maketrans(cyr, lat)
    # Убираем всё, кроме букв и цифр, меняем пробелы на подчеркивания
    res = text.lower().translate(table)
    return re.sub(r'[^a-z0-9_]', '', res.replace(' ', '_'))

EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', 'rss', '_rss_output', '.git', 'attachments', 'Obsidian RSS'}

def clean_markdown(content):
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_feeds():
    print(f"--- Генерация RSS (Корень репозитория) ---")
    
    items = os.listdir(VAULT_PATH)
    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]

    for folder in top_folders:
        folder_path = os.path.join(VAULT_PATH, folder)
        notes = []
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if content.strip():
                            mtime = os.path.getmtime(path)
                            date = datetime.datetime.fromtimestamp(mtime)
                            notes.append({
                                "title": os.path.splitext(file)[0],
                                "content": markdown.markdown(clean_markdown(content)),
                                "date": date,
                                "path": path
                            })
                    except Exception: pass

        if not notes: continue
        notes.sort(key=lambda x: x['date'], reverse=True)
        
        rss_items = []
        for n in notes:
            rss_items.append(PyRSS2Gen.RSSItem(
                title=n['title'],
                # Ссылка на сам репозиторий, чтобы NotebookLM не ругался на 404
                link=f"https://local-obsidian-note/{quote(n['title'])}",
                description=n['content'],
                guid=PyRSS2Gen.Guid(n['path']),
                pubDate=n['date']
            ))

        rss = PyRSS2Gen.RSS2(
            title=f"Obsidian: {folder}",
            link="https://github.com/",
            description=f"Auto-feed",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items
        )

        english_name = translit(folder)
        out_path = os.path.join(OUTPUT_DIR, f"{english_name}.xml")
        with open(out_path, "w", encoding='utf-8') as f:
            rss.write_xml(f, encoding='utf-8')
        print(f"    [OK] Создан: {english_name}.xml")

if __name__ == "__main__":
    generate_feeds()
