import os
import datetime
import PyRSS2Gen
import markdown
import re
from urllib.parse import quote

# Автоматически определяем данные Гитхаба
OUTPUT_DIR = os.getcwd() 
VAULT_PATH = os.path.dirname(OUTPUT_DIR)

# Пытаемся угадать твой логин и репозиторий для правильных ссылок
def get_base_url():
    # Мы знаем, что ты в папке Obsidian RSS
    repo_name = os.path.basename(OUTPUT_DIR).replace(' ', '-')
    # Здесь можно было бы вытащить логин, но мы сделаем универсальную ссылку
    return f"https://local-obsidian-sync.github.io/{repo_name}"

BASE_URL = get_base_url()

def translit(text):
    cyr = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя '
    lat = 'abvgdeezzijklmnoprstufhzcss_y_eua_'
    table = str.maketrans(cyr, lat)
    res = text.lower().translate(table)
    return re.sub(r'[^a-z0-9_]', '', res.replace(' ', '_'))

EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', 'rss', '_rss_output', '.git', 'attachments', 'Obsidian RSS'}

def clean_markdown(content):
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_feeds():
    print(f"--- Генерация RSS (Проверка ссылок) ---")
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
                                "date": date
                            })
                    except Exception: pass

        if not notes: continue
        notes.sort(key=lambda x: x['date'], reverse=True)
        
        rss_items = []
        for n in notes:
            # ВАЖНО: Ссылка теперь ведет на твой работающий index.html
            # Чтобы NotebookLM не видел 404
            item_link = f"{BASE_URL}/index.html?note={quote(n['title'])}"
            
            rss_items.append(PyRSS2Gen.RSSItem(
                title=n['title'],
                link=item_link,
                description=n['content'],
                guid=PyRSS2Gen.Guid(item_link),
                pubDate=n['date']
            ))

        rss = PyRSS2Gen.RSS2(
            title=f"Vault {folder}",
            link=BASE_URL,
            description=f"Notes from {folder}",
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
