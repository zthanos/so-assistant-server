# Windows PowerShell
$env:DATABASE_URL="sqlite:///./so_assistant.db"
$env:MIGRATIONS_AUTO_APPROVE="1"   # προαιρετικό, για non-interactive
python migrate_database.py
