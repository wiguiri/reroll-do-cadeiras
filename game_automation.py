import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
import pyautogui
import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageOps
import time
import threading
import re
import keyboard
import json
import os
import urllib.request
import subprocess
import tempfile
import random
import sys

# ============================================
# CONFIGURAÇÕES DE VERSÃO E ATUALIZAÇÃO
# ============================================
APP_VERSION = "1.1.0"
GITHUB_REPO = "wiguiri/reroll-do-cadeiras"

# Configurar CustomTkinter
ctk.set_appearance_mode("dark")  # Modes: "System" (padrão), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (padrão), "green", "dark-blue"

# Configurar caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Arquivo de configuração

import sys
import os

# Detecta se está rodando como executável PyInstaller
if getattr(sys, 'frozen', False):
    # Rodando como executável
    application_path = sys._MEIPASS
    tesseract_path = os.path.join(application_path, 'tesseract_portable', 'tesseract.exe')
else:
    # Rodando como script Python normal
    application_path = os.path.dirname(os.path.abspath(__file__))
    tesseract_path = os.path.join(application_path, 'tesseract_portable', 'tesseract.exe')

# Configura pytesseract para usar o Tesseract portable
if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path

CONFIG_FILE = 'game_automation_config.json'


# ============================================
# CLASSE DE AUTO-ATUALIZAÇÃO
# ============================================
class AutoUpdater:
    """Sistema de auto-atualização via GitHub Releases"""
    
    def __init__(self, current_version, github_repo):
        self.current_version = current_version
        self.github_repo = github_repo
        self.update_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
    
    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        try:
            req = urllib.request.Request(
                self.update_url,
                headers={'User-Agent': 'RerollDoCadeiras-Updater'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
            latest_version = data.get('tag_name', '').lstrip('v')
            download_url = None
            
            # Procura o .exe nos assets
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            if self._is_newer_version(latest_version):
                return {
                    'available': True,
                    'version': latest_version,
                    'download_url': download_url,
                    'release_notes': data.get('body', 'Sem notas de atualização')
                }
            
            return {'available': False}
            
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return {'available': False, 'error': str(e)}
    
    def _is_newer_version(self, remote_version):
        """Compara versões (formato: X.Y.Z)"""
        try:
            local_parts = [int(x) for x in self.current_version.split('.')]
            remote_parts = [int(x) for x in remote_version.split('.')]
            return remote_parts > local_parts
        except:
            return False
    
    def download_and_install(self, download_url, progress_callback=None):
        """Baixa e instala a atualização"""
        try:
            # Cria arquivo temporário
            temp_dir = tempfile.gettempdir()
            new_exe_path = os.path.join(temp_dir, "RerollDoCadeiras_new.exe")
            
            # Baixa o arquivo com progresso
            def report_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    progress_callback(percent)
            
            urllib.request.urlretrieve(download_url, new_exe_path, report_progress)
            
            # Cria script batch para substituir o executável
            current_exe = sys.executable if getattr(sys, 'frozen', False) else None
            
            if current_exe:
                batch_path = os.path.join(temp_dir, "update_reroll.bat")
                with open(batch_path, 'w') as f:
                    f.write(f'''@echo off
echo ========================================
echo    Atualizando Reroll do Cadeiras...
echo ========================================
timeout /t 2 /nobreak >nul
copy /Y "{new_exe_path}" "{current_exe}"
if errorlevel 1 (
    echo ERRO: Falha ao copiar arquivo!
    pause
    exit /b 1
)
del "{new_exe_path}"
echo Atualizacao concluida! Reiniciando...
timeout /t 1 /nobreak >nul
start "" "{current_exe}"
del "%~f0"
''')
                
                # Executa o batch e fecha o programa
                subprocess.Popen(batch_path, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                return True
            
            return False
            
        except Exception as e:
            print(f"Erro ao instalar atualização: {e}")
            return False


class GameAutomation:
    def __init__(self, root):
        self.root = root
        
        # Configurar janela principal
        self.root.title("🎮 Reroll do Cadeiras")
        self.root.geometry("1150x900")
        self.root.minsize(1100, 800)
        
        # Configurar ícone da janela
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'icone.png')
            else:
                icon_path = 'icone.png'
            
            if os.path.exists(icon_path):
                from PIL import Image
                icon_img = Image.open(icon_path)
                icon_photo = ctk.CTkImage(light_image=icon_img, dark_image=icon_img, size=(64, 64))
                # CustomTkinter não suporta iconphoto diretamente, mas podemos tentar com tkinter puro
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass  # Se falhar, usa ícone padrão
        
        self.is_running = False
        self.region = None
        self.target_values = {}
        self.log_window = None
        self.detail_log = None
        
        # Posições para automação de chaves (Aba 3)
        self.key_position = None
        self.orb_position = None
        self.bp_position = None
        
        # Cores CustomTkinter (já vêm prontas, mas guardamos referências)
        self.colors = {
            'primary': ('#3B8ED0', '#1F6AA5'),      # Azul CTk
            'success': '#10b981',      # Verde
            'warning': '#f59e0b',      # Laranja
            'danger': '#ef4444',       # Vermelho
            'dark': '#64748b',         # Cinza escuro
            'accent': '#3B8ED0',       # Azul (igual ao primary)
        }
        
        # Atalhos padrão (podem ser alterados pelo usuário)
        self.hotkeys = {
            'region': 'F1',
            'test': 'F3',
            'start': 'F5',
            'stop': 'F6'
        }
        
        # Variáveis do log (console foi removido)
        self.log_text = None
        
        self.setup_ui()
        self.load_config()  # Carrega configurações salvas (inclui atalhos)
        self.setup_global_hotkeys()  # Configura atalhos após carregar config
        
        # Salva ao fechar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Verifica atualizações ao iniciar
        # self.check_updates_on_start()  # Desabilitado temporariamente
        
    def setup_ui(self):
        # Configurar grid responsivo
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Container principal - SCROLLÁVEL
        main_container = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        
        # Header moderno
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Título grande e moderno
        title = ctk.CTkLabel(header_frame, text="⚡ Reroll do Cadeiras",
                            font=("Segoe UI", 24, "bold"))
        title.grid(row=0, column=0, sticky="w")
        
        # Créditos
        credits = ctk.CTkLabel(header_frame, text="por Victor Gomes de Sá",
                              font=("Segoe UI", 10),
                              text_color="gray60")
        credits.grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        # Botão de engrenagem (configuração de atalhos) no canto superior direito
        self.settings_btn = ctk.CTkButton(header_frame, text="⚙",
                                         command=self.open_hotkeys_settings,
                                         width=45, height=45,
                                         font=("Segoe UI", 24),
                                         fg_color="transparent", hover_color="gray30",
                                         corner_radius=10)
        self.settings_btn.grid(row=0, column=2, rowspan=2, sticky="ne", padx=(10, 0))
        
        # Sistema de abas moderno com CTkTabview
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        
        # Criar abas
        self.tabview.add("🎯 Valores Específicos")
        self.tabview.add("🔍 Busca de Atributos")
        self.tabview.add("🔑 Automação de Chaves")
        
        # Referências às abas
        self.tab_values = self.tabview.tab("🎯 Valores Específicos")
        self.tab_attributes = self.tabview.tab("🔍 Busca de Atributos")
        self.tab_keys = self.tabview.tab("🔑 Automação de Chaves")
        
        # Configurar conteúdo das abas
        self.setup_tab_values()
        self.setup_tab_attributes()
        self.setup_tab_keys()
        
        # Card de controles inferiores
        controls_card = ctk.CTkFrame(main_container, corner_radius=15, border_width=2)
        controls_card.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        controls_card.grid_columnconfigure(0, weight=1)
        
        # Região de captura - Card moderno
        region_container = ctk.CTkFrame(controls_card, fg_color="transparent")
        region_container.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        region_container.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(region_container, text="📍 Região de Captura",
                    font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        buttons_row = ctk.CTkFrame(region_container, fg_color="transparent")
        buttons_row.grid(row=1, column=0, sticky="ew")
        
        self.btn_region = ctk.CTkButton(buttons_row, text=f"🎯 Selecionar Região ({self.hotkeys['region']})",
                     command=self.select_region_visual, height=35)
        self.btn_region.pack(side="left", padx=(0, 10))
        self.btn_test = ctk.CTkButton(buttons_row, text=f"🔍 Testar Captura ({self.hotkeys['test']})",
                     command=self.test_capture_detailed, height=35,
                     fg_color="gray40")
        self.btn_test.pack(side="left")
        
        self.region_label = ctk.CTkLabel(region_container, text="● Região não configurada",
                                        text_color="#f59e0b")
        self.region_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
        
        # Separador
        ctk.CTkFrame(controls_card, height=2, fg_color="gray30").grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Configurações - Layout moderno em grid
        config_container = ctk.CTkFrame(controls_card, fg_color="transparent")
        config_container.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        
        ctk.CTkLabel(config_container, text="⚙️ Configurações",
                    font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))
        
        settings_row = ctk.CTkFrame(config_container, fg_color="transparent")
        settings_row.grid(row=1, column=0, sticky="w")
        
        # Delay entre pressões
        ctk.CTkLabel(settings_row, text="Delay (s):").pack(side="left", padx=(0, 5))
        self.delay_var = tk.StringVar(value="0.4")
        ctk.CTkEntry(settings_row, textvariable=self.delay_var, width=70, placeholder_text="0.1").pack(side="left", padx=(0, 20))
        
        # Delay do click
        ctk.CTkLabel(settings_row, text="Click (ms):").pack(side="left", padx=(0, 5))
        self.click_delay_var = tk.StringVar(value="20")
        ctk.CTkEntry(settings_row, textvariable=self.click_delay_var, width=70, placeholder_text="20").pack(side="left", padx=(0, 20))
        
        # Tentativas máximas
        ctk.CTkLabel(settings_row, text="Max:").pack(side="left", padx=(0, 5))
        self.max_attempts_var = tk.StringVar(value="1000")
        ctk.CTkEntry(settings_row, textvariable=self.max_attempts_var, width=80, placeholder_text="1000").pack(side="left")
        
        # Separador
        ctk.CTkFrame(controls_card, height=2, fg_color="gray30").grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        
        # Botões de controle - Destaque
        control_container = ctk.CTkFrame(controls_card, fg_color="transparent")
        control_container.grid(row=4, column=0, sticky="ew", padx=20, pady=15)
        control_container.grid_columnconfigure(0, weight=1)
        
        buttons_control = ctk.CTkFrame(control_container, fg_color="transparent")
        buttons_control.grid(row=0, column=0)
        
        self.start_button = ctk.CTkButton(buttons_control, text=f"▶ INICIAR ({self.hotkeys['start']})",
                                         command=self.start_automation,
                                         width=180, height=45,
                                         font=("Segoe UI", 13, "bold"),
                                         fg_color="#047857", hover_color="#065f46",
                                         text_color="white")
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(buttons_control, text=f"⬛ PARAR ({self.hotkeys['stop']})",
                                        command=self.stop_automation,
                                        width=180, height=45,
                                        font=("Segoe UI", 13, "bold"),
                                        fg_color="#b91c1c", hover_color="#991b1b",
                                        text_color="white",
                                        state="disabled")
        self.stop_button.pack(side="left", padx=5)
        
        ctk.CTkButton(buttons_control, text="📊 Log Detalhado",
                     command=self.open_log_window,
                     width=150, height=45,
                     font=("Segoe UI", 13, "bold"),
                     fg_color="#4b5563", hover_color="#374151",
                     text_color="white").pack(side="left", padx=5)
        
        # Status com ícone
        self.status_label = ctk.CTkLabel(control_container, text="● Aguardando configuração...",
                                        font=("Segoe UI", 10),
                                        text_color="gray60")
        self.status_label.grid(row=1, column=0, pady=(10, 0))
        
        self.controls_card = controls_card  # Guardar referência
        
        # Footer com tema e versão
        footer_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Toggle de tema
        theme_switch = ctk.CTkSwitch(footer_frame, text="🌙 Modo Dark",
                                    command=self.toggle_theme,
                                    font=("Segoe UI", 11))
        theme_switch.grid(row=0, column=0, sticky="w")
        theme_switch.select()  # Inicia com dark ativo
        
        # Versão e botão de atualização
        version_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        version_frame.grid(row=0, column=2, sticky="e")
        
        self.version_label = ctk.CTkLabel(version_frame, text=f"v{APP_VERSION}",
                                         font=("Segoe UI", 10), text_color="gray50")
        self.version_label.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(version_frame, text="🔄 Verificar Atualizações",
                     command=self.check_updates_manual,
                     width=160, height=28,
                     font=("Segoe UI", 10),
                     fg_color="gray30", hover_color="gray40").pack(side="left")
        
        # Configurar hotkeys
        self.setup_hotkeys()
    
    def setup_tab_values(self):
        """Configura a aba de busca por valores específicos"""
        # Header com título e presets
        header_frame = ctk.CTkFrame(self.tab_values, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(header_frame, text="📝 Atributos e Valores Alvos",
                    font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Botões de preset no canto direito
        preset_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        preset_frame.pack(side="right")
        
        self.values_preset_combo = ctk.CTkComboBox(preset_frame, width=160, height=32,
                                                   values=["Preset 1", "+ Novo Preset"],
                                                   command=lambda x: self.on_preset_selected('values', x),
                                                   font=("Segoe UI", 11))
        self.values_preset_combo.pack(side="left", padx=5)
        self.values_preset_combo.set("Preset 1")
        
        ctk.CTkButton(preset_frame, text="Salvar", width=70, height=32,
                     command=lambda: self.save_current_preset('values'),
                     font=("Segoe UI", 11, "bold"), fg_color="#047857", hover_color="#065f46",
                     text_color="white").pack(side="left", padx=2)
        ctk.CTkButton(preset_frame, text="Excluir", width=70, height=32,
                     command=lambda: self.delete_preset_dialog('values'),
                     font=("Segoe UI", 11), fg_color="#b91c1c", hover_color="#991b1b",
                     text_color="white").pack(side="left", padx=2)
        
        # Frame scrollável para atributos - ALTURA MAIOR
        attr_frame = ctk.CTkScrollableFrame(self.tab_values, corner_radius=10, height=220)
        attr_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.attr_entries = []
        self.attr_inner_frame = attr_frame
        
        # Adicionar primeira linha
        self.add_attribute_row()
        
        # Botão grande e visível
        ctk.CTkButton(self.tab_values, text="➕ ADICIONAR ATRIBUTO",
                     command=self.add_attribute_row, height=40,
                     font=("Segoe UI", 12, "bold"),
                     fg_color="#2563eb", hover_color="#1d4ed8").pack(pady=10, padx=15, fill="x")
        
        # Instruções
        ctk.CTkLabel(self.tab_values,
                    text="💡 Digite o nome do atributo e o valor desejado. Ex: Strength = 15",
                    text_color="#6b7280", wraplength=600,
                    font=("Segoe UI", 10)).pack(pady=(0, 15), padx=15)
    
    def setup_tab_attributes(self):
        """Configura a aba de busca por presença de atributos"""
        # Header com título e presets
        header_frame = ctk.CTkFrame(self.tab_attributes, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(header_frame, text="📋 Atributos para Buscar",
                    font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Botões de preset no canto direito
        preset_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        preset_frame.pack(side="right")
        
        self.search_preset_combo = ctk.CTkComboBox(preset_frame, width=160, height=32,
                                                   values=["Preset 1", "+ Novo Preset"],
                                                   command=lambda x: self.on_preset_selected('search', x),
                                                   font=("Segoe UI", 11))
        self.search_preset_combo.pack(side="left", padx=5)
        self.search_preset_combo.set("Preset 1")
        
        ctk.CTkButton(preset_frame, text="Salvar", width=70, height=32,
                     command=lambda: self.save_current_preset('search'),
                     font=("Segoe UI", 11, "bold"), fg_color="#047857", hover_color="#065f46",
                     text_color="white").pack(side="left", padx=2)
        ctk.CTkButton(preset_frame, text="Excluir", width=70, height=32,
                     command=lambda: self.delete_preset_dialog('search'),
                     font=("Segoe UI", 11), fg_color="#b91c1c", hover_color="#991b1b",
                     text_color="white").pack(side="left", padx=2)
        
        # Frame scrollável - ALTURA MAIOR
        search_frame = ctk.CTkScrollableFrame(self.tab_attributes, corner_radius=10, height=190)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.search_entries = []
        self.search_inner_frame = search_frame
        
        # Adicionar primeira linha
        self.add_search_row()
        
        # Botão grande e visível
        ctk.CTkButton(self.tab_attributes, text="➕ ADICIONAR ATRIBUTO",
                     command=self.add_search_row, height=40,
                     font=("Segoe UI", 12, "bold"),
                     fg_color="#2563eb", hover_color="#1d4ed8").pack(pady=10, padx=15, fill="x")
        
        # Configuração de modo
        count_frame = ctk.CTkFrame(self.tab_attributes, corner_radius=10, fg_color=("gray90", "gray20"))
        count_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(count_frame, text="🎯 Modo:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10, pady=10)
        self.min_attributes_var = tk.StringVar(value="ALL")
        
        ctk.CTkRadioButton(count_frame, text="TODOS", variable=self.min_attributes_var, 
                          value="ALL", font=("Segoe UI", 11)).pack(side="left", padx=5)
        ctk.CTkRadioButton(count_frame, text="Mínimo:", variable=self.min_attributes_var, 
                          value="MIN", font=("Segoe UI", 11)).pack(side="left", padx=5)
        
        self.min_count_entry = ctk.CTkEntry(count_frame, width=60, placeholder_text="3", height=35)
        self.min_count_entry.insert(0, "3")
        self.min_count_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(count_frame, text="atributo(s)", font=("Segoe UI", 11)).pack(side="left", padx=5)
        
        # Instruções
        ctk.CTkLabel(self.tab_attributes, 
                    text="💡 Busca PRESENÇA de atributos | ⭐ Obrigatório = sempre deve aparecer no modo MÍNIMO",
                    text_color="#6b7280", wraplength=600,
                    font=("Segoe UI", 10)).pack(pady=(0, 15), padx=15)
    
    def setup_tab_keys(self):
        """Configura a aba de automação de chaves"""
        # Header com título e presets
        header_frame = ctk.CTkFrame(self.tab_keys, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(header_frame, text="🔑 Atributos Desejados nas Chaves",
                    font=("Segoe UI", 14, "bold")).pack(side="left")
        
        # Botões de preset no canto direito
        preset_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        preset_frame.pack(side="right")
        
        self.keys_preset_combo = ctk.CTkComboBox(preset_frame, width=160, height=32,
                                                  values=["Preset 1", "+ Novo Preset"],
                                                  command=lambda x: self.on_preset_selected('keys', x),
                                                  font=("Segoe UI", 11))
        self.keys_preset_combo.pack(side="left", padx=5)
        self.keys_preset_combo.set("Preset 1")
        
        ctk.CTkButton(preset_frame, text="Salvar", width=70, height=32,
                     command=lambda: self.save_current_preset('keys'),
                     font=("Segoe UI", 11, "bold"), fg_color="#047857", hover_color="#065f46",
                     text_color="white").pack(side="left", padx=2)
        ctk.CTkButton(preset_frame, text="Excluir", width=70, height=32,
                     command=lambda: self.delete_preset_dialog('keys'),
                     font=("Segoe UI", 11), fg_color="#b91c1c", hover_color="#991b1b",
                     text_color="white").pack(side="left", padx=2)
        
        # Frame scrollável - ALTURA MAIOR
        search_frame = ctk.CTkScrollableFrame(self.tab_keys, corner_radius=10, height=150)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.keys_entries = []
        self.keys_inner_frame = search_frame
        
        # Adicionar primeira linha
        self.add_keys_row()
        
        # Botão grande e visível
        ctk.CTkButton(self.tab_keys, text="➕ ADICIONAR ATRIBUTO",
                     command=self.add_keys_row, height=40,
                     font=("Segoe UI", 12, "bold"),
                     fg_color="#2563eb", hover_color="#1d4ed8").pack(pady=10, padx=15, fill="x")
        
        # Configuração de modo
        count_frame = ctk.CTkFrame(self.tab_keys, corner_radius=10, fg_color=("gray90", "gray20"))
        count_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(count_frame, text="🎯 Modo:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10, pady=10)
        self.keys_min_var = tk.StringVar(value="ALL")
        
        ctk.CTkRadioButton(count_frame, text="TODOS", variable=self.keys_min_var, 
                          value="ALL", font=("Segoe UI", 11)).pack(side="left", padx=5)
        ctk.CTkRadioButton(count_frame, text="Mínimo:", variable=self.keys_min_var, 
                          value="MIN", font=("Segoe UI", 11)).pack(side="left", padx=5)
        
        self.keys_min_count = ctk.CTkEntry(count_frame, width=60, placeholder_text="2", height=35)
        self.keys_min_count.insert(0, "2")
        self.keys_min_count.pack(side="left", padx=5)
        
        ctk.CTkLabel(count_frame, text="atributo(s)", font=("Segoe UI", 11)).pack(side="left", padx=5)
        
        # Configuração de Posições
        pos_frame = ctk.CTkFrame(self.tab_keys, corner_radius=10, fg_color=("gray90", "gray20"))
        pos_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(pos_frame, text="📍 Configurar Posições",
                    font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=15, padx=15)
        
        # Posição da Chave
        key_frame = ctk.CTkFrame(pos_frame, fg_color="transparent")
        key_frame.pack(fill="x", pady=8, padx=15)
        ctk.CTkButton(key_frame, text="📍 CAPTURAR CHAVE", 
                     command=self.capture_key_position, width=200, height=40,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0,10))
        self.key_pos_label = ctk.CTkLabel(key_frame, text="● Não configurada", 
                                          text_color="#ef4444", font=("Segoe UI", 10))
        self.key_pos_label.pack(side="left", padx=5)
        
        # Posição do Orb
        orb_frame = ctk.CTkFrame(pos_frame, fg_color="transparent")
        orb_frame.pack(fill="x", pady=8, padx=15)
        ctk.CTkButton(orb_frame, text="🔮 CAPTURAR ORB", 
                     command=self.capture_orb_position, width=200, height=40,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0,10))
        self.orb_pos_label = ctk.CTkLabel(orb_frame, text="● Não configurada", 
                                          text_color="#ef4444", font=("Segoe UI", 10))
        self.orb_pos_label.pack(side="left", padx=5)
        
        # Posição da BP
        bp_frame = ctk.CTkFrame(pos_frame, fg_color="transparent")
        bp_frame.pack(fill="x", pady=(8, 15), padx=15)
        ctk.CTkButton(bp_frame, text="🎒 CAPTURAR BP", 
                     command=self.capture_bp_position, width=200, height=40,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0,10))
        self.bp_pos_label = ctk.CTkLabel(bp_frame, text="● Não configurada", 
                                         text_color="#ef4444", font=("Segoe UI", 10))
        self.bp_pos_label.pack(side="left", padx=5)
        
        # Instruções (será atualizado dinamicamente)
        self.keys_instructions_label = ctk.CTkLabel(self.tab_keys, 
                    text=f"💡 1. Configure região ({self.hotkeys['region']}) | 2. Capture posições | 3. {self.hotkeys['start']} inicia automação",
                    text_color="#6b7280", wraplength=600,
                    font=("Segoe UI", 10))
        self.keys_instructions_label.pack(pady=(0, 15), padx=15)
        
    def setup_hotkeys(self):
        """Configura bindings locais da janela"""
        # Remove bindings antigos se existirem
        try:
            self.root.unbind('<F1>')
            self.root.unbind('<F3>')
            self.root.unbind('<F5>')
            self.root.unbind('<F6>')
        except:
            pass
        
        # Adiciona novos bindings
        self.root.bind(f'<{self.hotkeys["region"]}>', lambda e: self.select_region_visual())
        self.root.bind(f'<{self.hotkeys["test"]}>', lambda e: self.test_capture_detailed())
        self.root.bind(f'<{self.hotkeys["start"]}>', lambda e: self.start_automation())
        self.root.bind(f'<{self.hotkeys["stop"]}>', lambda e: self.stop_automation())
    
    def setup_global_hotkeys(self):
        """Configura hotkeys globais que funcionam mesmo fora da janela"""
        # Remove todos os hotkeys antigos primeiro
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        
        try:
            keyboard.add_hotkey(self.hotkeys['region'].lower(), self.select_region_visual)
            keyboard.add_hotkey(self.hotkeys['test'].lower(), self.test_capture_detailed)
            keyboard.add_hotkey(self.hotkeys['start'].lower(), self.start_automation)
            keyboard.add_hotkey(self.hotkeys['stop'].lower(), self.stop_automation)
            self.log(f"⌨️ Atalhos: {self.hotkeys['region']} (Região) | {self.hotkeys['test']} (Teste) | {self.hotkeys['start']} (Iniciar) | {self.hotkeys['stop']} (Parar)")
        except Exception as e:
            self.log(f"⚠️ Erro ao configurar atalhos globais: {e}")
            self.log("Execute o programa como Administrador para usar atalhos globais")
    
    def open_hotkeys_settings(self):
        """Abre janela de configuração de atalhos"""
        # Desabilita hotkeys globais enquanto configura
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ Configurar Atalhos")
        settings_window.geometry("450x350")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Variáveis para armazenar os novos atalhos (declarado antes do on_close)
        hotkey_vars = {
            'region': tk.StringVar(value=self.hotkeys['region']),
            'test': tk.StringVar(value=self.hotkeys['test']),
            'start': tk.StringVar(value=self.hotkeys['start']),
            'stop': tk.StringVar(value=self.hotkeys['stop'])
        }
        
        # Salva e reativa hotkeys ao fechar a janela (por qualquer meio)
        def on_close():
            # Salva os atalhos alterados
            for key_name, var in hotkey_vars.items():
                self.hotkeys[key_name] = var.get().upper()
            
            # Atualiza labels na UI
            self.update_hotkey_labels()
            
            # Reconfigura hotkeys
            self.setup_hotkeys()
            self.setup_global_hotkeys()
            
            # Salva no arquivo
            self.save_config()
            
            settings_window.destroy()
        
        settings_window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Centraliza
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - 225
        y = (settings_window.winfo_screenheight() // 2) - 175
        settings_window.geometry(f"+{x}+{y}")
        
        # Título
        ctk.CTkLabel(settings_window, text="⚙️ Configurar Teclas de Atalho",
                    font=("Segoe UI", 18, "bold")).pack(pady=(20, 5))
        
        ctk.CTkLabel(settings_window, text="Clique no campo e pressione a nova tecla",
                    font=("Segoe UI", 11), text_color="gray60").pack(pady=(0, 15))
        
        # Frame para os atalhos
        hotkeys_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        hotkeys_frame.pack(fill="x", padx=30, pady=10)
        
        hotkey_entries = {}
        
        labels = {
            'region': '🎯 Selecionar Região:',
            'test': '🔍 Testar Captura:',
            'start': '▶ Iniciar Automação:',
            'stop': '⬛ Parar Automação:'
        }
        
        def capture_key(event, key_name, entry):
            """Captura a tecla pressionada"""
            key = event.keysym
            if key in ['Escape', 'Return', 'Tab']:
                return "break"
            
            # Formata a tecla (ex: f1 -> F1)
            formatted_key = key.upper() if len(key) == 1 else key.capitalize()
            if key.lower().startswith('f') and key[1:].isdigit():
                formatted_key = key.upper()
            
            hotkey_vars[key_name].set(formatted_key)
            entry.configure(border_color="#10b981")  # Verde para indicar sucesso
            settings_window.after(500, lambda: entry.configure(border_color="gray50"))
            return "break"
        
        for i, (key_name, label_text) in enumerate(labels.items()):
            row_frame = ctk.CTkFrame(hotkeys_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=8)
            
            ctk.CTkLabel(row_frame, text=label_text, font=("Segoe UI", 12),
                        width=180, anchor="w").pack(side="left")
            
            entry = ctk.CTkEntry(row_frame, textvariable=hotkey_vars[key_name],
                                width=100, height=35, font=("Segoe UI", 12, "bold"),
                                justify="center", border_color="gray50")
            entry.pack(side="left", padx=10)
            entry.bind('<KeyPress>', lambda e, kn=key_name, ent=entry: capture_key(e, kn, ent))
            hotkey_entries[key_name] = entry
        
        # Botões
        buttons_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        buttons_frame.pack(pady=25)
        
        def save_hotkeys():
            """Salva os novos atalhos"""
            # Verifica duplicatas
            values = [v.get().upper() for v in hotkey_vars.values()]
            if len(values) != len(set(values)):
                messagebox.showwarning("Aviso", "Não pode haver atalhos duplicados!")
                return
            
            # Atualiza os atalhos
            for key_name, var in hotkey_vars.items():
                self.hotkeys[key_name] = var.get().upper()
            
            # Atualiza os textos dos botões
            self.update_hotkey_labels()
            
            # Reconfigura os hotkeys globais e locais
            self.setup_hotkeys()
            self.setup_global_hotkeys()
            
            # Salva configuração
            self.save_config()
            
            settings_window.destroy()
            messagebox.showinfo("✓ Sucesso", "Atalhos atualizados com sucesso!")
        
        def reset_defaults():
            """Restaura atalhos padrão"""
            hotkey_vars['region'].set('F1')
            hotkey_vars['test'].set('F3')
            hotkey_vars['start'].set('F5')
            hotkey_vars['stop'].set('F6')
        
        ctk.CTkButton(buttons_frame, text="✓ Salvar", command=save_hotkeys,
                     width=120, height=40, font=("Segoe UI", 12, "bold"),
                     fg_color="#10b981", hover_color="#059669").pack(side="left", padx=10)
        
        ctk.CTkButton(buttons_frame, text="↺ Padrão", command=reset_defaults,
                     width=120, height=40, font=("Segoe UI", 12, "bold"),
                     fg_color="gray40", hover_color="gray30").pack(side="left", padx=10)
        
        ctk.CTkButton(buttons_frame, text="Cancelar", command=on_close,
                     width=100, height=40, font=("Segoe UI", 12),
                     fg_color="gray30", hover_color="gray20").pack(side="left", padx=10)
    
    def update_hotkey_labels(self):
        """Atualiza todos os labels/botões que mostram os atalhos"""
        # Botões de região e teste
        self.btn_region.configure(text=f"🎯 Selecionar Região ({self.hotkeys['region']})")
        self.btn_test.configure(text=f"🔍 Testar Captura ({self.hotkeys['test']})")
        
        # Botões de iniciar/parar
        self.start_button.configure(text=f"▶ INICIAR ({self.hotkeys['start']})")
        self.stop_button.configure(text=f"⬛ PARAR ({self.hotkeys['stop']})")
        
        # Instruções da aba de chaves
        self.keys_instructions_label.configure(
            text=f"💡 1. Configure região ({self.hotkeys['region']}) | 2. Capture posições | 3. {self.hotkeys['start']} inicia automação"
        )
    
    # ============================================
    # SISTEMA DE PRESETS
    # ============================================
    
    def get_presets_file(self):
        """Retorna o caminho do arquivo de presets"""
        return 'game_automation_presets.json'
    
    def load_all_presets(self):
        """Carrega todos os presets do arquivo"""
        try:
            presets_file = self.get_presets_file()
            if os.path.exists(presets_file):
                with open(presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'values': {}, 'search': {}, 'keys': {}}
    
    def save_all_presets(self, presets):
        """Salva todos os presets no arquivo"""
        try:
            with open(self.get_presets_file(), 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"⚠️ Erro ao salvar presets: {e}")
    
    def update_preset_combos(self):
        """Atualiza os ComboBox de presets com a lista atual"""
        presets = self.load_all_presets()
        
        # Garante que "Preset 1" existe em cada aba
        for tab_type in ['values', 'search', 'keys']:
            if 'Preset 1' not in presets.get(tab_type, {}):
                if tab_type not in presets:
                    presets[tab_type] = {}
                presets[tab_type]['Preset 1'] = [] if tab_type == 'values' else {'attributes': [], 'mode': 'ALL', 'min_count': '3'}
        
        self.save_all_presets(presets)
        
        # Atualiza combo da aba Values
        values_list = list(presets.get('values', {}).keys()) + ["+ Novo Preset"]
        self.values_preset_combo.configure(values=values_list)
        
        # Atualiza combo da aba Search
        search_list = list(presets.get('search', {}).keys()) + ["+ Novo Preset"]
        self.search_preset_combo.configure(values=search_list)
        
        # Atualiza combo da aba Keys
        keys_list = list(presets.get('keys', {}).keys()) + ["+ Novo Preset"]
        self.keys_preset_combo.configure(values=keys_list)
    
    def on_preset_selected(self, tab_type, name):
        """Chamado quando um preset é selecionado no combo"""
        if name == "+ Novo Preset":
            self.create_new_preset_dialog(tab_type)
        else:
            self.load_preset(tab_type, name)
    
    def save_current_preset(self, tab_type):
        """Salva o preset atualmente selecionado"""
        combo = getattr(self, f'{tab_type}_preset_combo')
        current_name = combo.get()
        
        if current_name == "+ Novo Preset":
            self.create_new_preset_dialog(tab_type)
            return
        
        self.save_preset(tab_type, current_name)
        messagebox.showinfo("✓ Salvo", f"Preset '{current_name}' salvo com sucesso!")
    
    def create_new_preset_dialog(self, tab_type):
        """Abre diálogo para criar novo preset"""
        # Restaura o combo para o preset anterior
        combo = getattr(self, f'{tab_type}_preset_combo')
        presets = self.load_all_presets()
        preset_names = list(presets.get(tab_type, {}).keys())
        if preset_names:
            combo.set(preset_names[0])
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Novo Preset")
        dialog.geometry("420x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Centraliza
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 210
        y = (dialog.winfo_screenheight() // 2) - 125
        dialog.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Título
        ctk.CTkLabel(main_frame, text="Criar Novo Preset",
                    font=("Segoe UI", 18, "bold")).pack(pady=(0, 5))
        
        ctk.CTkLabel(main_frame, text="Digite um nome para o novo preset:",
                    font=("Segoe UI", 11), text_color="gray60").pack(pady=(0, 15))
        
        name_entry = ctk.CTkEntry(main_frame, width=320, height=42, 
                                  placeholder_text="Ex: Build DPS, Tank Setup...",
                                  font=("Segoe UI", 12))
        name_entry.pack(pady=(0, 20))
        name_entry.focus()
        
        def do_create():
            name = name_entry.get().strip()
            if not name or name == "+ Novo Preset":
                messagebox.showwarning("Aviso", "Digite um nome válido para o preset")
                return
            
            # Verifica se já existe
            presets = self.load_all_presets()
            if name in presets.get(tab_type, {}):
                messagebox.showwarning("Aviso", f"Já existe um preset com o nome '{name}'")
                return
            
            # Salva o preset atual com o novo nome
            self.save_preset(tab_type, name)
            
            # Seleciona o novo preset no combo
            combo = getattr(self, f'{tab_type}_preset_combo')
            combo.set(name)
            
            dialog.destroy()
            messagebox.showinfo("Sucesso", f"Preset '{name}' criado!")
        
        # Frame dos botões
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        # Centraliza os botões
        btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_inner.pack()
        
        ctk.CTkButton(btn_inner, text="Criar", command=do_create,
                     width=130, height=42, font=("Segoe UI", 13, "bold"),
                     fg_color="#047857", hover_color="#065f46",
                     text_color="white").pack(side="left", padx=8)
        
        ctk.CTkButton(btn_inner, text="Cancelar", command=dialog.destroy,
                     width=130, height=42, font=("Segoe UI", 13),
                     fg_color="#4b5563", hover_color="#374151",
                     text_color="white").pack(side="left", padx=8)
        
        # Enter para criar
        name_entry.bind('<Return>', lambda e: do_create())
    
    def save_preset(self, tab_type, name):
        """Salva o preset atual"""
        presets = self.load_all_presets()
        
        if tab_type == 'values':
            # Salva atributos com valores
            data = []
            for entry in self.attr_entries:
                attr_name = entry['name'].get().strip()
                attr_value = entry['value'].get().strip()
                if attr_name:
                    data.append({
                        'name': attr_name,
                        'value': attr_value,
                        'tolerance': entry['tolerance'].get() if 'tolerance' in entry else '0'
                    })
            presets['values'][name] = data
            
        elif tab_type == 'search':
            # Salva atributos de busca
            data = {
                'attributes': [],
                'mode': self.min_attributes_var.get(),
                'min_count': self.min_count_entry.get()
            }
            for entry in self.search_entries:
                attr_name = entry['name'].get().strip()
                if attr_name:
                    data['attributes'].append({
                        'name': attr_name,
                        'required': entry['required'].get()
                    })
            presets['search'][name] = data
            
        elif tab_type == 'keys':
            # Salva atributos de chaves
            data = {
                'attributes': [],
                'mode': self.keys_min_var.get(),
                'min_count': self.keys_min_count.get()
            }
            for entry in self.keys_entries:
                attr_name = entry['name'].get().strip()
                if attr_name:
                    data['attributes'].append({
                        'name': attr_name,
                        'required': entry['required'].get()
                    })
            presets['keys'][name] = data
        
        self.save_all_presets(presets)
        self.update_preset_combos()
        self.log(f"💾 Preset '{name}' salvo")
    
    def load_preset(self, tab_type, name):
        """Carrega um preset"""
        if name == "+ Novo Preset" or not name:
            return
        
        presets = self.load_all_presets()
        
        if tab_type == 'values':
            data = presets.get('values', {}).get(name)
            if not data:
                return
            
            # Limpa entradas atuais
            for entry in self.attr_entries[:]:
                entry['frame'].destroy()
            self.attr_entries.clear()
            
            # Carrega do preset
            for attr in data:
                self.add_attribute_row(attr.get('name', ''), attr.get('value', ''))
            
            if not self.attr_entries:
                self.add_attribute_row()
            
            self.values_preset_combo.set(name)
            
        elif tab_type == 'search':
            data = presets.get('search', {}).get(name)
            if not data:
                return
            
            # Limpa entradas atuais
            for entry in self.search_entries[:]:
                entry['frame'].destroy()
            self.search_entries.clear()
            
            # Carrega do preset
            for attr in data.get('attributes', []):
                self.add_search_row(attr.get('name', ''), attr.get('required', False))
            
            if not self.search_entries:
                self.add_search_row()
            
            # Carrega modo
            self.min_attributes_var.set(data.get('mode', 'ALL'))
            self.min_count_entry.delete(0, 'end')
            self.min_count_entry.insert(0, data.get('min_count', '3'))
            
            self.search_preset_combo.set(name)
            
        elif tab_type == 'keys':
            data = presets.get('keys', {}).get(name)
            if not data:
                return
            
            # Limpa entradas atuais
            for entry in self.keys_entries[:]:
                entry['frame'].destroy()
            self.keys_entries.clear()
            
            # Carrega do preset
            for attr in data.get('attributes', []):
                self.add_keys_row(attr.get('name', ''), attr.get('required', False))
            
            if not self.keys_entries:
                self.add_keys_row()
            
            # Carrega modo
            self.keys_min_var.set(data.get('mode', 'ALL'))
            self.keys_min_count.delete(0, 'end')
            self.keys_min_count.insert(0, data.get('min_count', '2'))
            
            self.keys_preset_combo.set(name)
        
        self.log(f"📂 Preset '{name}' carregado")
    
    def delete_preset_dialog(self, tab_type):
        """Exclui o preset atualmente selecionado"""
        combo = getattr(self, f'{tab_type}_preset_combo')
        current_preset = combo.get()
        
        # Carrega presets
        presets = self.load_all_presets()
        preset_list = list(presets.get(tab_type, {}).keys())
        
        # Não pode excluir se só tem 1 preset
        if len(preset_list) <= 1:
            messagebox.showinfo("Info", "Não é possível excluir. Deve haver pelo menos 1 preset.")
            return
        
        # Não pode excluir "+ Novo Preset"
        if current_preset == "+ Novo Preset":
            messagebox.showinfo("Info", "Selecione um preset válido para excluir.")
            return
        
        # Confirmação
        if messagebox.askyesno("Confirmar Exclusão", f"Excluir o preset '{current_preset}'?\n\nEsta ação não pode ser desfeita."):
            # Remove o preset
            if current_preset in presets.get(tab_type, {}):
                del presets[tab_type][current_preset]
                self.save_all_presets(presets)
                self.update_preset_combos()
                
                # Seleciona outro preset disponível
                remaining = list(presets.get(tab_type, {}).keys())
                if remaining:
                    combo.set(remaining[0])
                    self.load_preset(tab_type, remaining[0])
                
                self.log(f"Preset '{current_preset}' excluído")
                messagebox.showinfo("Sucesso", f"Preset '{current_preset}' excluído!")
        
    def select_region_visual(self):
        """Captura tela congelada e permite selecionar região visualmente"""
        self.log("📸 Capturando tela... Aguarde...")
        
        # Minimiza a janela principal
        self.root.iconify()
        self.root.update()
        
        # Aguarda para garantir que a janela foi minimizada
        time.sleep(0.2)
        
        # Captura a tela inteira
        screenshot = ImageGrab.grab()
        screen_width, screen_height = screenshot.size
        
        self.log("🎯 Tela capturada! Clique e arraste para selecionar a região")
        
        # Cria janela fullscreen
        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.configure(background='black')
        
        # Converte PIL Image para PhotoImage
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(screenshot)
        
        # Variáveis para armazenar coordenadas
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        
        # Canvas para mostrar a imagem e desenhar o retângulo
        canvas = tk.Canvas(overlay, highlightthickness=0, background='black')
        canvas.pack(fill="both", expand=True)
        
        # Mostra a screenshot de fundo
        canvas.create_image(0, 0, image=photo, anchor='nw')
        
        # Texto de instrução (com fundo para melhor visibilidade)
        canvas.create_rectangle(
            screen_width // 2 - 300, 20,
            screen_width // 2 + 300, 70,
            fill='black', outline='white', width=2
        )
        canvas.create_text(
            screen_width // 2, 45,
            text="Clique e arraste para selecionar a região | ESC para cancelar",
            font=('Arial', 14, 'bold'),
            fill='yellow'
        )
        
        def on_mouse_down(event):
            self.selection_start = (event.x, event.y)
            
        def on_mouse_move(event):
            if self.selection_start:
                # Remove retângulo anterior
                if self.selection_rect:
                    canvas.delete(self.selection_rect)
                    canvas.delete('coords_text')
                    canvas.delete('coords_bg')
                
                # Desenha novo retângulo
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y
                self.selection_rect = canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='red',
                    width=3
                )
                
                # Mostra coordenadas
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                text_x = (x1 + x2) // 2
                text_y = min(y1, y2) - 25
                
                # Fundo do texto
                canvas.create_rectangle(
                    text_x - 80, text_y - 15,
                    text_x + 80, text_y + 15,
                    fill='black', outline='yellow', width=1,
                    tags='coords_bg'
                )
                canvas.create_text(
                    text_x, text_y,
                    text=f"{w} x {h} pixels",
                    font=('Arial', 12, 'bold'),
                    fill='yellow',
                    tags='coords_text'
                )
        
        def on_mouse_up(event):
            if self.selection_start:
                self.selection_end = (event.x, event.y)
                
                x1, y1 = self.selection_start
                x2, y2 = self.selection_end
                
                # Normaliza as coordenadas (garante que x1 < x2 e y1 < y2)
                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)
                
                # Valida que a região tem tamanho mínimo
                if (right - left) < 10 or (bottom - top) < 10:
                    canvas.delete(self.selection_rect)
                    canvas.delete('coords_text')
                    canvas.delete('coords_bg')
                    self.selection_start = None
                    return
                
                # Define a região
                self.region = (left, top, right, bottom)
                
                # Fecha a janela overlay
                overlay.destroy()
                
                # Restaura a janela principal
                self.root.deiconify()
                
                # Atualiza o label da região
                width = right - left
                height = bottom - top
                self.region_label.configure(
                    text=f"✓ Região configurada: {left},{top} → {right},{bottom} ({width}x{height}px)",
                    text_color="#10b981"
                )
                
                # Loga sucesso
                self.log(f"✓ Região selecionada: ({left}, {top}) → ({right}, {bottom}) | {width}x{height}px")
                
                # Salva a configuração
                self.save_config()
                
        def on_escape(event):
            overlay.destroy()
            self.root.deiconify()
            self.log("❌ Seleção cancelada")
        
        # Bind eventos
        canvas.bind('<ButtonPress-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        overlay.bind('<Escape>', on_escape)
        
        # Mantém referência da imagem para não ser coletada pelo garbage collector
        overlay.photo = photo
        
        # Foca na janela
        overlay.focus_force()
    
    def add_attribute_row(self, name_val="", value_val=""):
        frame = ctk.CTkFrame(self.attr_inner_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(frame, text="Nome:", font=("Segoe UI", 11)).pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(frame, width=180, height=35, placeholder_text="Ex: Strength")
        name_entry.pack(side="left", padx=5)
        if name_val:
            name_entry.insert(0, name_val)
        
        ctk.CTkLabel(frame, text="Valor:", font=("Segoe UI", 11)).pack(side="left", padx=5)
        value_entry = ctk.CTkEntry(frame, width=100, height=35, placeholder_text="Ex: 15")
        value_entry.pack(side="left", padx=5)
        if value_val:
            value_entry.insert(0, value_val)
        
        # Botão de excluir
        entry_dict = {
            'frame': frame,
            'name': name_entry,
            'value': value_entry
        }
        
        delete_btn = ctk.CTkButton(frame, text="X", width=36, height=36,
                                   fg_color="#7f1d1d", hover_color="#991b1b",
                                   text_color="white", font=("Segoe UI", 14, "bold"),
                                   command=lambda: self.remove_attribute_row(entry_dict))
        delete_btn.pack(side="left", padx=5)
        
        self.attr_entries.append(entry_dict)
        
        # Auto-save quando adicionar (exceto no carregamento inicial)
        if name_val or value_val:
            self.root.after(100, self.save_config)
    
    def remove_attribute_row(self, entry_dict):
        """Remove uma linha de atributo"""
        if len(self.attr_entries) <= 1:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos um atributo")
            return
        
        # Remove da lista
        self.attr_entries.remove(entry_dict)
        
        # Destroi o frame
        entry_dict['frame'].destroy()
        
        self.log(f"✓ Atributo removido")
        self.save_config()  # Salva após remover
    
    def add_search_row(self, name_val="", required_val=False):
        """Adiciona uma linha para atributo a procurar (sem valor)"""
        frame = ctk.CTkFrame(self.search_inner_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(frame, text="Nome:").pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(frame, width=180, placeholder_text="Ex: Critical Chance")
        name_entry.pack(side="left", padx=5)
        if name_val:
            name_entry.insert(0, name_val)
        
        # Checkbox para marcar como obrigatório
        required_var = tk.BooleanVar(value=required_val)
        required_check = ctk.CTkCheckBox(frame, text="⭐ Obrigatório", variable=required_var)
        required_check.pack(side="left", padx=10)
        
        # Botão de excluir
        entry_dict = {
            'frame': frame,
            'name': name_entry,
            'required': required_var
        }
        
        delete_btn = ctk.CTkButton(frame, text="X", width=36, height=36,
                                   fg_color="#7f1d1d", hover_color="#991b1b",
                                   text_color="white", font=("Segoe UI", 14, "bold"),
                                   command=lambda: self.remove_search_row(entry_dict))
        delete_btn.pack(side="left", padx=5)
        
        self.search_entries.append(entry_dict)
        
        # Auto-save quando adicionar
        if name_val:
            self.root.after(100, self.save_config)
    
    def remove_search_row(self, entry_dict):
        """Remove uma linha de atributo de busca"""
        if len(self.search_entries) <= 1:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos um atributo")
            return
        
        # Remove da lista
        self.search_entries.remove(entry_dict)
        
        # Destroi o frame
        entry_dict['frame'].destroy()
        
        self.log(f"✓ Atributo de busca removido")
        self.save_config()  # Salva após remover
    
    def add_keys_row(self, name_val="", required_val=False):
        """Adiciona uma linha para atributo desejado em chaves"""
        frame = ctk.CTkFrame(self.keys_inner_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5, padx=5)
        
        ctk.CTkLabel(frame, text="Nome:").pack(side="left", padx=5)
        name_entry = ctk.CTkEntry(frame, width=180, placeholder_text="Ex: Golden Realm")
        name_entry.pack(side="left", padx=5)
        if name_val:
            name_entry.insert(0, name_val)
        
        # Checkbox para marcar como obrigatório
        required_var = tk.BooleanVar(value=required_val)
        required_check = ctk.CTkCheckBox(frame, text="⭐ Obrigatório", variable=required_var)
        required_check.pack(side="left", padx=10)
        
        # Botão de excluir
        entry_dict = {
            'frame': frame,
            'name': name_entry,
            'required': required_var
        }
        
        delete_btn = ctk.CTkButton(frame, text="X", width=36, height=36,
                                   fg_color="#7f1d1d", hover_color="#991b1b",
                                   text_color="white", font=("Segoe UI", 14, "bold"),
                                   command=lambda: self.remove_keys_row(entry_dict))
        delete_btn.pack(side="left", padx=5)
        
        self.keys_entries.append(entry_dict)
        
        # Auto-save quando adicionar
        if name_val:
            self.root.after(100, self.save_config)
    
    def remove_keys_row(self, entry_dict):
        """Remove uma linha de atributo de chaves"""
        if len(self.keys_entries) <= 1:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos um atributo")
            return
        
        self.keys_entries.remove(entry_dict)
        entry_dict['frame'].destroy()
        
        self.log(f"✓ Atributo de chave removido")
        self.save_config()
    
    def capture_key_position(self):
        """Captura a posição do mouse para a chave"""
        self.log("Posicione o mouse sobre a CHAVE e pressione ENTER...")
        messagebox.showinfo("Capturar Posição da Chave", 
                           "Posicione o mouse sobre a CHAVE no inventário\ne pressione ENTER")
        
        def wait_for_enter():
            keyboard.wait('enter')
            self.key_position = pyautogui.position()
            self.key_pos_label.configure(text=f"X: {self.key_position[0]}, Y: {self.key_position[1]}", 
                                     text_color="#10b981")
            self.log(f"✓ Posição da chave: {self.key_position}")
            self.save_config()
        
        threading.Thread(target=wait_for_enter, daemon=True).start()
    
    def capture_orb_position(self):
        """Captura a posição do mouse para o Orb of Chance"""
        self.log("Posicione o mouse sobre o ORB OF CHANCE e pressione ENTER...")
        messagebox.showinfo("Capturar Posição do Orb", 
                           "Posicione o mouse sobre o ORB OF CHANCE\ne pressione ENTER")
        
        def wait_for_enter():
            keyboard.wait('enter')
            self.orb_position = pyautogui.position()
            self.orb_pos_label.configure(text=f"X: {self.orb_position[0]}, Y: {self.orb_position[1]}", 
                                     text_color="#10b981")
            self.log(f"✓ Posição do orb: {self.orb_position}")
            self.save_config()
        
        threading.Thread(target=wait_for_enter, daemon=True).start()
    
    def capture_bp_position(self):
        """Captura a posição do mouse para a BP destino"""
        self.log("Posicione o mouse sobre a BP (slot vazio) e pressione ENTER...")
        messagebox.showinfo("Capturar Posição da BP", 
                           "Posicione o mouse sobre um SLOT VAZIO na BP\ne pressione ENTER")
        
        def wait_for_enter():
            keyboard.wait('enter')
            self.bp_position = pyautogui.position()
            self.bp_pos_label.configure(text=f"X: {self.bp_position[0]}, Y: {self.bp_position[1]}", 
                                    text_color="#10b981")
            self.log(f"✓ Posição da BP: {self.bp_position}")
            self.save_config()
        
        threading.Thread(target=wait_for_enter, daemon=True).start()
        
    def test_capture(self):
        """Teste simples de captura (mantido para compatibilidade)"""
        self.test_capture_detailed()
    
    def test_capture_detailed(self):
        """Testa captura e mostra resultados detalhados no log"""
        if not self.region:
            messagebox.showwarning("Aviso", "Configure a região primeiro")
            self.log("⚠️ Configure a região antes de testar a captura")
            return
        
        try:
            self.log("🔍 Testando captura...")
            self.log_to_detail("\n" + "="*60, 'header')
            self.log_to_detail("🔍 TESTE DE CAPTURA", 'header')
            self.log_to_detail("="*60, 'header')
            
            # Captura a tela
            screenshot = ImageGrab.grab(bbox=self.region)
            text = pytesseract.image_to_string(screenshot, lang='eng')
            
            # Log do texto bruto
            self.log("=== Texto Capturado ===")
            self.log(text if text.strip() else "(vazio)")
            self.log("======================")
            
            self.log_to_detail(f"📄 Texto capturado (bruto):", 'info')
            self.log_to_detail(text if text.strip() else "(nenhum texto encontrado)", 'info')
            
            # Log linha por linha para debug
            lines = text.split('\n')
            self.log_to_detail(f"\n🔍 Análise linha por linha ({len([l for l in lines if l.strip()])} linhas):", 'info')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    self.log_to_detail(f"  Linha {i}: '{line.strip()}'", 'info')
            
            # Extrai valores
            current_values = self.extract_attributes_from_text(text)
            
            if current_values:
                # Separa atributos especiais (valor = 1) dos numéricos
                special_attrs = {k: v for k, v in current_values.items() if v == 1}
                numeric_attrs = {k: v for k, v in current_values.items() if v != 1}
                
                if special_attrs:
                    self.log_to_detail(f"\n⭐ Atributos especiais encontrados:", 'success')
                    for name in special_attrs.keys():
                        self.log_to_detail(f"  • {name.upper()}", 'success')
                        self.log(f"✓ {name.upper()}")
                
                if numeric_attrs:
                    self.log_to_detail(f"\n📊 Valores numéricos encontrados:", 'success')
                    for name, value in numeric_attrs.items():
                        self.log_to_detail(f"  • {name.upper()}: {value}", 'success')
                        self.log(f"✓ {name.upper()}: {value}")
                
                if not special_attrs and not numeric_attrs:
                    self.log_to_detail("⚠️ Nenhum atributo foi identificado no texto", 'warning')
                    self.log("⚠️ Nenhum atributo identificado")
            else:
                self.log_to_detail("⚠️ Nenhum atributo foi identificado no texto", 'warning')
                self.log("⚠️ Nenhum atributo identificado")
            
            # Verifica contra alvos definidos
            if current_values:
                self.log_to_detail(f"\n🎯 Comparação com valores alvo:", 'info')
                reached, message = self.check_target_reached(current_values)
                self.log_to_detail(message, 'success' if reached else 'warning')
            
            self.log_to_detail("\n" + "="*60, 'header')
            
            # Mostra resumo em popup
            if current_values:
                summary = "Valores encontrados:\n\n" + "\n".join([f"{k.upper()}: {v}" for k, v in current_values.items()])
            else:
                summary = "Nenhum valor numérico encontrado.\n\nTexto capturado:\n" + (text[:200] if text else "(vazio)")
            
            messagebox.showinfo("🔍 Teste de Captura", summary)
            
        except Exception as e:
            error_msg = f"Erro ao testar captura: {e}"
            self.log(error_msg)
            self.log_to_detail(f"❌ {error_msg}", 'error')
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")
    
    def extract_attributes_from_text(self, text):
        """Extrai valores numéricos do texto capturado"""
        attributes = {}
        
        # Atributos especiais conhecidos (sem valor numérico)
        special_attributes = {
            'golden realm': 1,
            'thunder realm': 1,
            'iced realm': 1,
            'tar realm': 1,
            'boss clone': 1
        }
        
        # Procura por padrões como "Physical Damage: +50%" ou "All Spells: +8"
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # PRIMEIRO: Verifica se é um dos 5 atributos especiais (case-insensitive)
            line_lower = line.lower()
            # Remove prefixos de tier se houver
            line_clean = re.sub(r'^t\d+\s+', '', line_lower, flags=re.IGNORECASE).strip()
            
            # Verifica exatamente contra os 5 atributos especiais
            found_special = False
            for special_name in special_attributes.keys():
                # Verifica se a linha limpa é exatamente o atributo especial
                if line_clean == special_name:
                    attributes[special_name] = 1
                    found_special = True
                    break
            
            # Se encontrou um atributo especial, pula para próxima linha
            if found_special:
                continue
            
            # Padrão 1: "Uma ou Mais Palavras: [+/-/4]dígitos[%]"
            # Captura "Physical Damage: +50%" ou "Holy Damage: +58%"
            match = re.search(r'([A-Za-z\s]+?)\s*:\s*[+\-4]?(\d{1,3})%?', line, re.IGNORECASE)
            if match:
                attr_name = match.group(1).strip()  # Remove espaços extras
                attr_value_str = match.group(2)
                attr_value = int(attr_value_str)
                
                # CORREÇÃO: OCR confunde "+" com "4" (ex: "+18" vira "418")
                # Se valor > 100 e começa com 4, provavelmente é um "+" mal lido
                if attr_value > 100 and attr_value_str.startswith('4'):
                    # Remove o primeiro dígito "4"
                    corrected_value = int(attr_value_str[1:]) if len(attr_value_str) > 1 else attr_value
                    if corrected_value <= 100:  # Se ficou razoável, usa o corrigido
                        attr_value = corrected_value
                # Ignora se o valor for muito alto (provavelmente erro de OCR)
                if attr_value < 500:  # Aumentado para aceitar percentuais
                    # Normaliza o nome (remove espaços extras e converte para minúsculas)
                    normalized_name = ' '.join(attr_name.lower().split())
                    # Remove prefixos de tier (T1-T9, tt, ts, t7, etc - qualquer "t" + caracteres até espaço)
                    normalized_name = re.sub(r'^t\S*\s+', '', normalized_name, flags=re.IGNORECASE)
                    # Remove dois pontos no final se houver (OCR pode adicionar)
                    normalized_name = normalized_name.rstrip(':')
                    
                    # Validações MELHORADAS para ignorar lixo do OCR
                    # Ignora se tiver muitas consoantes seguidas (provavelmente lixo)
                    if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', normalized_name):
                        continue
                    # Ignora se for muito curto (menos de 3 caracteres)
                    if len(normalized_name.replace(' ', '')) < 3:
                        continue
                    # Ignora padrões estranhos com letras soltas repetidas
                    if re.search(r'\b[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}', normalized_name):
                        continue
                    # Deve ter pelo menos uma palavra de 3+ letras
                    if not any(len(w) >= 3 for w in normalized_name.split()):
                        continue
                    
                    attributes[normalized_name] = attr_value
                continue
            
            # Padrão 2: "Uma ou Mais Palavras [+/-/4]valor" (sem dois pontos)
            match = re.search(r'([A-Za-z\s]+?)\s+[+\-4]?(\d{1,3})%?', line, re.IGNORECASE)
            if match:
                attr_name = match.group(1).strip()
                attr_value_str = match.group(2)
                attr_value = int(attr_value_str)
                
                # CORREÇÃO: OCR confunde "+" com "4" (ex: "+18" vira "418")
                if attr_value > 100 and attr_value_str.startswith('4'):
                    corrected_value = int(attr_value_str[1:]) if len(attr_value_str) > 1 else attr_value
                    if corrected_value <= 100:
                        attr_value = corrected_value
                if attr_value < 500:
                    normalized_name = ' '.join(attr_name.lower().split())
                    # Remove prefixos de tier (T1-T9, tt, ts, t7, etc - qualquer "t" + caracteres até espaço)
                    normalized_name = re.sub(r'^t\S*\s+', '', normalized_name, flags=re.IGNORECASE)
                    # Remove dois pontos no final se houver (OCR pode adicionar)
                    normalized_name = normalized_name.rstrip(':')
                    
                    # Validações MELHORADAS para ignorar lixo do OCR
                    # Ignora se tiver muitas consoantes seguidas (provavelmente lixo)
                    if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', normalized_name):
                        continue
                    # Ignora se for muito curto (menos de 3 caracteres)
                    if len(normalized_name.replace(' ', '')) < 3:
                        continue
                    # Ignora padrões estranhos com letras soltas repetidas
                    if re.search(r'\b[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}', normalized_name):
                        continue
                    # Deve ter pelo menos uma palavra de 3+ letras
                    if not any(len(w) >= 3 for w in normalized_name.split()):
                        continue
                    
                    attributes[normalized_name] = attr_value
                continue
            
            # Padrão 3: Outros atributos sem valor (já capturados acima os 5 especiais)
            # Agora tenta correções de OCR para atributos que não foram capturados
            if not re.search(r'\d', line):  # Se não tem dígitos
                # Remove possível lixo no início
                cleaned = line.strip()
                
                # Ignora linhas muito curtas (reduzido para 3)
                if len(cleaned) < 3:
                    continue
                
                # Ignora se não tiver pelo menos uma vogal
                if not re.search(r'[aeiou]', cleaned, re.IGNORECASE):
                    continue
                
                # Ignora se tiver muitas consoantes seguidas (reduzido para 6+)
                if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', cleaned, re.IGNORECASE):
                    continue
                
                # Ignora padrões estranhos como "a ee ae ee ee oll ney"
                if re.search(r'\b[a-z]{1,2}\b.*\b[a-z]{1,2}\b.*\b[a-z]{1,2}\b', cleaned, re.IGNORECASE):
                    # Exceto se for um padrão conhecido de OCR ruim de Tar Realm
                    if not re.search(r'(i+\s+r+\s*e+\s*r+|realm\s+le)', cleaned, re.IGNORECASE):
                        continue
                
                # Normaliza o nome
                normalized_name = ' '.join(cleaned.lower().split())
                
                # Remove prefixos de tier também nos atributos sem valor
                normalized_name = re.sub(r'^t\S*\s+', '', normalized_name, flags=re.IGNORECASE)
                
                # Correções de OCR comuns para atributos especiais
                ocr_corrections = {
                    'boss done': 'boss clone',
                    'boss dlone': 'boss clone',
                    'boss cione': 'boss clone',
                    'boss clone ea': 'boss clone',
                    'golden reaim': 'golden realm',
                    'goiden realm': 'golden realm',
                    'thunder reaim': 'thunder realm',
                    'tar reaim': 'tar realm',
                    'iced reaim': 'iced realm',
                    'realm le': 'tar realm',  # OCR confunde "Tar" 
                    'ig rer': 'tar realm',     # OCR confunde "Tar" 
                    'i rr rer': 'tar realm',   # OCR confunde "Tar"
                    'i rer': 'tar realm'       # OCR confunde "Tar"
                }
                
                # Aplica correções
                if normalized_name in ocr_corrections:
                    normalized_name = ocr_corrections[normalized_name]
                
                # Atributos booleanos conhecidos
                known_specials = ['golden realm', 'thunder realm', 'tar realm', 'iced realm', 'boss clone']
                
                # Correção por similaridade para atributos especiais (último recurso)
                if normalized_name not in known_specials:
                    # Verifica se contém "realm" ou palavras parecidas
                    if 'realm' in normalized_name or 'reaim' in normalized_name or 'clone' in normalized_name:
                        # Tenta identificar qual realm é
                        if any(x in normalized_name for x in ['tar', 'tai', 'ta ', 'tae', 'lr', 'rr']):
                            normalized_name = 'tar realm'
                        elif any(x in normalized_name for x in ['ice', 'iced', 'ic']):
                            normalized_name = 'iced realm'
                        elif any(x in normalized_name for x in ['thunder', 'thunde']):
                            normalized_name = 'thunder realm'
                        elif any(x in normalized_name for x in ['gold', 'golden', 'goiden']):
                            normalized_name = 'golden realm'
                        elif 'clone' in normalized_name or 'boss' in normalized_name:
                            normalized_name = 'boss clone'
                
                # Se é um atributo conhecido, adiciona sempre
                if normalized_name in known_specials:
                    attributes[normalized_name] = 1  # 1 = presente
                # Senão, se tem pelo menos 2 palavras, adiciona com valor 1 (presente)
                elif len(normalized_name.split()) >= 2:
                    attributes[normalized_name] = 1  # 1 = presente
        
        return attributes
    
    def check_target_reached(self, current_values):
        """Verifica se todos os atributos alvo foram atingidos (maior ou igual)"""
        all_reached = True
        details = []
        
        for entry in self.attr_entries:
            name = entry['name'].get().strip().lower()
            # Normaliza espaços múltiplos para um único espaço
            name = ' '.join(name.split())
            target = entry['value'].get().strip()
            
            if not name or not target:
                continue
            
            try:
                target_val = float(target)
                
                if name not in current_values:
                    all_reached = False
                    details.append(f"❌ {name.upper()}: NÃO ENCONTRADO (alvo: ≥{target_val})")
                    continue
                
                current_val = current_values[name]
                
                # Verifica se é maior ou igual
                if current_val >= target_val:
                    details.append(f"✅ {name.upper()}: {current_val} (alvo: ≥{target_val}) - ATINGIDO!")
                else:
                    all_reached = False
                    diff = target_val - current_val
                    details.append(f"⏳ {name.upper()}: {current_val} (falta: {diff:.1f} para {target_val})")
            except ValueError:
                continue
        
        status_msg = "\n".join(details)
        return all_reached, status_msg
    
    def check_attributes_found(self, current_values):
        """Verifica se os atributos desejados estão presentes (sem verificar valores)"""
        details = []
        
        # Separa atributos em obrigatórios e opcionais
        required_must_have = []  # Obrigatórios
        required_optional = []   # Opcionais
        
        for entry in self.search_entries:
            name = entry['name'].get().strip().lower()
            name = ' '.join(name.split())  # Normaliza espaços
            if name:
                is_required = entry['required'].get()
                if is_required:
                    required_must_have.append(name)
                else:
                    required_optional.append(name)
        
        all_attrs = required_must_have + required_optional
        
        if not all_attrs:
            return False, "❌ Nenhum atributo especificado para busca"
        
        # Conta quantos foram encontrados (separando obrigatórios e opcionais)
        found_must_have = []
        missing_must_have = []
        found_optional = []
        missing_optional = []
        
        # Verifica obrigatórios
        for attr_name in required_must_have:
            if attr_name in current_values:
                value = current_values[attr_name]
                found_must_have.append(attr_name)
                details.append(f"⭐ {attr_name.upper()}: {value} - OBRIGATÓRIO ENCONTRADO!")
            else:
                missing_must_have.append(attr_name)
                details.append(f"❌ {attr_name.upper()}: OBRIGATÓRIO NÃO ENCONTRADO")
        
        # Verifica opcionais
        for attr_name in required_optional:
            if attr_name in current_values:
                value = current_values[attr_name]
                found_optional.append(attr_name)
                details.append(f"✅ {attr_name.upper()}: {value} - ENCONTRADO!")
            else:
                missing_optional.append(attr_name)
                details.append(f"❌ {attr_name.upper()}: NÃO ENCONTRADO")
        
        # Total de encontrados
        total_found = len(found_must_have) + len(found_optional)
        
        # Verifica o modo (ALL ou MIN)
        mode = self.min_attributes_var.get()
        
        if mode == "ALL":
            # Modo TODOS: precisa ter todos os atributos
            success = (total_found == len(all_attrs))
            details.insert(0, f"📊 Modo: TODOS - Encontrados: {total_found}/{len(all_attrs)}")
        else:
            # Modo MIN: precisa ter TODOS os obrigatórios + mínimo X no total
            try:
                min_required = int(self.min_count_entry.get())
            except:
                min_required = 1
            
            # REGRA: Todos obrigatórios devem estar presentes E total >= mínimo
            all_must_have_found = (len(missing_must_have) == 0)
            enough_total = (total_found >= min_required)
            
            success = all_must_have_found and enough_total
            
            if required_must_have:
                details.insert(0, f"📊 Modo: MÍNIMO - Encontrados: {total_found}/{len(all_attrs)} " +
                              f"(precisa: {min_required}) | Obrigatórios: {len(found_must_have)}/{len(required_must_have)}")
            else:
                details.insert(0, f"📊 Modo: MÍNIMO - Encontrados: {total_found}/{len(all_attrs)} (precisa: {min_required})")
        
        # Mostra atributos extras que apareceram
        extra_attrs = []
        for found_attr in current_values.keys():
            if found_attr not in all_attrs:
                extra_attrs.append(f"  • {found_attr}: {current_values[found_attr]}")
        
        if extra_attrs:
            details.append("\n📋 Outros atributos presentes:")
            details.extend(extra_attrs)
        
        status_msg = "\n".join(details)
        return success, status_msg
    
    def open_log_window(self):
        """Abre uma janela separada com log detalhado"""
        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.log_window.lift()
            self.log_window.focus_force()
            return
        
        self.log_window = ctk.CTkToplevel(self.root)
        self.log_window.title("📊 Log Detalhado")
        self.log_window.geometry("750x500")
        self.log_window.attributes('-topmost', True)  # Sempre no topo
        
        # Frame principal com tema escuro
        frame = ctk.CTkFrame(self.log_window, fg_color="#1a1a1a")
        frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        header = ctk.CTkFrame(frame, fg_color="#2d2d2d", height=50)
        header.pack(fill="x", padx=10, pady=10)
        header.pack_propagate(False)
        
        ctk.CTkLabel(header, text="📊 Valores Capturados em Tempo Real", 
                    font=('Segoe UI', 16, 'bold'),
                    text_color="white").pack(side="left", padx=15, pady=10)
        
        # Botão minimizar (remove topmost)
        ctk.CTkButton(header, text="📌", width=40, height=30,
                     font=("Segoe UI", 14),
                     fg_color="#4b5563", hover_color="#374151",
                     text_color="white",
                     command=lambda: self.toggle_log_topmost()).pack(side="right", padx=5, pady=10)
        
        # Botão limpar
        ctk.CTkButton(header, text="🗑 Limpar", width=80, height=30,
                     font=("Segoe UI", 11),
                     fg_color="#7f1d1d", hover_color="#991b1b",
                     text_color="white",
                     command=self.clear_detail_log).pack(side="right", padx=5, pady=10)
        
        # Área de texto com tema escuro
        text_frame = ctk.CTkFrame(frame, fg_color="#1a1a1a")
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.detail_log = tk.Text(text_frame, wrap=tk.WORD, 
                                  font=('Consolas', 12),
                                  bg="#1e1e1e", fg="#e0e0e0",
                                  insertbackground="white",
                                  selectbackground="#3d5a80",
                                  relief="flat", padx=10, pady=10)
        
        scrollbar = ctk.CTkScrollbar(text_frame, command=self.detail_log.yview)
        self.detail_log.configure(yscrollcommand=scrollbar.set)
        
        self.detail_log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Configurar tags de cores para tema escuro
        self.detail_log.tag_config('success', foreground='#4ade80', font=('Consolas', 12, 'bold'))
        self.detail_log.tag_config('warning', foreground='#fbbf24', font=('Consolas', 12, 'bold'))
        self.detail_log.tag_config('error', foreground='#f87171', font=('Consolas', 12, 'bold'))
        self.detail_log.tag_config('info', foreground='#60a5fa', font=('Consolas', 12))
        self.detail_log.tag_config('header', foreground='#c084fc', font=('Consolas', 13, 'bold'))
        
        self.log_to_detail("Log detalhado iniciado.", 'info')
        self.log_to_detail("Os valores capturados aparecerão aqui em tempo real.", 'info')
    
    def toggle_log_topmost(self):
        """Alterna se a janela de log fica sempre no topo"""
        if self.log_window:
            current = self.log_window.attributes('-topmost')
            self.log_window.attributes('-topmost', not current)
    
    def clear_detail_log(self):
        """Limpa o log detalhado"""
        if self.detail_log:
            self.detail_log.delete(1.0, tk.END)
    
    def log_to_detail(self, message, tag='info'):
        """Adiciona mensagem na janela de log detalhado"""
        try:
            if self.log_window and tk.Toplevel.winfo_exists(self.log_window) and self.detail_log:
                timestamp = time.strftime("%H:%M:%S")
                self.detail_log.insert(tk.END, f"[{timestamp}] {message}\n", tag)
                self.detail_log.see(tk.END)
                self.log_window.update_idletasks()
        except:
            pass  # Ignora erros se janela foi fechada
    
    def automation_loop_values(self):
        """Loop de automação para busca por valores específicos"""
        delay = float(self.delay_var.get())
        max_attempts = int(self.max_attempts_var.get())
        click_delay = float(self.click_delay_var.get()) / 1000.0  # Converte ms para segundos
        attempts = 0
        
        self.log("Iniciando automação (Busca por VALORES específicos)...")
        self.log_to_detail("="*60, 'header')
        self.log_to_detail("🎯 AUTOMAÇÃO INICIADA - BUSCA POR VALORES", 'header')
        self.log_to_detail("="*60, 'header')
        
        while self.is_running and attempts < max_attempts:
            try:
                # Captura a tela
                screenshot = ImageGrab.grab(bbox=self.region)
                text = pytesseract.image_to_string(screenshot, lang='eng')
                
                # Extrai os valores
                current_values = self.extract_attributes_from_text(text)
                
                # Log dos valores capturados
                self.log_to_detail(f"\n--- Tentativa #{attempts + 1} ---", 'header')
                
                # Só continua se conseguiu identificar valores
                if not current_values:
                    self.log_to_detail("⏸️ Aguardando... Nenhum valor identificado na região", 'warning')
                    self.log_to_detail("Certifique-se de que os atributos estão visíveis na tela", 'warning')
                    time.sleep(0.5)  # Aguarda meio segundo antes de tentar novamente
                    continue  # Volta ao início do loop SEM fazer click
                
                # Valores identificados, mostra no log
                self.log_to_detail(f"✓ Valores capturados: {current_values}", 'info')
                
                # Verifica se atingiu o alvo
                reached, message = self.check_target_reached(current_values)
                
                # Mostra detalhes no log
                self.log_to_detail(message, 'success' if reached else 'warning')
                
                self.update_status(f"Tentativa {attempts + 1}: {'Atingido!' if reached else 'Continuando...'}")
                
                if reached:
                    self.log(f"✓ SUCESSO! Valores desejados atingidos após {attempts + 1} tentativas")
                    self.log_to_detail("\n" + "="*60, 'success')
                    self.log_to_detail("🎉 SUCESSO! TODOS OS VALORES ATINGIDOS!", 'success')
                    self.log_to_detail("="*60, 'success')
                    self.stop_automation()
                    messagebox.showinfo("Sucesso", f"Valores desejados atingidos!\n\nTentativas: {attempts + 1}")
                    break
                
                # Shift + Click (só executa se conseguiu identificar valores)
                current_pos = pyautogui.position()
                
                # Press e Release separados (mais próximo do AHK)
                keyboard.press('shift')
                time.sleep(click_delay)
                pyautogui.mouseDown(button='left')
                time.sleep(click_delay)
                pyautogui.mouseUp(button='left')
                time.sleep(click_delay)
                keyboard.release('shift')
                
                self.log_to_detail(f"🖱️ Shift+Click (orb mantido: {current_pos.x}, {current_pos.y}, delay: {int(click_delay*1000)}ms)...", 'info')
                attempts += 1
                
                # Aguarda um pouco para o jogo processar
                time.sleep(delay)
                
                # ⚡ VERIFICAÇÃO EXTRA: Captura imediatamente após o click para evitar passar do valor
                try:
                    screenshot_check = ImageGrab.grab(bbox=self.region)
                    text_check = pytesseract.image_to_string(screenshot_check, lang='eng')
                    values_check = self.extract_attributes_from_text(text_check)
                    
                    if values_check:
                        reached_check, message_check = self.check_target_reached(values_check)
                        
                        if reached_check:
                            self.log_to_detail(f"\n⚡ Verificação pós-click: {values_check}", 'info')
                            self.log_to_detail("🎉 VALORES ATINGIDOS após o último click!", 'success')
                            self.log(f"✓ SUCESSO! Valores desejados atingidos após {attempts} tentativas")
                            self.log_to_detail("\n" + "="*60, 'success')
                            self.log_to_detail("🎉 SUCESSO! TODOS OS VALORES ATINGIDOS!", 'success')
                            self.log_to_detail("="*60, 'success')
                            self.stop_automation()
                            messagebox.showinfo("Sucesso", f"Valores desejados atingidos!\n\nTentativas: {attempts}")
                            break
                except:
                    pass  # Se falhar a verificação extra, continua normalmente
                
            except Exception as e:
                self.log(f"Erro: {e}")
                self.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if attempts >= max_attempts:
            self.log(f"⚠ Número máximo de tentativas ({max_attempts}) atingido")
            self.log_to_detail(f"\n⚠️ Número máximo de tentativas ({max_attempts}) atingido sem sucesso", 'warning')
            self.stop_automation()
    
    def automation_loop_attributes(self):
        """Loop de automação para busca por presença de atributos"""
        delay = float(self.delay_var.get())
        max_attempts = int(self.max_attempts_var.get())
        click_delay = float(self.click_delay_var.get()) / 1000.0
        attempts = 0
        
        self.log("Iniciando automação (Busca por PRESENÇA de atributos)...")
        self.log_to_detail("="*60, 'header')
        self.log_to_detail("🔍 AUTOMAÇÃO INICIADA - BUSCA POR ATRIBUTOS", 'header')
        self.log_to_detail("="*60, 'header')
        
        while self.is_running and attempts < max_attempts:
            try:
                # Captura a tela
                screenshot = ImageGrab.grab(bbox=self.region)
                text = pytesseract.image_to_string(screenshot, lang='eng')
                
                # Extrai os valores
                current_values = self.extract_attributes_from_text(text)
                
                # Log dos valores capturados
                self.log_to_detail(f"\n--- Tentativa #{attempts + 1} ---", 'header')
                
                # Só continua se conseguiu identificar valores
                if not current_values:
                    self.log_to_detail("⏸️ Aguardando... Nenhum valor identificado na região", 'warning')
                    self.log_to_detail("Certifique-se de que os atributos estão visíveis na tela", 'warning')
                    time.sleep(0.5)
                    continue
                
                # Valores identificados
                self.log_to_detail(f"✓ Atributos encontrados: {list(current_values.keys())}", 'info')
                
                # Verifica se todos os atributos desejados foram encontrados
                found, message = self.check_attributes_found(current_values)
                
                # Mostra detalhes no log
                self.log_to_detail(message, 'success' if found else 'warning')
                
                self.update_status(f"Tentativa {attempts + 1}: {'Todos encontrados!' if found else 'Procurando...'}")
                
                if found:
                    self.log(f"✓ SUCESSO! Todos os atributos encontrados após {attempts + 1} tentativas")
                    self.log_to_detail("\n" + "="*60, 'success')
                    self.log_to_detail("🎉 SUCESSO! TODOS OS ATRIBUTOS ENCONTRADOS!", 'success')
                    self.log_to_detail("="*60, 'success')
                    self.stop_automation()
                    messagebox.showinfo("Sucesso", f"Todos os atributos encontrados!\n\nTentativas: {attempts + 1}")
                    break
                
                # Shift + Click
                current_pos = pyautogui.position()
                
                keyboard.press('shift')
                time.sleep(click_delay)
                pyautogui.mouseDown(button='left')
                time.sleep(click_delay)
                pyautogui.mouseUp(button='left')
                time.sleep(click_delay)
                keyboard.release('shift')
                
                self.log_to_detail(f"🖱️ Shift+Click (posição: {current_pos.x}, {current_pos.y})...", 'info')
                attempts += 1
                
                time.sleep(delay)
                
                # Verificação extra pós-click
                try:
                    screenshot_check = ImageGrab.grab(bbox=self.region)
                    text_check = pytesseract.image_to_string(screenshot_check, lang='eng')
                    values_check = self.extract_attributes_from_text(text_check)
                    
                    if values_check:
                        found_check, message_check = self.check_attributes_found(values_check)
                        
                        if found_check:
                            self.log_to_detail(f"\n⚡ Verificação pós-click: Todos encontrados!", 'success')
                            self.log(f"✓ SUCESSO! Todos os atributos encontrados após {attempts} tentativas")
                            self.log_to_detail("\n" + "="*60, 'success')
                            self.log_to_detail("🎉 SUCESSO! TODOS OS ATRIBUTOS ENCONTRADOS!", 'success')
                            self.log_to_detail("="*60, 'success')
                            self.stop_automation()
                            messagebox.showinfo("Sucesso", f"Todos os atributos encontrados!\n\nTentativas: {attempts}")
                            break
                except:
                    pass
                    
            except Exception as e:
                self.log(f"Erro: {e}")
                self.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if attempts >= max_attempts:
            self.log(f"⚠ Número máximo de tentativas ({max_attempts}) atingido")
            self.log_to_detail(f"\n⚠️ Número máximo de tentativas ({max_attempts}) atingido sem sucesso", 'warning')
            self.stop_automation()
    
    def automation_loop_keys(self):
        """Loop de automação para rolagem de chaves"""
        delay = float(self.delay_var.get())
        click_delay = float(self.click_delay_var.get()) / 1000.0
        
        keys_processed = 0
        empty_attempts = 0  # Contador de tentativas sem atributos (sem chaves)
        max_empty_attempts = 5
        
        self.log("Iniciando automação de CHAVES...")
        self.log_to_detail("="*60, 'header')
        self.log_to_detail("🔑 AUTOMAÇÃO DE CHAVES INICIADA", 'header')
        self.log_to_detail("="*60, 'header')
        self.log_to_detail("💡 DICA: Chaves sempre têm 6 atributos. Se OCR ler menos, ajuste a região de captura!", 'info')
        
        while self.is_running:
            try:
                # Log de início do ciclo
                self.log(f"🔍 Processando chave #{keys_processed + 1}...")
                self.log_to_detail(f"\n{'='*50}", 'header')
                self.log_to_detail(f"🔍 CHAVE #{keys_processed + 1}", 'header')
                self.log_to_detail(f"{'='*50}", 'header')
                
                # Verifica se ainda está rodando antes de cada ação
                if not self.is_running:
                    break
                
                # Move mouse para posição da chave para ver atributos
                pyautogui.moveTo(self.key_position[0], self.key_position[1])
                time.sleep(0.5)  # Aguarda tooltip aparecer completo
                
                if not self.is_running:
                    break
                
                # Captura atributos da chave atual
                self.log_to_detail("📸 Capturando atributos...", 'info')
                screenshot = ImageGrab.grab(bbox=self.region)
                
                # Tenta primeiro com imagem normal
                text = pytesseract.image_to_string(screenshot, lang='eng')
                current_values = self.extract_attributes_from_text(text)
                
                # Se leu menos de 6, tenta com processamento de imagem
                if not current_values or len(current_values) < 6:
                    self.log_to_detail(f"  ⚠️ Leu apenas {len(current_values) if current_values else 0}/6, processando imagem...", 'warning')
                    time.sleep(0.3)
                    screenshot = ImageGrab.grab(bbox=self.region)
                    
                    # Tenta múltiplas configurações
                    best_values = current_values if current_values else {}
                    
                    # Tentativa 1: Escala de cinza + contraste alto
                    screenshot_gray = screenshot.convert('L')
                    enhancer = ImageEnhance.Contrast(screenshot_gray)
                    screenshot_enhanced = enhancer.enhance(2.5)
                    text_enhanced = pytesseract.image_to_string(screenshot_enhanced, lang='eng', config='--psm 6')
                    retry_values = self.extract_attributes_from_text(text_enhanced)
                    if len(retry_values) > len(best_values):
                        best_values = retry_values
                    
                    # Tentativa 2: Brightness aumentado
                    if len(best_values) < 6:
                        brightness = ImageEnhance.Brightness(screenshot_gray)
                        screenshot_bright = brightness.enhance(1.5)
                        text_bright = pytesseract.image_to_string(screenshot_bright, lang='eng', config='--psm 6')
                        retry_values2 = self.extract_attributes_from_text(text_bright)
                        if len(retry_values2) > len(best_values):
                            best_values = retry_values2
                    
                    # Tentativa 3: Inversão (branco em preto) - para texto laranja
                    if len(best_values) < 6:
                        inverted = ImageOps.invert(screenshot_gray)
                        enhancer_inv = ImageEnhance.Contrast(inverted)
                        inverted_contrast = enhancer_inv.enhance(3.0)
                        text_inv = pytesseract.image_to_string(inverted_contrast, lang='eng', config='--psm 6')
                        retry_values3 = self.extract_attributes_from_text(text_inv)
                        if len(retry_values3) > len(best_values):
                            best_values = retry_values3
                    
                    current_values = best_values
                    self.log_to_detail(f"  ✓ Com processamento capturou {len(current_values)}/6 atributos", 'info')
                    
                    # Log dos atributos capturados para debug
                    if len(current_values) < 6:
                        attrs_captured = list(current_values.keys())
                        self.log_to_detail(f"  📋 Atributos lidos: {attrs_captured}", 'info')
                
                # Se não conseguiu ler atributos, provavelmente acabaram as chaves
                if not current_values:
                    empty_attempts += 1
                    self.log_to_detail(f"⚠️ Nenhum atributo detectado (tentativa {empty_attempts}/{max_empty_attempts})", 'warning')
                    
                    if empty_attempts >= max_empty_attempts:
                        self.log("⚠️ Chaves acabaram (sem atributos detectados após 5 tentativas)")
                        self.log_to_detail("\n" + "="*60, 'warning')
                        self.log_to_detail("⚠️ CHAVES ACABARAM - Sem atributos detectados", 'warning')
                        self.log_to_detail("="*60, 'warning')
                        self.stop_automation()
                        messagebox.showinfo("Automação Concluída", 
                                           f"Chaves processadas: {keys_processed}\n\n" +
                                           "Não foi possível detectar mais atributos.\n" +
                                           "Provavelmente as chaves acabaram.")
                        break
                    
                    time.sleep(delay)
                    continue
                
                # Resetar contador de tentativas vazias
                empty_attempts = 0
                
                # Valores identificados
                self.log_to_detail(f"✓ Atributos da chave: {list(current_values.keys())}", 'info')
                
                # Verifica se tem os atributos desejados
                found, message = self.check_keys_attributes(current_values)
                self.log_to_detail(message, 'success' if found else 'warning')
                
                if found:
                    # Verifica se ainda está rodando antes de mover
                    if not self.is_running:
                        break
                    
                    # CHAVE BOA! Mover para BP
                    self.log("🎉 CHAVE COM ATRIBUTOS DESEJADOS! Movendo para BP...")
                    self.log_to_detail("🎉 CHAVE PERFEITA! Movendo para BP...", 'success')
                    
                    # Clica com botão direito primeiro para deselecionar o orb
                    pyautogui.click(button='right')
                    time.sleep(0.15)
                    
                    if not self.is_running:
                        break
                    
                    # Drag and drop: Chave -> BP
                    pyautogui.moveTo(self.key_position[0], self.key_position[1])
                    time.sleep(0.1)
                    pyautogui.mouseDown(button='left')
                    time.sleep(0.1)
                    pyautogui.moveTo(self.bp_position[0], self.bp_position[1], duration=0.3)
                    time.sleep(0.1)
                    pyautogui.mouseUp(button='left')
                    
                    self.log_to_detail(f"✓ Chave movida para BP (slot: {self.bp_position})", 'success')
                    keys_processed += 1
                    
                    # Volta mouse para posição da chave (próxima chave)
                    time.sleep(0.3)
                    pyautogui.moveTo(self.key_position[0], self.key_position[1])
                    
                    self.update_status(f"Chaves processadas: {keys_processed}")
                    time.sleep(delay)
                    
                else:
                    # CHAVE RUIM - Rolar com Orb of Chance
                    self.log_to_detail("❌ Atributos não desejados. Rolando com Orb...", 'info')
                    
                    # Clicar direito no Orb of Chance
                    pyautogui.moveTo(self.orb_position[0], self.orb_position[1])
                    time.sleep(0.1)
                    pyautogui.click(button='right')
                    time.sleep(0.2)
                    
                    self.log_to_detail(f"🔮 Clique direito no Orb (pos: {self.orb_position})", 'info')
                    
                    # Loop de Shift+Click na chave até conseguir atributos
                    max_roll_attempts = 100  # Máximo de tentativas de rolagem por chave
                    roll_attempt = 0
                    
                    self.log(f"🔄 Iniciando rolagem... (máx {max_roll_attempts} tentativas)")
                    self.log_to_detail(f"🔄 Rolando chave com Orb (máx {max_roll_attempts} tentativas)...", 'info')
                    
                    while self.is_running and roll_attempt < max_roll_attempts:
                        # Verifica se ainda está rodando
                        if not self.is_running:
                            break
                        
                        # Move para chave e faz Shift+Click para rolar
                        pyautogui.moveTo(self.key_position[0], self.key_position[1])
                        time.sleep(0.05)
                        
                        keyboard.press('shift')
                        time.sleep(click_delay)
                        pyautogui.mouseDown(button='left')
                        time.sleep(click_delay)
                        pyautogui.mouseUp(button='left')
                        time.sleep(click_delay)
                        keyboard.release('shift')
                        
                        roll_attempt += 1
                        
                        # Aguarda um pouco para os atributos atualizarem
                        time.sleep(delay)
                        
                        # Verifica novamente após o delay
                        if not self.is_running:
                            break
                        
                        # Move mouse para posição da chave para ler atributos
                        pyautogui.moveTo(self.key_position[0], self.key_position[1])
                        time.sleep(0.5)  # Aguarda mais tempo para tooltip aparecer completo
                        
                        # VERIFICA ATRIBUTOS A CADA ROLAGEM
                        screenshot_check = ImageGrab.grab(bbox=self.region)
                        text_check = pytesseract.image_to_string(screenshot_check, lang='eng')
                        values_check = self.extract_attributes_from_text(text_check)
                        
                        # Se leu menos de 6, tenta com processamento de imagem
                        if not values_check or len(values_check) < 6:
                            time.sleep(0.2)
                            screenshot_check = ImageGrab.grab(bbox=self.region)
                            
                            # Tenta múltiplas configurações
                            best_check = values_check if values_check else {}
                            
                            # Config 1: Contraste alto
                            screenshot_gray = screenshot_check.convert('L')
                            enhancer = ImageEnhance.Contrast(screenshot_gray)
                            screenshot_enhanced = enhancer.enhance(2.5)
                            text_check = pytesseract.image_to_string(screenshot_enhanced, lang='eng', config='--psm 6')
                            retry1 = self.extract_attributes_from_text(text_check)
                            if len(retry1) > len(best_check):
                                best_check = retry1
                            
                            # Config 2: Brilho aumentado (se ainda não tem 6)
                            if len(best_check) < 6:
                                brightness = ImageEnhance.Brightness(screenshot_gray)
                                screenshot_bright = brightness.enhance(1.5)
                                text_bright = pytesseract.image_to_string(screenshot_bright, lang='eng', config='--psm 6')
                                retry2 = self.extract_attributes_from_text(text_bright)
                                if len(retry2) > len(best_check):
                                    best_check = retry2
                            
                            # Config 3: Inversão (para texto laranja/amarelo em fundo escuro)
                            if len(best_check) < 6:
                                inverted = ImageOps.invert(screenshot_gray)
                                enhancer_inv = ImageEnhance.Contrast(inverted)
                                inverted_contrast = enhancer_inv.enhance(3.0)
                                text_inv = pytesseract.image_to_string(inverted_contrast, lang='eng', config='--psm 6')
                                retry3 = self.extract_attributes_from_text(text_inv)
                                if len(retry3) > len(best_check):
                                    best_check = retry3
                            
                            values_check = best_check
                            if roll_attempt % 10 == 0 and len(best_check) > 0:
                                self.log_to_detail(f"  🔄 Processamento: {len(values_check)}/6 atributos", 'info')
                        
                        # CHECAGEM E LOG A CADA ROLAGEM
                        if values_check:
                            found_check, msg = self.check_keys_attributes(values_check)
                            
                            # LOG DE CADA TENTATIVA
                            attrs_list = list(values_check.keys())
                            
                            # Aviso se não leu 6 atributos (chaves sempre têm 6)
                            if len(attrs_list) < 6 and roll_attempt % 5 == 0:
                                self.log_to_detail(f"  ⚠️ OCR leu apenas {len(attrs_list)}/6 atributos - pode ter perdido algum!", 'warning')
                            
                            # Verifica se tem algum atributo da lista desejada
                            desired_attrs = [entry['name'].get().strip().lower() for entry in self.keys_entries if entry['name'].get().strip()]
                            matching = [a for a in attrs_list if any(d in a.lower() or a.lower() in d for d in desired_attrs)]
                            
                            # Mostra TODAS as tentativas
                            if matching:
                                # Tem atributo da lista, mas verifica se atende o critério
                                if found_check:
                                    self.log(f"🎉 Roll #{roll_attempt}: {matching} ← CRITÉRIO ATENDIDO!")
                                    self.log_to_detail(f"🎉 Roll #{roll_attempt}/{max_roll_attempts}: {attrs_list} ← ATENDE CRITÉRIO!", 'success')
                                else:
                                    # Tem atributo mas não atende critério completo - explica POR QUE
                                    # Extrai informações do critério
                                    total_found = len([a for a in attrs_list if any(d in a.lower() or a.lower() in d for d in desired_attrs)])
                                    total_needed = len(desired_attrs)
                                    
                                    # Verifica se tem o obrigatório
                                    obrigatorio_nome = [entry['name'].get().strip() for entry in self.keys_entries if entry['required'].get()]
                                    tem_obrigatorio = any(any(obrig.lower() in a.lower() or a.lower() in obrig.lower() for a in attrs_list) for obrig in obrigatorio_nome)
                                    
                                    if not tem_obrigatorio and obrigatorio_nome:
                                        falta_msg = f"FALTA OBRIGATÓRIO ({obrigatorio_nome[0]})"
                                    else:
                                        falta_msg = f"Tem obrigatório mas falta {2 - total_found} atributo(s) para mínimo de 2"
                                    
                                    self.log(f"⚡ Roll #{roll_attempt}: {matching} ← {falta_msg}")
                                    self.log_to_detail(f"⚡ Roll #{roll_attempt}/{max_roll_attempts}: {attrs_list}", 'warning')
                                    self.log_to_detail(f"   ↳ {falta_msg}", 'warning')
                            else:
                                if roll_attempt % 10 == 0:
                                    self.log(f"🔄 Roll #{roll_attempt}/{max_roll_attempts}: {attrs_list[:3]}...")
                                self.log_to_detail(f"  Roll #{roll_attempt}: {attrs_list}", 'info')
                            
                            # VERIFICA SE ENCONTROU OS ATRIBUTOS BONS (A CADA TENTATIVA!)
                            if found_check:
                                # Verifica se ainda está rodando antes de mover
                                if not self.is_running:
                                    break
                                
                                self.log(f"🎉 ATRIBUTOS CONSEGUIDOS após {roll_attempt} rolagens!")
                                self.log_to_detail(f"🎉 SUCESSO após {roll_attempt} rolagens!", 'success')
                                self.log_to_detail(msg, 'success')
                                
                                # Clica com botão direito primeiro para deselecionar o orb
                                pyautogui.click(button='right')
                                time.sleep(0.15)
                                
                                if not self.is_running:
                                    break
                                
                                # Mover para BP
                                self.log_to_detail("📦 Movendo chave para BP...", 'info')
                                pyautogui.moveTo(self.key_position[0], self.key_position[1])
                                time.sleep(0.1)
                                pyautogui.mouseDown(button='left')
                                time.sleep(0.1)
                                pyautogui.moveTo(self.bp_position[0], self.bp_position[1], duration=0.3)
                                time.sleep(0.1)
                                pyautogui.mouseUp(button='left')
                                
                                self.log("✓ Chave BOA salva na BP!")
                                self.log_to_detail(f"✓ Chave movida para BP (slot: {self.bp_position})", 'success')
                                keys_processed += 1
                                
                                # Volta para posição da chave
                                time.sleep(0.3)
                                pyautogui.moveTo(self.key_position[0], self.key_position[1])
                                
                                self.update_status(f"✓ Chaves boas: {keys_processed}", 'success')
                                break
                        else:
                            # Sem atributos
                            self.log_to_detail(f"  Roll #{roll_attempt}: ⚠️ SEM ATRIBUTOS", 'warning')
                    
                    # Se saiu do loop sem encontrar
                    if roll_attempt >= max_roll_attempts:
                        self.log(f"⚠️ Não conseguiu atributos bons após {max_roll_attempts} tentativas. Próxima chave...")
                        self.log_to_detail(f"⚠️ Limite de {max_roll_attempts} rolagens atingido. Próxima chave...", 'warning')
                    
                    # Pequeno delay antes da próxima chave
                    time.sleep(delay * 0.5)
                    
            except Exception as e:
                self.log(f"Erro: {e}")
                self.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        # Finalização
        if keys_processed > 0:
            self.log(f"✓ Automação concluída! {keys_processed} chave(s) com bons atributos processada(s)")
            self.log_to_detail(f"\n✓ Total de chaves processadas: {keys_processed}", 'success')
    
    def check_keys_attributes(self, current_values):
        """Verifica se a chave tem os atributos desejados (similar a check_attributes_found)"""
        # Separa atributos em obrigatórios e opcionais
        required_must_have = []  # Obrigatórios
        required_optional = []   # Opcionais
        
        for entry in self.keys_entries:
            name = entry['name'].get().strip().lower()
            name = ' '.join(name.split())
            if name:
                is_required = entry['required'].get()
                if is_required:
                    required_must_have.append(name)
                else:
                    required_optional.append(name)
        
        all_attrs = required_must_have + required_optional
        
        if not all_attrs:
            return False, "Nenhum atributo configurado"
        
        # Conta quantos foram encontrados (separando obrigatórios e opcionais)
        found_must_have = []
        missing_must_have = []
        found_optional = []
        missing_optional = []
        details = []
        
        # Normaliza os nomes dos atributos encontrados para comparação
        normalized_current = {}
        for k, v in current_values.items():
            normalized_key = k.lower().strip()
            normalized_current[normalized_key] = v
        
        # Verifica obrigatórios
        for attr_name in required_must_have:
            # Busca exata ou parcial
            found_value = None
            for current_key, current_val in normalized_current.items():
                if attr_name in current_key or current_key in attr_name:
                    found_value = current_val
                    break
            
            if found_value is not None:
                found_must_have.append(attr_name)
                details.append(f"⭐ {attr_name.upper()}: {found_value} - OBRIGATÓRIO ENCONTRADO!")
            else:
                missing_must_have.append(attr_name)
                details.append(f"❌ {attr_name.upper()}: OBRIGATÓRIO NÃO ENCONTRADO")
        
        # Verifica opcionais
        for attr_name in required_optional:
            # Busca exata ou parcial
            found_value = None
            for current_key, current_val in normalized_current.items():
                if attr_name in current_key or current_key in attr_name:
                    found_value = current_val
                    break
            
            if found_value is not None:
                found_optional.append(attr_name)
                details.append(f"✅ {attr_name.upper()}: {found_value} - ENCONTRADO!")
            else:
                missing_optional.append(attr_name)
                details.append(f"❌ {attr_name.upper()}: NÃO ENCONTRADO")
        
        # Total de encontrados
        total_found = len(found_must_have) + len(found_optional)
        
        # Verifica modo (ALL ou MIN)
        mode = self.keys_min_var.get()
        
        if mode == "ALL":
            success = (total_found == len(all_attrs))
            details.insert(0, f"📊 Modo: TODOS - Encontrados: {total_found}/{len(all_attrs)}")
        else:
            try:
                min_required = int(self.keys_min_count.get())
            except:
                min_required = 1
            
            # REGRA: Todos obrigatórios devem estar presentes E total >= mínimo
            all_must_have_found = (len(missing_must_have) == 0)
            enough_total = (total_found >= min_required)
            
            success = all_must_have_found and enough_total
            
            if required_must_have:
                details.insert(0, f"📊 Modo: MÍNIMO - Encontrados: {total_found}/{len(all_attrs)} " +
                              f"(precisa: {min_required}) | Obrigatórios: {len(found_must_have)}/{len(required_must_have)}")
            else:
                details.insert(0, f"📊 Modo: MÍNIMO - Encontrados: {total_found}/{len(all_attrs)} (precisa: {min_required})")
        
        # Lista outros atributos presentes
        other_attrs = []
        for attr_name, attr_value in current_values.items():
            if attr_name not in all_attrs:
                other_attrs.append(f"  • {attr_name}: {attr_value}")
        
        if other_attrs:
            details.append("\n📋 Outros atributos presentes:")
            details.extend(other_attrs)
        
        status_msg = "\n".join(details)
        return success, status_msg
    
    def save_config(self):
        """Salva configurações em arquivo JSON"""
        try:
            # Salva qual aba estava ativa (CustomTkinter)
            active_tab_name = self.tabview.get()
            if active_tab_name == "🎯 Valores Específicos":
                active_tab = 0
            elif active_tab_name == "🔍 Busca de Atributos":
                active_tab = 1
            else:  # "🔑 Automação de Chaves"
                active_tab = 2
            
            config = {
                'region': self.region,
                'attributes': [],
                'search_attributes': [],
                'keys_attributes': [],
                'delay': self.delay_var.get(),
                'click_delay': self.click_delay_var.get(),
                'max_attempts': self.max_attempts_var.get(),
                'active_tab': active_tab,
                'min_attributes_mode': self.min_attributes_var.get(),
                'min_attributes_count': self.min_count_entry.get(),
                'keys_min_mode': self.keys_min_var.get(),
                'keys_min_count': self.keys_min_count.get(),
                'key_position': self.key_position,
                'orb_position': self.orb_position,
                'bp_position': self.bp_position,
                'hotkeys': self.hotkeys  # Salva atalhos personalizados
            }
            
            # Salva atributos (aba 1 - valores específicos)
            for entry in self.attr_entries:
                name = entry['name'].get().strip()
                value = entry['value'].get().strip()
                if name and value:
                    config['attributes'].append({
                        'name': name,
                        'value': value
                    })
            
            # Salva atributos de busca (aba 2 - presença)
            for entry in self.search_entries:
                name = entry['name'].get().strip()
                if name:
                    config['search_attributes'].append({
                        'name': name,
                        'required': entry['required'].get()
                    })
            
            # Salva atributos de chaves (aba 3 - automação de chaves)
            for entry in self.keys_entries:
                name = entry['name'].get().strip()
                if name:
                    config['keys_attributes'].append({
                        'name': name,
                        'required': entry['required'].get()
                    })
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.log(f"⚠️ Erro ao salvar configurações: {e}")
    
    def load_config(self):
        """Carrega configurações do arquivo JSON"""
        try:
            if not os.path.exists(CONFIG_FILE):
                self.log("📋 Nenhuma configuração anterior encontrada")
                return
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Carrega região
            if config.get('region'):
                self.region = tuple(config['region'])
                left, top, right, bottom = self.region
                self.region_label.configure(
                    text=f"✓ Região configurada: {right-left}x{bottom-top}px | ({left}, {top}) → ({right}, {bottom})",
                    text_color=self.colors['success']
                )
            
            # Carrega delays e tentativas
            if config.get('delay'):
                self.delay_var.set(config['delay'])
            if config.get('click_delay'):
                self.click_delay_var.set(config['click_delay'])
            if config.get('max_attempts'):
                self.max_attempts_var.set(config['max_attempts'])
            
            # Carrega atributos (aba 1)
            if config.get('attributes'):
                # Remove a linha padrão vazia
                if len(self.attr_entries) == 1:
                    first_entry = self.attr_entries[0]
                    if not first_entry['name'].get() and not first_entry['value'].get():
                        first_entry['frame'].destroy()
                        self.attr_entries.clear()
                
                # Adiciona os atributos salvos
                for attr in config['attributes']:
                    self.add_attribute_row(attr['name'], attr['value'])
                
                self.log(f"✓ Aba 1: {len(config['attributes'])} atributo(s) com valores carregados")
            
            # Carrega atributos de busca (aba 2)
            if config.get('search_attributes'):
                # Remove a linha padrão vazia
                if len(self.search_entries) == 1:
                    first_entry = self.search_entries[0]
                    if not first_entry['name'].get():
                        first_entry['frame'].destroy()
                        self.search_entries.clear()
                
                # Adiciona os atributos de busca salvos
                for attr_data in config['search_attributes']:
                    # Compatibilidade: aceita formato antigo (string) e novo (dict)
                    if isinstance(attr_data, str):
                        self.add_search_row(attr_data, False)
                    else:
                        self.add_search_row(attr_data.get('name', ''), attr_data.get('required', False))
                
                self.log(f"✓ Aba 2: {len(config['search_attributes'])} atributo(s) de busca carregados")
            
            # Carrega configurações de modo mínimo (aba 2)
            if config.get('min_attributes_mode'):
                self.min_attributes_var.set(config['min_attributes_mode'])
            if config.get('min_attributes_count'):
                self.min_count_entry.delete(0, "end")
                self.min_count_entry.insert(0, config['min_attributes_count'])
            
            # Carrega atributos de chaves (aba 3)
            if config.get('keys_attributes'):
                # Remove a linha padrão vazia
                if len(self.keys_entries) == 1:
                    first_entry = self.keys_entries[0]
                    if not first_entry['name'].get():
                        first_entry['frame'].destroy()
                        self.keys_entries.clear()
                
                # Adiciona os atributos de chaves salvos
                for attr_data in config['keys_attributes']:
                    # Compatibilidade: aceita formato antigo (string) e novo (dict)
                    if isinstance(attr_data, str):
                        self.add_keys_row(attr_data, False)
                    else:
                        self.add_keys_row(attr_data.get('name', ''), attr_data.get('required', False))
                
                self.log(f"✓ Aba 3: {len(config['keys_attributes'])} atributo(s) de chaves carregados")
            
            # Carrega configurações de modo mínimo (aba 3)
            if config.get('keys_min_mode'):
                self.keys_min_var.set(config['keys_min_mode'])
            if config.get('keys_min_count'):
                self.keys_min_count.delete(0, "end")
                self.keys_min_count.insert(0, config['keys_min_count'])
            
            # Carrega posições (aba 3)
            if config.get('key_position'):
                self.key_position = tuple(config['key_position'])
                self.key_pos_label.configure(
                    text=f"X: {self.key_position[0]}, Y: {self.key_position[1]}", 
                    text_color="#10b981"
                )
            
            if config.get('orb_position'):
                self.orb_position = tuple(config['orb_position'])
                self.orb_pos_label.configure(
                    text=f"X: {self.orb_position[0]}, Y: {self.orb_position[1]}", 
                    text_color="#10b981"
                )
            
            if config.get('bp_position'):
                self.bp_position = tuple(config['bp_position'])
                self.bp_pos_label.configure(
                    text=f"X: {self.bp_position[0]}, Y: {self.bp_position[1]}", 
                    text_color="#10b981"
                )
            
            # Restaura a aba que estava ativa
            if config.get('active_tab') is not None:
                try:
                    tab_names = ["🎯 Valores Específicos", "🔍 Busca de Atributos", "🔑 Automação de Chaves"]
                    active_tab_idx = config['active_tab']
                    if 0 <= active_tab_idx < len(tab_names):
                        self.tabview.set(tab_names[active_tab_idx])
                        self.log(f"✓ Aba restaurada: {tab_names[active_tab_idx]}")
                except:
                    pass  # Se falhar, mantém a aba padrão
            
            # Carrega atalhos personalizados
            if config.get('hotkeys'):
                self.hotkeys = config['hotkeys']
                self.update_hotkey_labels()
                self.log(f"✓ Atalhos carregados: {self.hotkeys['region']}/{self.hotkeys['test']}/{self.hotkeys['start']}/{self.hotkeys['stop']}")
            
            # Carrega lista de presets nos combos
            self.update_preset_combos()
            
        except Exception as e:
            self.log(f"⚠️ Erro ao carregar configurações: {e}")
    
    def on_closing(self):
        """Chamado ao fechar a janela"""
        self.save_config()
        self.log("💾 Configurações salvas")
        self.root.destroy()
    
    # ============================================
    # MÉTODOS DE AUTO-ATUALIZAÇÃO
    # ============================================
    
    def check_updates_on_start(self):
        """Verifica atualizações ao iniciar (em thread separada)"""
        def check():
            try:
                updater = AutoUpdater(APP_VERSION, GITHUB_REPO)
                result = updater.check_for_updates()
                
                if result.get('available'):
                    self.root.after(0, lambda: self.show_update_dialog(result, updater))
                else:
                    self.log(f"✓ Versão atual: {APP_VERSION} (atualizado)")
            except Exception as e:
                self.log(f"⚠️ Não foi possível verificar atualizações: {e}")
        
        # Verifica em thread separada para não travar a UI
        threading.Thread(target=check, daemon=True).start()
    
    def check_updates_manual(self):
        """Verifica atualizações manualmente (botão)"""
        self.log("🔍 Verificando atualizações...")
        
        def check():
            updater = AutoUpdater(APP_VERSION, GITHUB_REPO)
            result = updater.check_for_updates()
            
            if result.get('available'):
                self.root.after(0, lambda: self.show_update_dialog(result, updater))
            elif result.get('error'):
                self.root.after(0, lambda: messagebox.showerror(
                    "Erro", f"Não foi possível verificar atualizações:\n{result['error']}"))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "✓ Atualizado", f"Você já está na versão mais recente!\n\nVersão: {APP_VERSION}"))
                self.log(f"✓ Versão {APP_VERSION} é a mais recente")
        
        threading.Thread(target=check, daemon=True).start()
    
    def show_update_dialog(self, update_info, updater):
        """Mostra diálogo de atualização disponível"""
        # Limita o tamanho das notas de atualização
        notes = update_info.get('release_notes', 'Sem notas de atualização')
        if len(notes) > 500:
            notes = notes[:500] + "..."
        
        msg = f"""🎉 Nova versão disponível!

📌 Versão atual: {APP_VERSION}
🆕 Nova versão: {update_info['version']}

📝 Notas da atualização:
{notes}

Deseja atualizar agora?"""
        
        if messagebox.askyesno("🔄 Atualização Disponível", msg):
            if update_info.get('download_url'):
                self.perform_update(updater, update_info['download_url'])
            else:
                messagebox.showerror("Erro", "URL de download não encontrada na release.")
    
    def perform_update(self, updater, download_url):
        """Executa o processo de atualização"""
        # Cria janela de progresso
        progress_window = ctk.CTkToplevel(self.root)
        progress_window.title("🔄 Atualizando...")
        progress_window.geometry("450x180")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Centraliza a janela
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (225)
        y = (progress_window.winfo_screenheight() // 2) - (90)
        progress_window.geometry(f"+{x}+{y}")
        
        # Conteúdo
        ctk.CTkLabel(progress_window, text="📥 Baixando atualização...",
                    font=("Segoe UI", 16, "bold")).pack(pady=(25, 15))
        
        progress_bar = ctk.CTkProgressBar(progress_window, width=380, height=20)
        progress_bar.pack(pady=10)
        progress_bar.set(0)
        
        progress_label = ctk.CTkLabel(progress_window, text="0%", font=("Segoe UI", 12))
        progress_label.pack(pady=5)
        
        status_label = ctk.CTkLabel(progress_window, text="Conectando ao servidor...",
                                   font=("Segoe UI", 10), text_color="gray60")
        status_label.pack(pady=5)
        
        def update_progress(percent):
            try:
                progress_bar.set(percent / 100)
                progress_label.configure(text=f"{percent}%")
                if percent < 100:
                    status_label.configure(text="Baixando arquivo...")
                else:
                    status_label.configure(text="Instalando atualização...")
                progress_window.update()
            except:
                pass
        
        def do_update():
            success = updater.download_and_install(download_url, update_progress)
            if success:
                self.root.after(100, lambda: self.finish_update(progress_window))
            else:
                self.root.after(0, lambda: self.update_failed(progress_window))
        
        threading.Thread(target=do_update, daemon=True).start()
    
    def finish_update(self, progress_window):
        """Finaliza a atualização e fecha o programa"""
        try:
            progress_window.destroy()
        except:
            pass
        
        messagebox.showinfo("✓ Atualização", 
                          "Atualização baixada com sucesso!\n\nO programa será reiniciado.")
        self.root.quit()
    
    def update_failed(self, progress_window):
        """Trata falha na atualização"""
        try:
            progress_window.destroy()
        except:
            pass
        
        messagebox.showerror("Erro", 
                            "Falha ao instalar atualização.\n\nTente novamente mais tarde.")
    
    def start_automation(self):
        # Se já está rodando, não permite iniciar novamente
        if self.is_running:
            messagebox.showinfo("Aviso", "Automação já está em execução")
            return
        
        if not self.region:
            messagebox.showwarning("Aviso", "Configure a região de captura primeiro")
            return
        
        # Detecta qual aba está ativa (CustomTkinter)
        active_tab_name = self.tabview.get()
        
        # Mapeia nome para índice
        if active_tab_name == "🎯 Valores Específicos":
            active_tab = 0
        elif active_tab_name == "🔍 Busca de Atributos":
            active_tab = 1
        elif active_tab_name == "🔑 Automação de Chaves":
            active_tab = 2
        else:
            active_tab = 0
        
        if active_tab == 0:  # Aba de valores específicos
            # Valida entradas
            valid_entries = False
            for entry in self.attr_entries:
                if entry['name'].get().strip() and entry['value'].get().strip():
                    valid_entries = True
                    break
            
            if not valid_entries:
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo alvo")
                return
            
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.update_status("▶️ Iniciando...", 'info')
            
            # Inicia thread de automação com valores
            thread = threading.Thread(target=self.automation_loop_values, daemon=True)
            thread.start()
            self.log("▶️ Automação INICIADA (Valores Específicos)")
            
        elif active_tab == 1:  # Aba de busca por atributos
            # Valida entradas
            valid_entries = False
            for entry in self.search_entries:
                if entry['name'].get().strip():
                    valid_entries = True
                    break
            
            if not valid_entries:
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo para procurar")
                return
            
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.update_status("▶️ Iniciando...", 'info')
            
            # Inicia thread de automação com busca de atributos
            thread = threading.Thread(target=self.automation_loop_attributes, daemon=True)
            thread.start()
            self.log("▶️ Automação INICIADA (Busca de Atributos)")
            
        else:  # Aba de automação de chaves (active_tab == 2)
            # Valida entradas
            valid_entries = False
            for entry in self.keys_entries:
                if entry['name'].get().strip():
                    valid_entries = True
                    break
            
            if not valid_entries:
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo desejado")
                return
            
            # Valida posições
            if not self.key_position:
                messagebox.showwarning("Aviso", "Configure a posição da chave primeiro")
                return
            if not self.orb_position:
                messagebox.showwarning("Aviso", "Configure a posição do Orb of Chance primeiro")
                return
            if not self.bp_position:
                messagebox.showwarning("Aviso", "Configure a posição da BP destino primeiro")
                return
            
            self.is_running = True
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.update_status("▶️ Iniciando...", 'info')
            
            # Inicia thread de automação de chaves
            thread = threading.Thread(target=self.automation_loop_keys, daemon=True)
            thread.start()
            self.log("▶️ Automação INICIADA (Automação de Chaves)")
    
    def stop_automation(self):
        """Para a automação e reabilita os botões"""
        # Marca como parado PRIMEIRO
        self.is_running = False
        
        # Aguarda um pouco para garantir que threads param
        time.sleep(0.1)
        
        try:
            # Reabilita botões
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            
            # Atualiza status
            self.update_status("⬛ Pronto para iniciar", 'info')
            self.log("⬛ Automação PARADA - Pronto para reiniciar")
            self.log_to_detail("\n⬛ AUTOMAÇÃO INTERROMPIDA - Você pode iniciar novamente", 'warning')
        except Exception as e:
            print(f"Erro ao parar automação: {e}")
            # Força atualização dos botões mesmo com erro
            try:
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
            except:
                pass
    
    def update_status(self, text, status_type='info'):
        """Atualiza status com cores modernas
        status_type: 'success', 'warning', 'danger', 'info'
        """
        color_map = {
            'success': self.colors['success'],
            'warning': self.colors['warning'],
            'danger': self.colors['danger'],
            'info': self.colors['dark'],
            'running': self.colors['accent']
        }
        
        icon_map = {
            'success': '✓',
            'warning': '⚠',
            'danger': '✗',
            'info': '●',
            'running': '▶'
        }
        
        color = color_map.get(status_type, self.colors['success'])
        icon = icon_map.get(status_type, '●')
        
        self.status_label.configure(text=f"{icon} {text}", text_color=color)
        self.root.update_idletasks()
    
    def log(self, message):
        """Log mensagem - só exibe se console estiver visível"""
        try:
            if self.log_text:
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{timestamp}] {message}\n")
                self.log_text.see("end")
                self.root.update_idletasks()
        except:
            pass  # Ignora erro se console foi fechado
    
    def toggle_theme(self):
        """Alterna entre tema dark e light"""
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
    
class SplashScreen:
    """Tela de loading moderna com animações de partículas"""
    def __init__(self):
        # Cria janela Tk pura (não depende de CTk)
        self.splash = tk.Tk()
        self.splash.overrideredirect(True)
        self.splash.attributes('-topmost', True)
        
        # Tamanho
        self.width = 500
        self.height = 400
        
        # Centralizar
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        self.splash.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
        # Canvas com fundo escuro
        self.canvas = tk.Canvas(self.splash, width=self.width, height=self.height, 
                               bg="#0f0f1a", highlightthickness=0)
        self.canvas.pack()
        
        # Fundo com gradiente simulado (retângulos sobrepostos)
        self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#0f0f1a", outline="")
        self.canvas.create_rectangle(10, 10, self.width-10, self.height-10, fill="#1a1a2e", outline="")
        self.canvas.create_rectangle(15, 15, self.width-15, self.height-15, fill="#16213e", outline="")
        
        # Borda brilhante
        self.canvas.create_rectangle(15, 15, self.width-15, self.height-15, 
                                     outline="#6366f1", width=2)
        
        # Partículas de fundo (efeito)
        self.particles = []
        for _ in range(20):
            px = random.randint(30, self.width-30)
            py = random.randint(30, self.height-30)
            size = random.randint(2, 5)
            color = random.choice(["#4a5de0", "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe"])
            p = self.canvas.create_oval(px-size, py-size, px+size, py+size, fill=color, outline="")
            self.particles.append({
                'id': p, 'x': px, 'y': py, 
                'dx': random.uniform(-0.8, 0.8), 
                'dy': random.uniform(-0.8, 0.8), 
                'size': size
            })
        
        # Ícone emoji grande
        self.canvas.create_text(self.width//2, 90, text="⚡", 
                               font=("Segoe UI", 55), fill="#6366f1")
        
        # Título
        self.canvas.create_text(self.width//2, 170, text="REROLL DO", 
                               font=("Segoe UI", 28, "bold"), fill="#e0e7ff")
        self.canvas.create_text(self.width//2, 215, text="CADEIRAS", 
                               font=("Segoe UI", 36, "bold"), fill="#818cf8")
        
        # Subtítulo
        self.canvas.create_text(self.width//2, 260, text="por Victor Gomes de Sá", 
                               font=("Segoe UI", 10), fill="#64748b")
        
        # Barra de progresso moderna
        self.bar_x = 80
        self.bar_y = 310
        self.bar_width = self.width - 160
        self.bar_height = 12
        
        # Fundo da barra com borda
        self.canvas.create_rectangle(self.bar_x-2, self.bar_y-2, 
                                     self.bar_x + self.bar_width+2, self.bar_y + self.bar_height+2,
                                     fill="#0f172a", outline="#334155")
        
        # Barra de progresso
        self.progress_bar = self.canvas.create_rectangle(self.bar_x, self.bar_y, 
                                                          self.bar_x, self.bar_y + self.bar_height,
                                                          fill="#6366f1", outline="")
        
        # Texto de status
        self.status_text = self.canvas.create_text(self.width//2, 350, text="Iniciando...", 
                                                   font=("Segoe UI", 11), fill="#94a3b8")
        
        # Versão
        self.canvas.create_text(self.width//2, self.height-25, text=f"v{APP_VERSION}", 
                               font=("Segoe UI", 9), fill="#475569")
        
        self.splash.update()
    
    def animate_particles(self):
        """Anima as partículas de fundo"""
        for p in self.particles:
            p['x'] += p['dx']
            p['y'] += p['dy']
            
            # Bounce nas bordas
            if p['x'] < 40 or p['x'] > self.width-40:
                p['dx'] *= -1
            if p['y'] < 40 or p['y'] > self.height-40:
                p['dy'] *= -1
            
            self.canvas.coords(p['id'], 
                              p['x']-p['size'], p['y']-p['size'],
                              p['x']+p['size'], p['y']+p['size'])
    
    def update_progress(self, value, status="Carregando..."):
        """Atualiza a barra de progresso (0 a 1)"""
        fill_width = int(self.bar_width * value)
        self.canvas.coords(self.progress_bar, 
                          self.bar_x, self.bar_y, 
                          self.bar_x + fill_width, self.bar_y + self.bar_height)
        self.canvas.itemconfig(self.status_text, text=status)
        
        # Anima partículas
        self.animate_particles()
        self.splash.update()
    
    def destroy(self):
        """Fecha a splash com fade out"""
        try:
            for alpha in [0.8, 0.6, 0.4, 0.2, 0]:
                self.splash.attributes('-alpha', alpha)
                self.splash.update()
                time.sleep(0.03)
            self.splash.destroy()
        except:
            pass

def main():
    print("🚀 Iniciando Reroll do Cadeiras...")
    
    try:
        # Mostra splash primeiro (Tk puro, independente)
        splash = SplashScreen()
        
        # Mensagens de status
        status_messages = [
            (0.0, "Inicializando..."),
            (0.25, "Carregando módulos..."),
            (0.50, "Configurando interface..."),
            (0.75, "Preparando automação..."),
            (0.95, "Pronto!")
        ]
        
        # Animação contínua e suave
        total_steps = 60  # 60 frames para ~2 segundos
        for i in range(total_steps + 1):
            progress = i / total_steps
            
            # Determina a mensagem de status atual
            current_status = "Iniciando..."
            for threshold, msg in status_messages:
                if progress >= threshold:
                    current_status = msg
            
            splash.update_progress(progress, current_status)
            time.sleep(0.033)  # ~30 FPS
        
        time.sleep(0.2)
        splash.destroy()
        
        # Agora cria a janela principal CTk
        root = ctk.CTk()
        print("✓ Carregando interface...")
        app = GameAutomation(root)
        print("✓ Pronto!")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
