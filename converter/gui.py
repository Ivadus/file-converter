import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from concurrent.futures import ThreadPoolExecutor
import logging
from .converters import CONVERSION_FUNCTIONS
from .utils import setup_logging, COLORS, apply_hover_effect, open_folder
from tkinterdnd2 import TkinterDnD, DND_FILES
import threading


class ModernButton(tk.Button):
    def __init__(self, master, is_secondary=False, **kwargs):
        super().__init__(master, **kwargs)
        bg_color = COLORS['button_bg'] if not is_secondary else COLORS['input_bg']
        hover_color = COLORS['button_hover'] if not is_secondary else COLORS['glass_bg']

        self.configure(
            background=bg_color,
            foreground=COLORS['text_primary'],
            activebackground=hover_color,
            activeforeground=COLORS['text_primary'],
            relief=tk.FLAT,
            borderwidth=0,
            padx=20,
            pady=8,
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        apply_hover_effect(self, hover_color)


class GlassFrame(tk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            background=COLORS['glass_bg'],
            padx=20,
            pady=20,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['border_active']
        )


class FileConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер файлов")
        self.root.geometry("900x700")
        self.root.configure(background=COLORS['bg_primary'])
        self.root.minsize(800, 600)

        self.setup_theme()
        self.output_dir = os.getcwd()
        self.selected_files = []
        setup_logging()
        self.processing = False
        self.create_widgets()
        self.setup_drag_and_drop()

    def setup_theme(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('Modern.Horizontal.TProgressbar',
                             background=COLORS['accent'],
                             troughcolor=COLORS['progress_bg'],
                             thickness=8,
                             borderwidth=0)

        self.style.configure('Modern.TCombobox',
                             fieldbackground=COLORS['input_bg'],
                             background=COLORS['input_bg'],
                             foreground=COLORS['text_primary'],
                             arrowcolor=COLORS['text_primary'],
                             borderwidth=0)

    def create_widgets(self):
        # Главный контейнер с отступами
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(expand=True, fill='both', padx=30, pady=30)

        # Заголовок
        header_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        header_frame.pack(fill='x', pady=(0, 20))

        title_label = tk.Label(
            header_frame,
            text="Конвертер файлов",
            font=('Segoe UI', 24, 'bold'),
            foreground=COLORS['text_primary'],
            background=COLORS['bg_primary']
        )
        title_label.pack(side='left')

        # Область Drag & Drop
        self.drop_frame = GlassFrame(main_container)
        self.drop_frame.configure(height=150)
        self.drop_frame.pack(fill='x', pady=(0, 20))
        self.drop_frame.pack_propagate(False)

        drop_content = tk.Frame(self.drop_frame, bg=COLORS['glass_bg'])
        drop_content.place(relx=0.5, rely=0.5, anchor='center')

        drop_label = tk.Label(
            drop_content,
            text="Перетащите файлы сюда\nили",
            font=('Segoe UI', 12),
            foreground=COLORS['text_secondary'],
            background=COLORS['glass_bg']
        )
        drop_label.pack(pady=(0, 10))

        browse_button = ModernButton(
            drop_content,
            text="Выберите файлы",
            command=self.select_files
        )
        browse_button.pack()

        # Панель настроек
        settings_frame = GlassFrame(main_container)
        settings_frame.pack(fill='x', pady=(0, 20))

        # Левая часть настроек
        settings_left = tk.Frame(settings_frame, bg=COLORS['glass_bg'])
        settings_left.pack(side='left')

        format_label = tk.Label(
            settings_left,
            text="Формат:",
            font=('Segoe UI', 10),
            foreground=COLORS['text_primary'],
            background=COLORS['glass_bg']
        )
        format_label.pack(side='left', padx=(0, 10))

        self.image_format_var = tk.StringVar(value='.png')
        image_format_menu = ttk.Combobox(
            settings_left,
            textvariable=self.image_format_var,
            values=['.png', '.jpg', '.tiff'],
            state='readonly',
            style='Modern.TCombobox',
            width=10
        )
        image_format_menu.pack(side='left')

        # Правая часть настроек
        settings_right = tk.Frame(settings_frame, bg=COLORS['glass_bg'])
        settings_right.pack(side='right')

        output_button = ModernButton(
            settings_right,
            text="Выбрать папку для сохранения",
            command=self.select_output_folder,
            is_secondary=True
        )
        output_button.pack(side='left', padx=(0, 10))

        convert_button = ModernButton(
            settings_right,
            text="Конвертировать",
            command=self.start_conversion
        )
        convert_button.pack(side='left')

        # Список файлов
        files_frame = GlassFrame(main_container)
        files_frame.pack(fill='both', expand=True, pady=(0, 20))

        files_label = tk.Label(
            files_frame,
            text="Выбранные файлы:",
            font=('Segoe UI', 11),
            foreground=COLORS['text_primary'],
            background=COLORS['glass_bg']
        )
        files_label.pack(anchor='w', pady=(0, 10))

        self.files_list = tk.Text(
            files_frame,
            font=('Segoe UI', 10),
            background=COLORS['input_bg'],
            foreground=COLORS['text_primary'],
            relief='flat',
            height=5,
            wrap='word'
        )
        self.files_list.pack(fill='both', expand=True)
        self.files_list.configure(state='disabled')

        # Прогресс и статус
        bottom_frame = tk.Frame(main_container, bg=COLORS['bg_primary'])
        bottom_frame.pack(fill='x')

        self.progress = ttk.Progressbar(
            bottom_frame,
            style='Modern.Horizontal.TProgressbar',
            mode='determinate'
        )
        self.progress.pack(fill='x')

        self.status_label = tk.Label(
            bottom_frame,
            text="Готов к работе",
            font=('Segoe UI', 10),
            foreground=COLORS['text_secondary'],
            background=COLORS['bg_primary'],
            wraplength=840
        )
        self.status_label.pack(pady=(10, 0))

    def setup_drag_and_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_files)
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_files)

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)

    def select_files(self):
        filetypes = [('Поддерживаемые файлы', ' '.join(CONVERSION_FUNCTIONS.keys())),
                     ('Все файлы', '*.*')]
        files = filedialog.askopenfilenames(filetypes=filetypes)
        if files:
            self.add_files(files)

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.output_dir = folder
            self.update_status(f"Папка сохранения: {folder}")

    def add_files(self, files):
        self.selected_files.extend(files)
        self.update_files_list()
        self.update_status(f"Добавлено {len(files)} файл(ов). Всего: {len(self.selected_files)} файл(ов)")

    def update_files_list(self):
        self.files_list.configure(state='normal')
        self.files_list.delete(1.0, tk.END)
        for file in self.selected_files:
            self.files_list.insert(tk.END, f"• {os.path.basename(file)}\n")
        self.files_list.configure(state='disabled')

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showwarning("Внимание", "Пожалуйста, выберите файлы для конвертации")
            return
        if self.processing:
            return

        self.processing = True
        threading.Thread(target=self.process_files, args=(self.selected_files,), daemon=True).start()

    def process_files(self, files):
        try:
            self.update_progress(0, len(files))
            self.update_status("Конвертация файлов...")

            converted_files = []
            with ThreadPoolExecutor(max_workers=4) as executor:
                future_to_file = {executor.submit(self.convert_file, file): file for file in files}
                completed = 0

                for future in future_to_file:
                    try:
                        file = future_to_file[future]
                        output_file = future.result()
                        converted_files.append(output_file)
                    except Exception as e:
                        file = future_to_file[future]
                        logging.error(f"Ошибка конвертации {file}: {str(e)}")
                        self.show_error(f"Ошибка конвертации {os.path.basename(file)}: {str(e)}")

                    completed += 1
                    self.update_progress(completed, len(files))

            self.selected_files = []
            self.update_files_list()

            status = (f"Успешно конвертировано: {len(converted_files)} файл(ов)\n" +
                      f"Расположение: {self.output_dir}")
            self.update_status(status)
            self.show_success(f"Конвертация завершена: {len(converted_files)} файл(ов)")

            # Открываем папку с результатами
            open_folder(self.output_dir)

        finally:
            self.processing = False

    def update_progress(self, value, maximum):
        self.root.after(0, lambda: self.progress.configure(value=value, maximum=maximum))

    def update_status(self, text):
        self.root.after(0, lambda: self.status_label.configure(text=text))

    def show_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("Ошибка", message))

    def show_success(self, message):
        self.root.after(0, lambda: messagebox.showinfo("Успех", message))

    def convert_file(self, file_path):
        ext = os.path.splitext(file_path.lower())[1]
        if ext not in CONVERSION_FUNCTIONS:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}")

        conversion_func = CONVERSION_FUNCTIONS[ext]
        if ext in {'.heic', '.tiff', '.bmp', '.webp', '.cr2', '.nef', '.arw'}:
            output_format = self.image_format_var.get()
            result = conversion_func(file_path, self.output_dir, output_format)
        else:
            result = conversion_func(file_path, self.output_dir)
        return result