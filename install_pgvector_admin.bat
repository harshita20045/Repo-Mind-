@echo off
echo Installing pgvector into PostgreSQL 18...
copy /Y "%~dp0scratch\pgvector_files\lib\vector.dll" "C:\Program Files\PostgreSQL\18\lib\"
copy /Y "%~dp0scratch\pgvector_files\share\extension\*" "C:\Program Files\PostgreSQL\18\share\extension\"
echo pgvector installed successfully!
pause
