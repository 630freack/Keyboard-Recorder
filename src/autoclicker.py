import tkinter as tk
import threading
import time
import keyboard as kb
import ctypes
from pynput import keyboard
from pynput.keyboard import Listener
import sys
import os
import json
import ctypes
import subprocess
import platform

# Отключаем fail-safe механизм pyautogui
# Fail-safe disabled

# Глобальные переменные
is_recording = False
is_playing = False
recorded_events = []
start_time = None
listener = None
play_thread = None
root = None


def record_key(event):
    """Запись нажатия клавиши"""
    global recorded_events, start_time
    
    if is_recording:
        current_time = time.time()
        
        # Сохраняем событие
        event_data = {
            'type': 'key',
            'key': str(event),
            'time': current_time - start_time,
            'action': 'press'
        }
        recorded_events.append(event_data)


def record_release(event):
    """Запись отпускания клавиши"""
    global recorded_events, start_time
    
    if is_recording:
        current_time = time.time()
        
        # Сохраняем событие
        event_data = {
            'type': 'key',
            'key': str(event),
            'time': current_time - start_time,
            'action': 'release'
        }
        recorded_events.append(event_data)


def start_recording():
    """Начать запись действий"""
    global is_recording, recorded_events, start_time, listener
    
    if not is_recording:
        is_recording = True
        recorded_events = []
        start_time = time.time()
        
        # Обновляем интерфейс
        status_label.config(text="Статус: Идет запись...", fg="red")
        record_button.config(text="Остановить запись")
        
        # Создаем и запускаем слушатель клавиатуры
        listener = Listener(
            on_press=record_key,
            on_release=record_release
        )
        listener.start()


def stop_recording():
    """Остановить запись действий"""
    global is_recording, listener
    
    if is_recording:
        is_recording = False
        
        # Останавливаем слушатель
        if listener:
            listener.stop()
            listener = None
        
        # Обновляем интерфейс
        status_label.config(text=f"Записано: {len(recorded_events)} событий", fg="green")
        record_button.config(text="Начать запись")


def toggle_record():
    """Переключение записи"""
    if is_recording:
        stop_recording()
    else:
        start_recording()


def play_recording():
    """Воспроизведение записи"""
    global is_playing, play_thread
    
    if not recorded_events:
        status_label.config(text="Ошибка: Нет записанных действий", fg="red")
        return
    
    if not is_playing:
        is_playing = True
        play_button.config(text="Остановить воспроизведение")
        status_label.config(text="Статус: Воспроизведение...", fg="blue")
        
        # Запускаем воспроизведение в отдельном потоке
        play_thread = threading.Thread(target=_play_loop, daemon=True)
        play_thread.start()


def _play_loop():
    """Цикл воспроизведения"""
    global is_playing
    
    while is_playing:
        _play_once()
        # Проверяем, не была ли остановлена воспроизведение во время выполнения
        if not is_playing:
            break
        # Небольшая пауза перед следующим циклом
        time.sleep(0.1)


def _play_once():
    """Воспроизведение записи один раз"""
    if not recorded_events:
        return
    
    # Получаем время начала воспроизведения
    start_play = time.time()
    
    # Воспроизводим каждое событие
    for event in recorded_events:
        if not is_playing:  # Проверяем, не остановили ли воспроизведение
            break
            
        # Ждем нужное количество времени
        current_time = time.time()
        wait_time = event['time'] - (current_time - start_play)
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        # Выполняем действие
        try:
            if event['action'] == 'press':
                # Конвертируем строковое представление клавиши в объект клавиши
                key = event['key'].replace("'", "").replace('Key.', '').replace('"', '')
                kb.press(key)
            elif event['action'] == 'release':
                key = event['key'].replace("'", "").replace('Key.', '').replace('"', '')
                kb.release(key)
        except Exception as e:
            print(f"Error playing event {event}: {e}")
            continue
    
    # Отпускаем все клавиши после завершения цикла
    kb.release('ctrl')
    kb.release('alt')
    kb.release('shift')
    kb.release('win')


def stop_playback():
    """Остановить воспроизведение"""
    global is_playing
    
    if is_playing:
        is_playing = False
        
        # Ждем завершения потока воспроизведения
        if play_thread:
            play_thread.join(timeout=1)
        
        # Отпускаем все клавиши
        kb.release('ctrl')
        kb.release('alt')
        kb.release('shift')
        kb.release('win')
        
        # Обновляем интерфейс
        play_button.config(text="Воспроизвести запись")
        status_label.config(text="Статус: Остановлено", fg="black")


def toggle_play():
    """Переключение воспроизведения"""
    if is_playing:
        stop_playback()
    else:
        play_recording()


def save_recording():
    """Сохранить запись в файл"""
    if not recorded_events:
        status_label.config(text="Ошибка: Нет записанных действий", fg="red")
        return
    
    try:
        with open("recording.json", "w", encoding="utf-8") as f:
            json.dump(recorded_events, f, indent=2, ensure_ascii=False)
        status_label.config(text="Запись сохранена в recording.json", fg="green")
    except Exception as e:
        status_label.config(text="Ошибка сохранения", fg="red")
        print(f"Error saving recording: {e}")


