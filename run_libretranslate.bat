@echo off
echo === Starting LibreTranslate Server ===
echo (Using virtual environment)

call libretranslate-env\Scripts\activate
echo Virtual environment activated.

echo Starting LibreTranslate server on port 5001...
libretranslate --port 5001 --host 127.0.0.1

echo Deactivating virtual environment...
deactivate
pause