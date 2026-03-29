import os
import datetime
import PyRSS2Gen
import markdown
import re

# ПУТЬ К ТВОЕМУ ХРАНИЛИЩУ (на уровень выше)
VAULT_PATH = os.path.dirname(os.getcwd())
# ТЕПЕРЬ ПАПКА НАЗЫВАЕТСЯ ПРОСТО 'rss'
OUTPUT_DIR = os.path.join(os.getcwd(), "rss")

# Папки, которые мы игнорируем
EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', 'rss', '_rss_output', '.git', 'attachments', 'Obsidian RSS'}

def clean_markdown(content):
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_feeds():
    print(f"--- Генерация RSS для NotebookLM ---")
    print(f"[*] Базовая папка: {VAULT_PATH}")
    print(f"[*] Папка для RSS: {OUTPUT_DIR}")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        items = os.listdir(VAULT_PATH)
    except Exception as e:
        print(f"[!] ОШИБКА пути: {e}")
        return

    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]
    print(f"[*] Найдено категорий: {len(top_folders)}")

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
                    except Exception as e:
                        print(f"    [!] Ошибка в {file}: {e}")

        if not notes: continue
        notes.sort(key=lambda x: x['date'], reverse=True)
        rss_items = [PyRSS2Gen.RSSItem(
            title=n['title'],
            link=f"https://obsidian.local/{folder}/{n['title'].replace(' ', '_')}",
            description=n['content'],
            guid=PyRSS2Gen.Guid(n['path']),
            pubDate=n['date']
        ) for n in notes]

        rss = PyRSS2Gen.RSS2(
            title=f"Obsidian: {folder}",
            link="https://github.com/local-vault",
            description=f"Auto-feed from {folder}",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items
        )

        out_path = os.path.join(OUTPUT_DIR, f"{folder}.xml")
        with open(out_path, "w", encoding='utf-8') as f:
            rss.write_xml(f, encoding='utf-8')
        print(f"    [OK] Создан: {folder}.xml")

if __name__ == "__main__":
    generate_feeds()
    print("\n[Готово] Теперь нажми 'Commit' и 'Push' в GitHub Desktop.")
