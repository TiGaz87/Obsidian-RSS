import os
import datetime
import PyRSS2Gen
import markdown
import re

# ПУТЬ К ТВОЕМУ ХРАНИЛИЩУ (на уровень выше, так как мы в папке Obsidian RSS)
VAULT_PATH = os.path.dirname(os.getcwd())
# ПУТЬ, КУДА СОХРАНЯТЬ RSS (в папку _rss_output прямо здесь)
OUTPUT_DIR = os.path.join(os.getcwd(), "_rss_output")

# Папки, которые мы игнорируем
EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', '_rss_output', '.git', 'attachments', 'Obsidian RSS'}

def clean_markdown(content):
    # Убираем вики-ссылки [[link|text]] -> текст
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    # Убираем картинки
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_feeds():
    print(f"--- Генерация RSS для NotebookLM ---")
    print(f"[*] Базовая папка заметок: {VAULT_PATH}")
    print(f"[*] Куда сохраняем RSS: {OUTPUT_DIR}")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[+] Создана папка для фидов: {OUTPUT_DIR}")

    # Сканируем папки первого уровня в GazStorage
    try:
        items = os.listdir(VAULT_PATH)
    except Exception as e:
        print(f"[!] ОШИБКА: Не могу найти папку {VAULT_PATH}. Проверь букву диска!")
        return

    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]

    print(f"[*] Найдено категорий в Обсидиане: {len(top_folders)} ({', '.join(top_folders)})")

    for folder in top_folders:
        folder_path = os.path.join(VAULT_PATH, folder)
        notes = []
        
        for root, dirs, files in os.walk(folder_path):
            # Не заходим в системные папки
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(path)
                        date = datetime.datetime.fromtimestamp(mtime)
                        
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if content.strip():
                            clean_text = clean_markdown(content)
                            html_content = markdown.markdown(clean_text)
                            
                            notes.append({
                                "title": os.path.splitext(file)[0],
                                "content": html_content,
                                "date": date,
                                "path": path
                            })
                    except Exception as e:
                        print(f"    [!] Ошибка в файле {file}: {e}")

        if not notes:
            continue

        notes.sort(key=lambda x: x['date'], reverse=True)

        rss_items = []
        for note in notes:
            rss_items.append(PyRSS2Gen.RSSItem(
                title=note['title'],
                link=f"https://obsidian.local/{folder}/{note['title'].replace(' ', '_')}",
                description=note['content'],
                guid=PyRSS2Gen.Guid(note['path']),
                pubDate=note['date']
            ))

        rss = PyRSS2Gen.RSS2(
            title=f"Obsidian: {folder}",
            link="https://github.com/local-vault",
            description=f"Автоматический фид из {folder}",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items
        )

        output_path = os.path.join(OUTPUT_DIR, f"{folder}.xml")
        with open(output_path, "w", encoding='utf-8') as f:
            rss.write_xml(f, encoding='utf-8')
        
        print(f"    [OK] Создан: {folder}.xml (заметок: {len(notes)})")

if __name__ == "__main__":
    generate_feeds()
    print("\n[Готово] Проверь GitHub Desktop, там должны появиться новые файлы.")
