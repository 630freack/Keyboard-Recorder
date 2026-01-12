@echo off
REM Автокликер для клавиши F
REM Запуск скрипта Python

cd /d "%~dp0"

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Ошибка: Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    echo Или добавьте Python в переменную среды PATH
    pause
    exit /b
)

REM Запуск скрипта
echo Запуск автокликера...
python run.py

echo Скрипт остановлен
pause