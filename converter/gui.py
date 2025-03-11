import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from concurrent.futures import ThreadPoolExecutor
import webbrowser
import logging
from .converters import CONVERSION_FUNCTIONS
from .utils import setup_logging
from tkinterdnd2 import TkinterDnD, DND_FILES

class FileConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Универсальный Конвертер")
        self.root.geometry("500x500")
        self.output_dir = os.getcwd()
        setup_logging()
        self.create_widgets()
        self.setup_drag_and_drop()

    def create_widgets(self):
        select_button = tk.Button(self.root, text="Выбрать файлы", command=self.select_files)
        select_button.pack(pady=10)

        folder_button = tk.Button(self.root, text="Выбрать папку", command=self.select_folder)
        folder_button.pack(pady=5)

        tk.Label(self.root, text="Формат для изображений:").pack(pady=5)
        self.image_format_var = tk.StringVar(value='.png')
        image_format_menu = ttk.Combobox(self.root, textvariable=self.image_format_var,
                                         values=['.png', '.jpg', '.tiff'], state='readonly')
        image_format_menu.pack(pady=5)

        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Статус: Ожидание файлов", wraplength=450)
        self.status_label.pack(pady=10)

        open_folder_button = tk.Button(self.root, text="Открыть папку с файлами", command=self.open_output_folder)
        open_folder_button.pack(pady=10)

    def setup_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_files)

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.process_files(files)

    def select_files(self):
        filetypes = [('Поддерживаемые файлы', ' '.join(CONVERSION_FUNCTIONS.keys())),
                     ('Все файлы', '*.*')]
        files = filedialog.askopenfilenames(filetypes=filetypes)
        if files:
            self.process_files(files)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            files = [os.path.join(folder, f) for f in os.listdir(folder)
                     if os.path.splitext(f.lower())[1] in CONVERSION_FUNCTIONS]
            self.process_files(files)

    def process_files(self, files):
        if not files:
            return

        print("Начало обработки файлов:", files)
        self.progress['maximum'] = len(files)
        self.progress['value'] = 0
        self.status_label.config(text="Статус: Конвертация...")

        converted_files = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(self.convert_file, file): file for file in files}
            for future in future_to_file:
                try:
                    print(f"Обрабатываю файл: {future_to_file[future]}")
                    output_file = future.result()
                    converted_files.append(output_file)
                    print(f"Успешно сконвертирован: {output_file}")
                except Exception as e:
                    file = future_to_file[future]
                    logging.error(f"Ошибка при конвертации {file}: {str(e)}")
                    messagebox.showerror("Ошибка", f"Не удалось конвертировать {file}: {str(e)}")
                self.progress['value'] += 1
                self.root.update_idletasks()

        self.status_label.config(text=f"Сконвертировано файлов: {len(converted_files)}\n" +
                                      "\n".join(converted_files[:5]) +
                                      ("\n...и ещё файлы" if len(converted_files) > 5 else ""))
        messagebox.showinfo("Успех", f"Сконвертировано файлов: {len(converted_files)}")

    def convert_file(self, file_path):
        print(f"Конвертирую файл: {file_path}")
        ext = os.path.splitext(file_path.lower())[1]
        print(f"Расширение файла: {ext}")
        if ext not in CONVERSION_FUNCTIONS:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}")

        conversion_func = CONVERSION_FUNCTIONS[ext]
        print(f"Выбрана функция конвертации: {conversion_func.__name__}")
        if ext in {'.heic', '.tiff', '.bmp', '.webp', '.cr2', '.nef', '.arw'}:
            output_format = self.image_format_var.get()
            print(f"Конвертирую в формат: {output_format}")
            result = conversion_func(file_path, self.output_dir, output_format)
        else:
            print("Конвертирую видео в .mp4")
            result = conversion_func(file_path, self.output_dir)
        print(f"Результат конвертации: {result}")
        return result

    def open_output_folder(self):
        webbrowser.open(self.output_dir)