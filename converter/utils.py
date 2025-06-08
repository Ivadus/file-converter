import logging
import os
import subprocess

# Современная цветовая схема в стиле Neumorphism 2.0
COLORS = {
    'bg_primary': '#0F1117',  # Глубокий тёмный фон
    'glass_bg': '#1A1C24',  # Полупрозрачные панели (заменили rgba на hex)
    'input_bg': '#1E2028',  # Фон для полей ввода
    'button_bg': '#1f3438',  # Акцентный для кнопок
    'button_hover': '#9B5EF7',  # Светлее при наведении
    'accent': '#1f3438',  # Основной акцент
    'accent_secondary': '#3ABFED',  # Второй акцент (голубой)
    'text_primary': '#FFFFFF',  # Основной текст
    'text_secondary': '#A0A3B1',  # Вторичный текст
    'border': '#2A2D3A',  # Границы
    'border_active': '#1f3438',  # Активные границы
    'progress_bg': '#1E2028',  # Фон прогресс-бара
    'success': '#4CAF50',  # Цвет успеха
    'error': '#FF5252'  # Цвет ошибки
}


def setup_logging():
    logging.basicConfig(
        filename='converter.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def apply_hover_effect(widget, hover_color=None):
    """Применяет эффект наведения к виджету с плавной анимацией"""
    if hover_color is None:
        hover_color = COLORS['button_hover']

    default_bg = widget['background']

    def on_enter(e):
        widget['background'] = hover_color

    def on_leave(e):
        widget['background'] = default_bg

    widget.bind('<Enter>', on_enter)
    widget.bind('<Leave>', on_leave)


def open_folder(path):
    """Открывает папку в проводнике Windows или файловом менеджере"""
    if os.name == 'nt':  # Windows
        os.startfile(path)
    elif os.name == 'posix':  # macOS и Linux
        try:
            subprocess.run(['xdg-open', path])  # Linux
        except FileNotFoundError:
            subprocess.run(['open', path])  # macOS