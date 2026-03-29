import os
import datetime
import PyRSS2Gen
import markdown
import re

# Путь к твоему хранилищу (автоматически берем текущую папку)
VAULT_PATH = os.getcwd()
OUTPUT_DIR = os.path.join(VAULT_PATH, "_rss_output")
# Папки, которые мы игнорируем
EXCLUDED_DIRS = {'.obsidian', '.trash', 'Шаблоны', 'Chats', '.gemini', '_rss_output', '.git', 'attachments'}

def clean_markdown(content):
    # Убираем вики-ссылки [[link|text]] -> оставим только text
    content = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]*)\]\]', r'\1', content)
    # Убираем пути к картинкам ![...](...)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    return content

def generate_feeds():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[+] Создана папка для фидов: {OUTPUT_DIR}")

    # Сканируем папки первого уровня
    items = os.listdir(VAULT_PATH)
    top_folders = [d for d in items if os.path.isdir(os.path.join(VAULT_PATH, d)) and d not in EXCLUDED_DIRS]

    print(f"[*] Найдено категорий: {len(top_folders)}")

    for folder in top_folders:
        folder_path = os.path.join(VAULT_PATH, folder)
        notes = []
        
        # Собираем все .md файлы в этой папке и подпапках
        for root, dirs, files in os.walk(folder_path):
            # Пропускаем вложенные сервисные папки
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(path)
                        date = datetime.datetime.fromtimestamp(mtime)
                        
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        clean_text = clean_markdown(content)
                        # Конвертируем Markdown в HTML, чтобы NotebookLM лучше понимал структуру
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

        # Сортируем: самые свежие заметки будут в начале фида
        notes.sort(key=lambda x: x['date'], reverse=True)

        rss_items = []
        for note in notes:
            # Создаем элемент RSS
            rss_items.append(PyRSS2Gen.RSSItem(
                title=note['title'],
                # NotebookLM требует ссылку, сделаем её уникальной для каждой заметки
                link=f"https://obsidian.local/{folder}/{note['title'].replace(' ', '_')}",
                description=note['content'],
                guid=PyRSS2Gen.Guid(note['path']),
                pubDate=note['date']
            ))

        # Собираем весь фид
        rss = PyRSS2Gen.RSS2(
            title=f"Obsidian: {folder}",
            link="https://github.com/your-username/your-repo",
            description=f"Автоматический фид заметок из папки {folder}",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items
        )

        # Сохраняем файл
        output_filename = f"{folder}.xml"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        with open(output_path, "w", encoding='utf-8') as f:
            rss.write_xml(f, encoding='utf-8')
        
        print(f"    [OK] Создан: {output_filename} (заметок: {len(notes)})")

if __name__ == "__main__":
    print("--- Генерация RSS для NotebookLM ---")
    generate_feeds()
    print("\n[Готово] Теперь тебе нужно загрузить содержимое папки _rss_output на GitHub.")
