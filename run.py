import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Запускаем основной скрипт
if __name__ == "__main__":
    from src.autoclicker import create_gui, setup_keyboard_listener
    
    # Настройка слушателя клавиатуры для сворачивания/разворачивания
    setup_keyboard_listener()

    # Запуск GUI
    create_gui()