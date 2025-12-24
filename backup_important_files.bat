@echo off
echo 备份重要文件...

mkdir backup_before_cleanup 2>nul

copy "Pervis PRO\backend\main.py" "backup_before_cleanup\main.py" 2>nul
copy "Pervis PRO\backend\database.py" "backup_before_cleanup\database.py" 2>nul
copy "Pervis PRO\backend\requirements.txt" "backup_before_cleanup\requirements.txt" 2>nul
copy "Pervis PRO\backend\.env" "backup_before_cleanup\.env" 2>nul
copy "Pervis PRO\frontend\package.json" "backup_before_cleanup\package.json" 2>nul
copy "Pervis PRO\launcher\main.py" "backup_before_cleanup\launcher_main.py" 2>nul

echo 重要文件已备份到 backup_before_cleanup 目录