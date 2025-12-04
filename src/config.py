"""
Módulo de configurações e constantes do aplicativo.
Centraliza todas as configurações globais para fácil manutenção.
"""
import os
import sys
import json

# ============================================
# VERSÃO E ATUALIZAÇÃO
# ============================================
APP_VERSION = "1.2.4"
GITHUB_REPO = "wiguiri/reroll-do-cadeiras"

# ============================================
# ARQUIVOS DE CONFIGURAÇÃO
# ============================================
CONFIG_FILE = 'game_automation_config.json'
PRESETS_FILE = 'game_automation_presets.json'

# ============================================
# CAMINHOS DO SISTEMA
# ============================================
def get_application_path():
    """Retorna o caminho base da aplicação."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_tesseract_path():
    """Retorna o caminho do executável do Tesseract."""
    app_path = get_application_path()
    portable_path = os.path.join(app_path, 'tesseract_portable', 'tesseract.exe')
    
    if os.path.exists(portable_path):
        return portable_path
    
    # Fallback para instalação padrão
    default_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(default_path):
        return default_path
    
    return portable_path  # Retorna o caminho esperado mesmo se não existir

def get_icon_path():
    """Retorna o caminho do ícone da aplicação."""
    app_path = get_application_path()
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'icone.png')
    return os.path.join(app_path, 'icone.png')

# ============================================
# CORES DO TEMA
# ============================================
COLORS = {
    'primary': ('#3B8ED0', '#1F6AA5'),
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'dark': '#64748b',
    'accent': '#3B8ED0',
}

# ============================================
# ATALHOS PADRÃO
# ============================================
DEFAULT_HOTKEYS = {
    'region': 'F1',
    'test': 'F3',
    'start': 'F5',
    'stop': 'F6'
}

# ============================================
# CONFIGURAÇÕES PADRÃO
# ============================================
DEFAULT_SETTINGS = {
    'delay': '0.4',
    'click_delay': '20',
    'max_attempts': '1000',
}

# ============================================
# ATRIBUTOS ESPECIAIS (sem valor numérico)
# ============================================
SPECIAL_ATTRIBUTES = {
    'golden realm': 1,
    'thunder realm': 1,
    'iced realm': 1,
    'tar realm': 1,
    'boss clone': 1
}

# ============================================
# CORREÇÕES DE OCR
# ============================================
OCR_CORRECTIONS = {
    'boss done': 'boss clone',
    'boss dlone': 'boss clone',
    'boss cione': 'boss clone',
    'boss clone ea': 'boss clone',
    'golden reaim': 'golden realm',
    'goiden realm': 'golden realm',
    'thunder reaim': 'thunder realm',
    'tar reaim': 'tar realm',
    'iced reaim': 'iced realm',
    'realm le': 'tar realm',
    'ig rer': 'tar realm',
    'i rr rer': 'tar realm',
    'i rer': 'tar realm'
}

# ============================================
# CONFIGURAÇÃO DE UI
# ============================================
UI_CONFIG = {
    'window_title': "🎮 Reroll do Cadeiras",
    'window_size': "1150x900",
    'window_min_size': (1100, 800),
    'font_family': "Segoe UI",
    'appearance_mode': "dark",
    'color_theme': "blue",
}

# ============================================
# SPLASH SCREEN
# ============================================
SPLASH_CONFIG = {
    'width': 500,
    'height': 400,
    'bg_color': "#0f0f1a",
    'accent_color': "#6366f1",
    'animation_fps': 30,
    'duration_seconds': 2,
}