def load_recording():
    """Загрузить запись из файла"""
    global recorded_events
    
    try:
        if os.path.exists("recording.json"):
            with open("recording.json", "r", encoding="utf-8") as f:
                recorded_events = json.load(f)
            status_label.config(text=f"Загружено: {len(recorded_events)} событий", fg="green")
        else:
            status_label.config(text="Файл recording.json не найден", fg="red")
    except Exception as e:
        status_label.config(text="Ошибка загрузки", fg="red")
        print(f"Error loading recording: {e}")


def minimize_to_tray():
    """Сворачивание окна в системный трей"""
    global root
    root.withdraw()  # Скрываем главное окно


def show_from_tray():
    """Показ окна из системного трея"""
    global root
    root.deiconify()  # Показываем главное окно


def on_activate():
    """Обработчик активации по клавише Insert"""
    if root.winfo_viewable():
        minimize_to_tray()
    else:
        show_from_tray()


def for_canonical(f):
    """Вспомогательная функция для отслеживания клавиш"""
    return lambda k: f(k)


def setup_keyboard_listener():
    """Настройка слушателя клавиатуры"""
    global listener
    
    # Создаем слушатель клавиатуры для отслеживания Insert
    listener = keyboard.Listener(
        on_press=on_key_press,
        on_release=on_key_release
    )
    listener.start()


def on_key_press(key):
    """Обработчик нажатия клавиши"""
    try:
        if key == keyboard.Key.insert:
            on_activate()
    except AttributeError:
        pass


def on_key_release(key):
    """Обработчик отпускания клавиши"""
    pass


def on_closing():
    """Обработчик закрытия приложения"""
    global listener, is_playing
    
    # Останавливаем все процессы
    if listener:
        listener.stop()
    
    if is_playing:
        stop_playback()
    
    if is_recording:
        stop_recording()
    
    # Закрываем приложение
    root.destroy()
    sys.exit(0)


def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Запуск приложения от имени администратора"""
    if is_admin():
        status_label.config(text="Статус: Админ права есть", fg="green")
        return
    
    # Перезапуск приложения с правами администратора
    if sys.platform == "win32":
        try:
            # Получаем путь к текущему скрипту
            script = os.path.abspath(sys.argv[0])
            # Создаем команду для запуска от имени администратора
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script, None, 1)
            root.destroy()  # Закрываем текущий экземпляр
            sys.exit(0)  # Выходим из программы
        except Exception as e:
            status_label.config(text="Ошибка запуска от админа", fg="red")
            print(f"Error running as admin: {e}")


def create_gui():
    """Создание графического интерфейса"""
    global root, record_button, play_button, status_label

    root = tk.Tk()
    root.title("Keyboard Recorder")
    root.geometry("500x450")
    root.resizable(False, False)
    
    # Сделать окно всегда поверх других
    root.wm_attributes("-topmost", True)

    # Заголовок
    title_label = tk.Label(root, text="Keyboard Recorder", font=("Arial", 16, "bold"))
    title_label.pack(pady=10)

    # Описание
    desc_label = tk.Label(root, text="Записывайте и воспроизводите действия на клавиатуре", font=("Arial", 10))
    desc_label.pack(pady=5)

    # Статус
    status_label = tk.Label(root, text="Статус: Готов", fg="black", font=("Arial", 10))
    status_label.pack(pady=10)

    # Кнопка записи
    record_button = tk.Button(root, text="Начать запись", width=20, height=2, command=toggle_record)
    record_button.pack(pady=10)

    # Кнопка воспроизведения
    play_button = tk.Button(root, text="Воспроизвести запись", width=20, height=2, command=toggle_play)
    play_button.pack(pady=10)

    # Фрейм для кнопок сохранения/загрузки
    save_frame = tk.Frame(root)
    save_frame.pack(pady=10)

    save_button = tk.Button(save_frame, text="Сохранить", width=10, command=save_recording)
    save_button.pack(side=tk.LEFT, padx=5)

    load_button = tk.Button(save_frame, text="Загрузить", width=10, command=load_recording)
    load_button.pack(side=tk.LEFT, padx=5)

    # Кнопка запуска от имени администратора
    admin_button = tk.Button(root, text="Запустить от имени администратора", width=25, command=run_as_admin)
    admin_button.pack(pady=10)
    
    # Кнопка выхода
    exit_button = tk.Button(root, text="Выход", width=15, command=on_closing)
    exit_button.pack(pady=10)

    # Обработка закрытия окна
    root.protocol("WM_DELETE_WINDOW", minimize_to_tray)

    # Запуск GUI
    root.mainloop()


if __name__ == "__main__":
    # Настройка слушателя клавиатуры для сворачивания/разворачивания
    setup_keyboard_listener()

    # Создание GUI
    create_gui()

    # Очистка после закрытия
    if listener:
        listener.stop()
