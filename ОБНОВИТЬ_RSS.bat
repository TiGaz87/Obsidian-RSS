@echo off
echo [*] Начинаю обновление RSS...
python generate_rss.py
echo.
echo [*] Готово! Теперь открой GitHub Desktop, нажми "Commit" и "Push".
echo [*] После этого нажми "Refresh" в NotebookLM.
pause
