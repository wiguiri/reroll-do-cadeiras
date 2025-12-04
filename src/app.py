"""
Aplicação principal - Reroll do Cadeiras.
Classe principal que integra todos os módulos.
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from PIL import ImageTk
import time
import threading
import keyboard
import pyautogui
import os
import sys

from src.config import (
    APP_VERSION, COLORS, DEFAULT_HOTKEYS, DEFAULT_SETTINGS,
    UI_CONFIG, get_icon_path
)
from src.presets import PresetManager, ConfigManager
from src.ocr_engine import OCREngine
from src.automation import AutomationEngine
from src.updater import AutoUpdater
from src.ui.tabs import ValuesTab, SearchTab, KeysTab, T7Tab, SkillSpamTab
from src.ui.components import LogWindow, StatusBar
from src.ui.dialogs import HotkeySettingsDialog, NewPresetDialog, UpdateDialog, UpdateProgressDialog


# Configurar CustomTkinter
ctk.set_appearance_mode(UI_CONFIG['appearance_mode'])
ctk.set_default_color_theme(UI_CONFIG['color_theme'])


class GameAutomation:
    """Aplicação principal de automação."""
    
    def __init__(self, root):
        """
        Inicializa a aplicação.
        
        Args:
            root: Janela principal CTk.
        """
        self.root = root
        self._setup_window()
        
        # Gerenciadores
        self.preset_manager = PresetManager()
        self.config_manager = ConfigManager()
        self.ocr = OCREngine()
        self.automation = AutomationEngine(self)
        
        # Estado
        self.is_running = False
        self.region = None
        self.hotkeys = DEFAULT_HOTKEYS.copy()
        self.colors = COLORS
        
        # Posições para automação de chaves
        self.key_position = None
        self.orb_position = None
        self.bp_position = None
        
        # Skill spam
        self.skill_spam_running = False
        self.skill_spam_threads = []
        
        # UI
        self.log_window = LogWindow(self.root)
        self.log_text = None  # Para compatibilidade
        
        # Variáveis de configuração
        self.delay_var = tk.StringVar(value=DEFAULT_SETTINGS['delay'])
        self.click_delay_var = tk.StringVar(value=DEFAULT_SETTINGS['click_delay'])
        self.max_attempts_var = tk.StringVar(value=DEFAULT_SETTINGS['max_attempts'])
        
        # Construir UI
        self._setup_ui()
        
        # Carregar configurações
        self.load_config()
        
        # Configurar hotkeys APÓS carregar config (para usar hotkeys salvos)
        self._setup_local_hotkeys()
        self.setup_global_hotkeys()
        
        # Verificar atualizações automaticamente ao iniciar
        self.root.after(2000, self._check_updates_auto)
        
        # Eventos
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_window(self):
        """Configura a janela principal."""
        self.root.title(UI_CONFIG['window_title'])
        self.root.geometry(UI_CONFIG['window_size'])
        self.root.minsize(*UI_CONFIG['window_min_size'])
        
        # Ícone
        try:
            icon_path = get_icon_path()
            if os.path.exists(icon_path):
                self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass
    
    def _setup_ui(self):
        """Constrói a interface do usuário."""
        # Grid responsivo
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Container principal scrollável
        main_container = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_columnconfigure(0, weight=1)
        
        self._build_header(main_container)
        self._build_tabs(main_container)
        self._build_controls(main_container)
        self._build_footer(main_container)
        
        # Hotkeys serão configurados após load_config()
    
    def _build_header(self, parent):
        """Constrói o cabeçalho."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        ctk.CTkLabel(
            header_frame, text="⚡ Reroll do Cadeiras",
            font=(UI_CONFIG['font_family'], 24, "bold")
        ).grid(row=0, column=0, sticky="w")
        
        # Créditos
        ctk.CTkLabel(
            header_frame, text="por Victor Gomes de Sá",
            font=(UI_CONFIG['font_family'], 10),
            text_color="gray60"
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        # Botão de configurações
        self.settings_btn = ctk.CTkButton(
            header_frame, text="⚙",
            command=self._open_hotkeys_settings,
            width=45, height=45,
            font=(UI_CONFIG['font_family'], 24),
            fg_color="transparent", hover_color="gray30",
            corner_radius=10
        )
        self.settings_btn.grid(row=0, column=2, rowspan=2, sticky="ne", padx=(10, 0))
    
    def _build_tabs(self, parent):
        """Constrói as abas."""
        self.tabview = ctk.CTkTabview(
            parent, 
            corner_radius=10,
            segmented_button_fg_color=("gray85", "gray25"),
            segmented_button_selected_color=("#3b82f6", "#2563eb"),
            segmented_button_selected_hover_color=("#2563eb", "#1d4ed8"),
            segmented_button_unselected_color=("gray85", "gray25"),
            segmented_button_unselected_hover_color=("gray75", "gray35")
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        
        # Aumentar tamanho das abas
        self.tabview._segmented_button.configure(font=(UI_CONFIG['font_family'], 12, "bold"))
        
        # Criar abas
        self.tabview.add("🎯 Valores Específicos")
        self.tabview.add("🔍 Busca de Atributos")
        self.tabview.add("⭐ Buscar T7")
        self.tabview.add("🔑 Automação de Chaves")
        self.tabview.add("⚡ Skill Spam")
        
        # Instanciar abas
        self.tab_values = ValuesTab(self.tabview.tab("🎯 Valores Específicos"), self)
        self.tab_search = SearchTab(self.tabview.tab("🔍 Busca de Atributos"), self)
        self.tab_t7 = T7Tab(self.tabview.tab("⭐ Buscar T7"), self)
        self.tab_keys = KeysTab(self.tabview.tab("🔑 Automação de Chaves"), self)
        self.tab_skill_spam = SkillSpamTab(self.tabview.tab("⚡ Skill Spam"), self)
    
    def _build_controls(self, parent):
        """Constrói os controles inferiores."""
        controls_card = ctk.CTkFrame(parent, corner_radius=15, border_width=2)
        controls_card.grid(row=2, column=0, sticky="ew", pady=(20, 0))
        controls_card.grid_columnconfigure(0, weight=1)
        
        self._build_region_section(controls_card)
        self._build_settings_section(controls_card)
        self._build_buttons_section(controls_card)
        
        self.controls_card = controls_card
    
    def _build_region_section(self, parent):
        """Constrói a seção de região de captura."""
        region_container = ctk.CTkFrame(parent, fg_color="transparent")
        region_container.grid(row=0, column=0, sticky="ew", padx=20, pady=15)
        region_container.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            region_container, text="📍 Região de Captura",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))
        
        buttons_row = ctk.CTkFrame(region_container, fg_color="transparent")
        buttons_row.grid(row=1, column=0, sticky="ew")
        
        self.btn_region = ctk.CTkButton(
            buttons_row, text=f"🎯 Selecionar Região ({self.hotkeys['region']})",
            command=self.select_region_visual, height=35
        )
        self.btn_region.pack(side="left", padx=(0, 10))
        
        self.btn_test = ctk.CTkButton(
            buttons_row, text=f"🔍 Testar Captura ({self.hotkeys['test']})",
            command=self.test_capture_detailed, height=35,
            fg_color="gray40"
        )
        self.btn_test.pack(side="left")
        
        self.region_label = ctk.CTkLabel(
            region_container, text="● Região não configurada",
            text_color="#f59e0b"
        )
        self.region_label.grid(row=2, column=0, sticky="w", pady=(10, 0))
        
        # Separador
        ctk.CTkFrame(parent, height=2, fg_color="gray30").grid(
            row=1, column=0, sticky="ew", padx=20, pady=10
        )
    
    def _build_settings_section(self, parent):
        """Constrói a seção de configurações."""
        config_container = ctk.CTkFrame(parent, fg_color="transparent")
        config_container.grid(row=2, column=0, sticky="ew", padx=20, pady=15)
        
        ctk.CTkLabel(
            config_container, text="⚙️ Configurações",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))
        
        settings_row = ctk.CTkFrame(config_container, fg_color="transparent")
        settings_row.grid(row=1, column=0, sticky="w")
        
        # Delay
        ctk.CTkLabel(settings_row, text="Delay (s):").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(
            settings_row, textvariable=self.delay_var,
            width=70, placeholder_text="0.1"
        ).pack(side="left", padx=(0, 20))
        
        # Click delay
        ctk.CTkLabel(settings_row, text="Click (ms):").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(
            settings_row, textvariable=self.click_delay_var,
            width=70, placeholder_text="20"
        ).pack(side="left", padx=(0, 20))
        
        # Max tentativas
        ctk.CTkLabel(settings_row, text="Max:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(
            settings_row, textvariable=self.max_attempts_var,
            width=80, placeholder_text="1000"
        ).pack(side="left")
        
        # Separador
        ctk.CTkFrame(parent, height=2, fg_color="gray30").grid(
            row=3, column=0, sticky="ew", padx=20, pady=10
        )
    
    def _build_buttons_section(self, parent):
        """Constrói a seção de botões de controle."""
        control_container = ctk.CTkFrame(parent, fg_color="transparent")
        control_container.grid(row=4, column=0, sticky="ew", padx=20, pady=15)
        control_container.grid_columnconfigure(0, weight=1)
        
        buttons_control = ctk.CTkFrame(control_container, fg_color="transparent")
        buttons_control.grid(row=0, column=0)
        
        self.start_button = ctk.CTkButton(
            buttons_control, text=f"▶ INICIAR ({self.hotkeys['start']})",
            command=self.start_automation,
            width=180, height=45,
            font=(UI_CONFIG['font_family'], 13, "bold"),
            fg_color="#047857", hover_color="#065f46",
            text_color="white"
        )
        self.start_button.pack(side="left", padx=5)
        
        self.stop_button = ctk.CTkButton(
            buttons_control, text=f"⬛ PARAR ({self.hotkeys['stop']})",
            command=self.stop_automation,
            width=180, height=45,
            font=(UI_CONFIG['font_family'], 13, "bold"),
            fg_color="#b91c1c", hover_color="#991b1b",
            text_color="white",
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        
        ctk.CTkButton(
            buttons_control, text="📊 Log Detalhado",
            command=self.log_window.open,
            width=150, height=45,
            font=(UI_CONFIG['font_family'], 13, "bold"),
            fg_color="#4b5563", hover_color="#374151",
            text_color="white"
        ).pack(side="left", padx=5)
        
        # Status
        self.status_label = ctk.CTkLabel(
            control_container, text="● Aguardando configuração...",
            font=(UI_CONFIG['font_family'], 10),
            text_color="gray60"
        )
        self.status_label.grid(row=1, column=0, pady=(10, 0))
    
    def _build_footer(self, parent):
        """Constrói o rodapé."""
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.grid(row=3, column=0, sticky="ew", pady=(15, 0))
        footer_frame.grid_columnconfigure(1, weight=1)
        
        # Toggle de tema
        theme_switch = ctk.CTkSwitch(
            footer_frame, text="🌙 Modo Dark",
            command=self._toggle_theme,
            font=(UI_CONFIG['font_family'], 11)
        )
        theme_switch.grid(row=0, column=0, sticky="w")
        theme_switch.select()
        
        # Versão e atualização
        version_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        version_frame.grid(row=0, column=2, sticky="e")
        
        ctk.CTkLabel(
            version_frame, text=f"v{APP_VERSION}",
            font=(UI_CONFIG['font_family'], 10), text_color="gray50"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            version_frame, text="🔄 Verificar Atualizações",
            command=self._check_updates_manual,
            width=160, height=28,
            font=(UI_CONFIG['font_family'], 10),
            fg_color="gray30", hover_color="gray40"
        ).pack(side="left")
    
    def _setup_local_hotkeys(self):
        """Configura atalhos locais da janela."""
        # Remove TODOS os bindings de teclas de função e teclas comuns
        keys_to_unbind = [
            'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
            'Escape', 'Return', 'space'
        ]
        
        # Também remove os hotkeys atuais configurados
        for hotkey in self.hotkeys.values():
            if hotkey not in keys_to_unbind:
                keys_to_unbind.append(hotkey)
        
        for key in keys_to_unbind:
            try:
                self.root.unbind(f'<{key}>')
            except:
                pass
        
        # Configura os novos bindings
        self.root.bind(f'<{self.hotkeys["region"]}>', lambda e: self.select_region_visual())
        self.root.bind(f'<{self.hotkeys["test"]}>', lambda e: self.test_capture_detailed())
        self.root.bind(f'<{self.hotkeys["start"]}>', lambda e: self.start_automation())
        self.root.bind(f'<{self.hotkeys["stop"]}>', lambda e: self.stop_automation())
    
    def setup_global_hotkeys(self):
        """Configura atalhos globais."""
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        
        try:
            keyboard.add_hotkey(self.hotkeys['region'].lower(), self.select_region_visual)
            keyboard.add_hotkey(self.hotkeys['test'].lower(), self.test_capture_detailed)
            keyboard.add_hotkey(self.hotkeys['start'].lower(), self.start_automation)
            keyboard.add_hotkey(self.hotkeys['stop'].lower(), self.stop_automation)
            
            # Hotkey do Skill Spam
            skill_spam_hotkey = self.tab_skill_spam.get_hotkey()
            keyboard.add_hotkey(skill_spam_hotkey.lower(), self.toggle_skill_spam)
            
            self.log(f"⌨️ Atalhos: {self.hotkeys['region']}/{self.hotkeys['test']}/{self.hotkeys['start']}/{self.hotkeys['stop']}")
        except Exception as e:
            self.log(f"⚠️ Erro ao configurar atalhos: {e}")
    
    # ============================================
    # MÉTODOS DE REGIÃO E CAPTURA
    # ============================================
    
    def select_region_visual(self):
        """Captura tela e permite selecionar região visualmente."""
        self.log("📸 Capturando tela...")
        
        self.root.iconify()
        self.root.update()
        time.sleep(0.2)
        
        screenshot = self.ocr.capture_fullscreen()
        screen_width, screen_height = screenshot.size
        
        self.log("🎯 Clique e arraste para selecionar a região")
        
        # Cria overlay
        overlay = tk.Toplevel()
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.configure(background='black')
        
        photo = ImageTk.PhotoImage(screenshot)
        
        self.selection_start = None
        self.selection_rect = None
        
        canvas = tk.Canvas(overlay, highlightthickness=0, background='black')
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=photo, anchor='nw')
        
        # Instruções
        canvas.create_rectangle(
            screen_width // 2 - 300, 20,
            screen_width // 2 + 300, 70,
            fill='black', outline='white', width=2
        )
        canvas.create_text(
            screen_width // 2, 45,
            text="Clique e arraste para selecionar | ESC para cancelar",
            font=('Arial', 14, 'bold'), fill='yellow'
        )
        
        def on_mouse_down(event):
            self.selection_start = (event.x, event.y)
        
        def on_mouse_move(event):
            if self.selection_start:
                if self.selection_rect:
                    canvas.delete(self.selection_rect)
                    canvas.delete('coords_text')
                    canvas.delete('coords_bg')
                
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y
                self.selection_rect = canvas.create_rectangle(
                    x1, y1, x2, y2, outline='red', width=3
                )
                
                w = abs(x2 - x1)
                h = abs(y2 - y1)
                text_x = (x1 + x2) // 2
                text_y = min(y1, y2) - 25
                
                canvas.create_rectangle(
                    text_x - 80, text_y - 15,
                    text_x + 80, text_y + 15,
                    fill='black', outline='yellow', width=1, tags='coords_bg'
                )
                canvas.create_text(
                    text_x, text_y,
                    text=f"{w} x {h} pixels",
                    font=('Arial', 12, 'bold'), fill='yellow', tags='coords_text'
                )
        
        def on_mouse_up(event):
            if self.selection_start:
                x1, y1 = self.selection_start
                x2, y2 = event.x, event.y
                
                left = min(x1, x2)
                top = min(y1, y2)
                right = max(x1, x2)
                bottom = max(y1, y2)
                
                if (right - left) < 10 or (bottom - top) < 10:
                    canvas.delete(self.selection_rect)
                    canvas.delete('coords_text')
                    canvas.delete('coords_bg')
                    self.selection_start = None
                    return
                
                self.region = (left, top, right, bottom)
                overlay.destroy()
                self.root.deiconify()
                
                width = right - left
                height = bottom - top
                self.region_label.configure(
                    text=f"✓ Região: {left},{top} → {right},{bottom} ({width}x{height}px)",
                    text_color="#10b981"
                )
                
                self.log(f"✓ Região selecionada: {width}x{height}px")
                self.save_config()
        
        def on_escape(event):
            overlay.destroy()
            self.root.deiconify()
            self.log("❌ Seleção cancelada")
        
        canvas.bind('<ButtonPress-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        overlay.bind('<Escape>', on_escape)
        
        overlay.photo = photo
        overlay.focus_force()
    
    def test_capture_detailed(self):
        """Testa captura e mostra resultados."""
        if not self.region:
            messagebox.showwarning("Aviso", "Configure a região primeiro")
            return
        
        try:
            self.log("🔍 Testando captura...")
            self.log_to_detail("\n" + "="*60, 'header')
            self.log_to_detail("🔍 TESTE DE CAPTURA", 'header')
            
            screenshot = self.ocr.capture_region(self.region)
            text, current_values = self.ocr.extract_text_with_processing(screenshot)
            
            self.log("=== Texto Capturado ===")
            self.log(text if text.strip() else "(vazio)")
            
            self.log_to_detail(f"📄 Texto capturado:", 'info')
            self.log_to_detail(text if text.strip() else "(nenhum texto)", 'info')
            
            if current_values:
                self.log_to_detail(f"\n📊 Valores encontrados:", 'success')
                for name, value in current_values.items():
                    self.log_to_detail(f"  • {name.upper()}: {value}", 'success')
                    self.log(f"✓ {name.upper()}: {value}")
            else:
                self.log_to_detail("⚠️ Nenhum atributo identificado", 'warning')
                self.log("⚠️ Nenhum atributo identificado")
            
            # Popup
            if current_values:
                summary = "Valores encontrados:\n\n" + "\n".join(
                    [f"{k.upper()}: {v}" for k, v in current_values.items()]
                )
            else:
                summary = "Nenhum valor encontrado.\n\nTexto:\n" + (text[:200] if text else "(vazio)")
            
            messagebox.showinfo("🔍 Teste de Captura", summary)
            
        except Exception as e:
            self.log(f"Erro: {e}")
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")
    
    def test_t7_capture(self):
        """Testa captura de tiers T7 e mostra todos os atributos encontrados."""
        if not self.region:
            messagebox.showwarning("Aviso", "Configure a região primeiro (F1)")
            return
        
        try:
            self.log("🔍 Testando captura T7...")
            self.log_to_detail("\n" + "="*60, 'header')
            self.log_to_detail("🔍 TESTE DE CAPTURA T7", 'header')
            self.log_to_detail("="*60, 'header')
            
            screenshot = self.ocr.capture_region(self.region)
            
            # Tenta múltiplas configurações de OCR para melhor resultado
            from PIL import ImageEnhance, ImageOps
            
            all_results = []
            
            # Tentativa 1: Imagem normal
            text1 = self.ocr.extract_text(screenshot)
            tiers1 = self.ocr.extract_attributes_with_tiers(text1)
            all_results.append(('Normal', tiers1))
            
            # Tentativa 2: Escala de cinza + contraste
            gray = screenshot.convert('L')
            enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
            text2 = self.ocr.extract_text(enhanced, '--psm 6')
            tiers2 = self.ocr.extract_attributes_with_tiers(text2)
            all_results.append(('Contraste', tiers2))
            
            # Tentativa 3: Inversão
            inverted = ImageOps.invert(gray)
            inv_contrast = ImageEnhance.Contrast(inverted).enhance(3.0)
            text3 = self.ocr.extract_text(inv_contrast, '--psm 6')
            tiers3 = self.ocr.extract_attributes_with_tiers(text3)
            all_results.append(('Invertido', tiers3))
            
            # Tentativa 4: Brightness
            bright = ImageEnhance.Brightness(gray).enhance(1.5)
            text4 = self.ocr.extract_text(bright, '--psm 6')
            tiers4 = self.ocr.extract_attributes_with_tiers(text4)
            all_results.append(('Brilho', tiers4))
            
            # Pega o melhor resultado (mais atributos)
            best_method, best_tiers = max(all_results, key=lambda x: len(x[1]))
            
            # Log detalhado
            self.log_to_detail(f"\n📊 Melhor método: {best_method} ({len(best_tiers)} atributos)", 'info')
            
            has_t7 = False
            t7_attrs = []
            
            if best_tiers:
                self.log_to_detail(f"\n📋 Atributos encontrados:", 'info')
                for attr in best_tiers:
                    tier = attr['tier']
                    name = attr['name'].upper()
                    value = attr['value']
                    
                    if tier == 7:
                        self.log_to_detail(f"  ⭐ T{tier} {name}: +{value}", 'success')
                        self.log(f"⭐ T{tier} {name}: +{value}")
                        has_t7 = True
                        t7_attrs.append(f"T{tier} {name}: +{value}")
                    elif tier >= 5:
                        self.log_to_detail(f"  🔶 T{tier} {name}: +{value}", 'warning')
                        self.log(f"🔶 T{tier} {name}: +{value}")
                    else:
                        self.log_to_detail(f"  ⚪ T{tier} {name}: +{value}", 'info')
                        self.log(f"⚪ T{tier} {name}: +{value}")
            else:
                self.log_to_detail("⚠️ Nenhum atributo com tier detectado", 'warning')
                self.log("⚠️ Nenhum atributo detectado")
            
            # Comparação de métodos
            self.log_to_detail(f"\n📈 Comparação de métodos:", 'info')
            for method, tiers in all_results:
                self.log_to_detail(f"  • {method}: {len(tiers)} atributos", 'info')
            
            # Atualiza label na aba T7
            if has_t7:
                self.tab_t7.test_result_label.configure(
                    text=f"⭐ T7 ENCONTRADO! ({len(best_tiers)} attrs)",
                    text_color="#22c55e"
                )
            else:
                self.tab_t7.test_result_label.configure(
                    text=f"❌ Sem T7 ({len(best_tiers)} attrs detectados)",
                    text_color="#ef4444"
                )
            
            # Popup
            if best_tiers:
                summary = f"Método: {best_method}\n\nAtributos ({len(best_tiers)}):\n\n"
                for attr in best_tiers:
                    tier = attr['tier']
                    name = attr['name'].upper()
                    value = attr['value']
                    prefix = "⭐" if tier == 7 else ("🔶" if tier >= 5 else "⚪")
                    summary += f"{prefix} T{tier} {name}: +{value}\n"
                
                if has_t7:
                    summary += f"\n🎉 T7 ENCONTRADO!"
            else:
                summary = f"Nenhum atributo com tier detectado.\n\nTexto bruto:\n{text1[:300]}"
            
            messagebox.showinfo("🔍 Teste T7", summary)
            
        except Exception as e:
            self.log(f"Erro: {e}")
            self.tab_t7.test_result_label.configure(
                text=f"❌ Erro: {e}",
                text_color="#ef4444"
            )
            messagebox.showerror("Erro", f"Erro ao capturar: {e}")
    
    # ============================================
    # MÉTODOS DE VERIFICAÇÃO
    # ============================================
    
    def check_target_reached(self, current_values):
        """Verifica se os valores alvo foram atingidos."""
        all_reached = True
        details = []
        
        for entry in self.tab_values.entries:
            name = entry.get_name().lower()
            name = ' '.join(name.split())
            target = entry.get_value()
            
            if not name or not target:
                continue
            
            try:
                target_val = float(target)
                
                if name not in current_values:
                    all_reached = False
                    details.append(f"❌ {name.upper()}: NÃO ENCONTRADO (alvo: ≥{target_val})")
                    continue
                
                current_val = current_values[name]
                
                if current_val >= target_val:
                    details.append(f"✅ {name.upper()}: {current_val} (alvo: ≥{target_val}) - ATINGIDO!")
                else:
                    all_reached = False
                    diff = target_val - current_val
                    details.append(f"⏳ {name.upper()}: {current_val} (falta: {diff:.1f})")
            except ValueError:
                continue
        
        return all_reached, "\n".join(details)
    
    def check_attributes_found(self, current_values):
        """Verifica se os atributos desejados estão presentes."""
        return self._check_attributes_generic(
            self.tab_search.entries,
            self.tab_search.get_mode(),
            self.tab_search.get_min_count(),
            current_values
        )
    
    def check_keys_attributes(self, current_values):
        """Verifica se a chave tem os atributos desejados."""
        return self._check_attributes_generic(
            self.tab_keys.entries,
            self.tab_keys.get_mode(),
            self.tab_keys.get_min_count(),
            current_values
        )
    
    def _check_attributes_generic(self, entries, mode, min_count_str, current_values):
        """Verificação genérica de atributos."""
        required_must_have = []
        required_optional = []
        
        for entry in entries:
            name = entry.get_name().lower()
            name = ' '.join(name.split())
            if name:
                if entry.is_required():
                    required_must_have.append(name)
                else:
                    required_optional.append(name)
        
        all_attrs = required_must_have + required_optional
        
        if not all_attrs:
            return False, "❌ Nenhum atributo especificado"
        
        # Normaliza valores atuais
        normalized_current = {k.lower().strip(): v for k, v in current_values.items()}
        
        found_must_have = []
        missing_must_have = []
        found_optional = []
        details = []
        
        # Verifica obrigatórios
        for attr_name in required_must_have:
            found_value = None
            for current_key, current_val in normalized_current.items():
                if attr_name in current_key or current_key in attr_name:
                    found_value = current_val
                    break
            
            if found_value is not None:
                found_must_have.append(attr_name)
                details.append(f"⭐ {attr_name.upper()}: {found_value} - OBRIGATÓRIO!")
            else:
                missing_must_have.append(attr_name)
                details.append(f"❌ {attr_name.upper()}: OBRIGATÓRIO NÃO ENCONTRADO")
        
        # Verifica opcionais
        for attr_name in required_optional:
            found_value = None
            for current_key, current_val in normalized_current.items():
                if attr_name in current_key or current_key in attr_name:
                    found_value = current_val
                    break
            
            if found_value is not None:
                found_optional.append(attr_name)
                details.append(f"✅ {attr_name.upper()}: {found_value}")
            else:
                details.append(f"❌ {attr_name.upper()}: NÃO ENCONTRADO")
        
        total_found = len(found_must_have) + len(found_optional)
        
        if mode == "ALL":
            success = (total_found == len(all_attrs))
            details.insert(0, f"📊 Modo: TODOS - {total_found}/{len(all_attrs)}")
        else:
            try:
                min_required = int(min_count_str)
            except:
                min_required = 1
            
            all_must_have_found = (len(missing_must_have) == 0)
            enough_total = (total_found >= min_required)
            
            success = all_must_have_found and enough_total
            details.insert(0, f"📊 Modo: MÍNIMO - {total_found}/{len(all_attrs)} (precisa: {min_required})")
        
        return success, "\n".join(details)
    
    # ============================================
    # MÉTODOS DE AUTOMAÇÃO
    # ============================================
    
    def start_automation(self):
        """Inicia a automação."""
        if self.is_running:
            messagebox.showinfo("Aviso", "Automação já está em execução")
            return
        
        if not self.region:
            messagebox.showwarning("Aviso", "Configure a região primeiro")
            return
        
        # Detecta aba ativa
        active_tab_name = self.tabview.get()
        
        if active_tab_name == "🎯 Valores Específicos":
            if not any(e.get_name() and e.get_value() for e in self.tab_values.entries):
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo alvo")
                return
            mode = 'values'
            
        elif active_tab_name == "🔍 Busca de Atributos":
            if not any(e.get_name() for e in self.tab_search.entries):
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo")
                return
            mode = 'attributes'
        
        elif active_tab_name == "⭐ Buscar T7":
            # Verifica se modo específico tem atributos definidos
            if self.tab_t7.get_mode() == "SPECIFIC":
                if not self.tab_t7.get_specific_attributes():
                    messagebox.showwarning("Aviso", "Defina pelo menos um atributo específico para T7")
                    return
            mode = 't7'
            
        else:  # Automação de Chaves
            if not any(e.get_name() for e in self.tab_keys.entries):
                messagebox.showwarning("Aviso", "Defina pelo menos um atributo")
                return
            if not self.key_position:
                messagebox.showwarning("Aviso", "Configure a posição da chave")
                return
            if not self.orb_position:
                messagebox.showwarning("Aviso", "Configure a posição do Orb")
                return
            if not self.bp_position:
                messagebox.showwarning("Aviso", "Configure a posição da BP")
                return
            mode = 'keys'
        
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.update_status("▶️ Iniciando...", 'info')
        
        self.automation.start(mode)
        self.log(f"▶️ Automação INICIADA ({mode})")
    
    def stop_automation(self):
        """Para a automação."""
        self.is_running = False
        self.automation.stop()
        
        time.sleep(0.1)
        
        try:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.update_status("⬛ Pronto para iniciar", 'info')
            self.log("⬛ Automação PARADA")
            self.log_to_detail("\n⬛ AUTOMAÇÃO INTERROMPIDA", 'warning')
        except Exception as e:
            print(f"Erro ao parar: {e}")
    
    # ============================================
    # MÉTODOS DE SKILL SPAM
    # ============================================
    
    def toggle_skill_spam(self):
        """Alterna o estado do skill spam."""
        if self.skill_spam_running:
            self.stop_skill_spam()
        else:
            self.start_skill_spam()
    
    def start_skill_spam(self):
        """Inicia o spam de skills."""
        program = self.tab_skill_spam.get_selected_program()
        skills = self.tab_skill_spam.get_skills_data()
        
        if program == "Selecione um programa" or not program:
            messagebox.showwarning("Aviso", "Selecione um programa alvo")
            return
        
        if not skills:
            messagebox.showwarning("Aviso", "Configure pelo menos uma skill")
            return
        
        # Encontra a janela do programa
        try:
            import win32gui
            import win32con
            import win32api
            
            hwnd = win32gui.FindWindow(None, program)
            if not hwnd:
                messagebox.showerror("Erro", f"Programa não encontrado: {program}")
                return
            
            self.skill_spam_running = True
            self.tab_skill_spam.set_running(True)
            self.log(f"⚡ Skill Spam INICIADO para: {program}")
            self.log_to_detail("\n" + "="*60, 'header')
            self.log_to_detail(f"⚡ SKILL SPAM INICIADO", 'header')
            self.log_to_detail(f"🖥️ Programa: {program}", 'info')
            
            hotkey = self.tab_skill_spam.get_hotkey()
            self.log(f"⌨️ Pressione {hotkey.upper()} para parar")
            
            # Inicia threads para cada skill
            self.skill_spam_threads = []
            for skill in skills:
                key = skill['key']
                interval = max(50, skill['interval']) / 1000.0  # Converte para segundos
                
                self.log_to_detail(f"  • Tecla '{key}' a cada {skill['interval']}ms", 'info')
                
                thread = threading.Thread(
                    target=self._skill_spam_loop,
                    args=(hwnd, key, interval),
                    daemon=True
                )
                self.skill_spam_threads.append(thread)
                thread.start()
            
        except ImportError:
            messagebox.showerror("Erro", "Instale pywin32: pip install pywin32")
        except Exception as e:
            self.log(f"Erro: {e}")
            messagebox.showerror("Erro", f"Erro ao iniciar spam: {e}")
    
    def stop_skill_spam(self):
        """Para o spam de skills."""
        self.skill_spam_running = False
        self.tab_skill_spam.set_running(False)
        
        # NÃO remove o hotkey - ele deve continuar funcionando para toggle
        
        self.log("⏹️ Skill Spam PARADO")
        self.log_to_detail("\n⏹️ SKILL SPAM PARADO", 'warning')
    
    def _skill_spam_loop(self, hwnd, key, interval):
        """Loop de spam para uma skill específica."""
        import win32gui
        import win32con
        import win32api
        
        # Mapeamento de teclas especiais
        vk_codes = {
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
            'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
            'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
            'space': 0x20, 'enter': 0x0D, 'tab': 0x09,
            'shift': 0x10, 'ctrl': 0x11, 'alt': 0x12,
            'esc': 0x1B, 'backspace': 0x08,
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        }
        
        # Obtém o código da tecla
        key_lower = key.lower()
        if key_lower in vk_codes:
            vk = vk_codes[key_lower]
        elif len(key_lower) == 1 and key_lower.isalpha():
            vk = ord(key_lower.upper())
        else:
            self.log(f"⚠️ Tecla não reconhecida: {key}")
            return
        
        while self.skill_spam_running:
            try:
                # Verifica se a janela ainda existe
                if not win32gui.IsWindow(hwnd):
                    self.log(f"⚠️ Janela fechada")
                    break
                
                # Envia a tecla para a janela
                win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk, 0)
                time.sleep(0.01)
                win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk, 0)
                
                time.sleep(interval)
                
            except Exception as e:
                self.log(f"Erro no spam: {e}")
                break
    
    # ============================================
    # MÉTODOS DE CAPTURA DE POSIÇÃO
    # ============================================
    
    def capture_key_position(self):
        """Captura posição da chave."""
        self._capture_position("CHAVE", self._set_key_position)
    
    def capture_orb_position(self):
        """Captura posição do Orb."""
        self._capture_position("ORB OF CHANCE", self._set_orb_position)
    
    def capture_bp_position(self):
        """Captura posição da BP."""
        self._capture_position("BP (slot vazio)", self._set_bp_position)
    
    def _capture_position(self, name, callback):
        """Captura genérica de posição."""
        self.log(f"Posicione o mouse sobre {name} e pressione ENTER...")
        messagebox.showinfo(
            f"Capturar Posição",
            f"Posicione o mouse sobre {name}\ne pressione ENTER"
        )
        
        def wait_for_enter():
            keyboard.wait('enter')
            pos = pyautogui.position()
            callback(pos)
        
        threading.Thread(target=wait_for_enter, daemon=True).start()
    
    def _set_key_position(self, pos):
        self.key_position = pos
        self.tab_keys.key_capture.set_position(pos[0], pos[1])
        self.log(f"✓ Posição da chave: {pos}")
        self.save_config()
    
    def _set_orb_position(self, pos):
        self.orb_position = pos
        self.tab_keys.orb_capture.set_position(pos[0], pos[1])
        self.log(f"✓ Posição do orb: {pos}")
        self.save_config()
    
    def _set_bp_position(self, pos):
        self.bp_position = pos
        self.tab_keys.bp_capture.set_position(pos[0], pos[1])
        self.log(f"✓ Posição da BP: {pos}")
        self.save_config()
    
    # ============================================
    # MÉTODOS DE PRESETS
    # ============================================
    
    def on_preset_selected(self, tab_type, name):
        """Callback quando um preset é selecionado."""
        if name == "+ Novo Preset":
            self._create_new_preset_dialog(tab_type)
        else:
            self._load_preset(tab_type, name)
    
    def save_current_preset(self, tab_type):
        """Salva o preset atual."""
        combo = self._get_preset_combo(tab_type)
        current_name = combo.get_selected()
        
        if current_name == "+ Novo Preset":
            self._create_new_preset_dialog(tab_type)
            return
        
        self._save_preset(tab_type, current_name)
        messagebox.showinfo("✓ Salvo", f"Preset '{current_name}' salvo!")
    
    def delete_preset_dialog(self, tab_type):
        """Exclui o preset selecionado."""
        combo = self._get_preset_combo(tab_type)
        current_preset = combo.get_selected()
        
        preset_list = self.preset_manager.get_preset_names(tab_type)
        
        if len(preset_list) <= 1:
            messagebox.showinfo("Info", "Deve haver pelo menos 1 preset")
            return
        
        if current_preset == "+ Novo Preset":
            messagebox.showinfo("Info", "Selecione um preset válido")
            return
        
        if messagebox.askyesno("Confirmar", f"Excluir '{current_preset}'?"):
            self.preset_manager.delete_preset(tab_type, current_preset)
            self._update_preset_combos()
            
            remaining = self.preset_manager.get_preset_names(tab_type)
            if remaining:
                combo.set_selected(remaining[0])
                self._load_preset(tab_type, remaining[0])
            
            self.log(f"Preset '{current_preset}' excluído")
    
    def _get_preset_combo(self, tab_type):
        """Retorna o combo de presets para o tipo."""
        if tab_type == 'values':
            return self.tab_values.preset_selector
        elif tab_type == 'search':
            return self.tab_search.preset_selector
        elif tab_type == 't7':
            return self.tab_t7.preset_selector
        else:
            return self.tab_keys.preset_selector
    
    def _create_new_preset_dialog(self, tab_type):
        """Abre diálogo para criar novo preset."""
        combo = self._get_preset_combo(tab_type)
        preset_names = self.preset_manager.get_preset_names(tab_type)
        if preset_names:
            combo.set_selected(preset_names[0])
        
        def on_create(name):
            self._save_preset(tab_type, name)
            combo.set_selected(name)
        
        NewPresetDialog(self.root, preset_names, on_create)
    
    def _save_preset(self, tab_type, name):
        """Salva um preset."""
        if tab_type == 'values':
            data = self.tab_values.get_entries_data()
        elif tab_type == 'search':
            data = {
                'attributes': self.tab_search.get_entries_data(),
                'mode': self.tab_search.get_mode(),
                'min_count': self.tab_search.get_min_count()
            }
        elif tab_type == 't7':
            data = self.tab_t7.get_entries_data()
        else:
            data = {
                'attributes': self.tab_keys.get_entries_data(),
                'mode': self.tab_keys.get_mode(),
                'min_count': self.tab_keys.get_min_count()
            }
        
        self.preset_manager.save_preset(tab_type, name, data)
        self._update_preset_combos()
        self.log(f"💾 Preset '{name}' salvo")
    
    def _load_preset(self, tab_type, name):
        """Carrega um preset."""
        if name == "+ Novo Preset" or not name:
            return
        
        data = self.preset_manager.get_preset(tab_type, name)
        if not data:
            return
        
        if tab_type == 'values':
            self.tab_values.load_data(data)
            self.tab_values.preset_selector.set_selected(name)
        elif tab_type == 'search':
            self.tab_search.load_data(data)
            self.tab_search.preset_selector.set_selected(name)
        elif tab_type == 't7':
            self.tab_t7.load_data(data)
            self.tab_t7.preset_selector.set_selected(name)
        else:
            self.tab_keys.load_data(data)
            self.tab_keys.preset_selector.set_selected(name)
        
        self.log(f"📂 Preset '{name}' carregado")
    
    def _update_preset_combos(self):
        """Atualiza os combos de presets."""
        self.preset_manager.ensure_default_presets()
        
        for tab_type in ['values', 'search', 't7', 'keys']:
            names = self.preset_manager.get_preset_names(tab_type) + ["+ Novo Preset"]
            combo = self._get_preset_combo(tab_type)
            combo.update_values(names)
    
    # ============================================
    # MÉTODOS DE CONFIGURAÇÃO
    # ============================================
    
    def save_config(self):
        """Salva configurações."""
        try:
            active_tab_name = self.tabview.get()
            tab_map = {
                "🎯 Valores Específicos": 0,
                "🔍 Busca de Atributos": 1,
                "⭐ Buscar T7": 2,
                "🔑 Automação de Chaves": 3,
                "⚡ Skill Spam": 4
            }
            active_tab = tab_map.get(active_tab_name, 0)
            
            config = {
                'region': self.region,
                'attributes': self.tab_values.get_entries_data(),
                'search_attributes': self.tab_search.get_entries_data(),
                'keys_attributes': self.tab_keys.get_entries_data(),
                't7_config': self.tab_t7.get_entries_data(),
                'skill_spam_config': self.tab_skill_spam.get_entries_data(),
                'delay': self.delay_var.get(),
                'click_delay': self.click_delay_var.get(),
                'max_attempts': self.max_attempts_var.get(),
                'active_tab': active_tab,
                'min_attributes_mode': self.tab_search.get_mode(),
                'min_attributes_count': self.tab_search.get_min_count(),
                'keys_min_mode': self.tab_keys.get_mode(),
                'keys_min_count': self.tab_keys.get_min_count(),
                'key_position': self.key_position,
                'orb_position': self.orb_position,
                'bp_position': self.bp_position,
                'hotkeys': self.hotkeys
            }
            
            self.config_manager.save_config(config)
            
        except Exception as e:
            self.log(f"⚠️ Erro ao salvar: {e}")
    
    def load_config(self):
        """Carrega configurações."""
        try:
            config = self.config_manager.load_config()
            if not config:
                self.log("📋 Nenhuma configuração anterior")
                return
            
            # Região
            if config.get('region'):
                self.region = tuple(config['region'])
                left, top, right, bottom = self.region
                self.region_label.configure(
                    text=f"✓ Região: {right-left}x{bottom-top}px",
                    text_color=self.colors['success']
                )
            
            # Delays
            if config.get('delay'):
                self.delay_var.set(config['delay'])
            if config.get('click_delay'):
                self.click_delay_var.set(config['click_delay'])
            if config.get('max_attempts'):
                self.max_attempts_var.set(config['max_attempts'])
            
            # Atributos
            if config.get('attributes'):
                self.tab_values.clear_entries()
                for attr in config['attributes']:
                    self.tab_values.add_row(attr.get('name', ''), attr.get('value', ''))
                if not self.tab_values.entries:
                    self.tab_values.add_row()
            
            if config.get('search_attributes'):
                self.tab_search.clear_entries()
                for attr in config['search_attributes']:
                    if isinstance(attr, str):
                        self.tab_search.add_row(attr, False)
                    else:
                        self.tab_search.add_row(attr.get('name', ''), attr.get('required', False))
                if not self.tab_search.entries:
                    self.tab_search.add_row()
            
            if config.get('keys_attributes'):
                self.tab_keys.clear_entries()
                for attr in config['keys_attributes']:
                    if isinstance(attr, str):
                        self.tab_keys.add_row(attr, False)
                    else:
                        self.tab_keys.add_row(attr.get('name', ''), attr.get('required', False))
                if not self.tab_keys.entries:
                    self.tab_keys.add_row()
            
            # Modos
            if config.get('min_attributes_mode'):
                self.tab_search.min_mode_var.set(config['min_attributes_mode'])
            if config.get('min_attributes_count'):
                self.tab_search.min_count_entry.delete(0, "end")
                self.tab_search.min_count_entry.insert(0, config['min_attributes_count'])
            
            if config.get('keys_min_mode'):
                self.tab_keys.min_mode_var.set(config['keys_min_mode'])
            if config.get('keys_min_count'):
                self.tab_keys.min_count_entry.delete(0, "end")
                self.tab_keys.min_count_entry.insert(0, config['keys_min_count'])
            
            # Posições
            if config.get('key_position'):
                self.key_position = tuple(config['key_position'])
                self.tab_keys.key_capture.set_position(*self.key_position)
            
            if config.get('orb_position'):
                self.orb_position = tuple(config['orb_position'])
                self.tab_keys.orb_capture.set_position(*self.orb_position)
            
            if config.get('bp_position'):
                self.bp_position = tuple(config['bp_position'])
                self.tab_keys.bp_capture.set_position(*self.bp_position)
            
            # Configuração T7
            if config.get('t7_config'):
                self.tab_t7.load_data(config['t7_config'])
            
            # Configuração Skill Spam
            if config.get('skill_spam_config'):
                self.tab_skill_spam.load_data(config['skill_spam_config'])
            
            # Aba ativa
            if config.get('active_tab') is not None:
                try:
                    tab_names = ["🎯 Valores Específicos", "🔍 Busca de Atributos", "⭐ Buscar T7", "🔑 Automação de Chaves", "⚡ Skill Spam"]
                    idx = config['active_tab']
                    if 0 <= idx < len(tab_names):
                        self.tabview.set(tab_names[idx])
                except:
                    pass
            
            # Atalhos
            if config.get('hotkeys'):
                self.hotkeys = config['hotkeys']
                self._update_hotkey_labels()
            
            self._update_preset_combos()
            self.log("✓ Configurações carregadas")
            
        except Exception as e:
            self.log(f"⚠️ Erro ao carregar: {e}")
    
    # ============================================
    # MÉTODOS DE UI
    # ============================================
    
    def update_status(self, text, status_type='info'):
        """Atualiza o status."""
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
        """Log mensagem."""
        try:
            if self.log_text:
                timestamp = time.strftime("%H:%M:%S")
                self.log_text.insert("end", f"[{timestamp}] {message}\n")
                self.log_text.see("end")
                self.root.update_idletasks()
        except:
            pass
    
    def log_to_detail(self, message, tag='info'):
        """Log na janela detalhada."""
        self.log_window.log(message, tag)
    
    def _toggle_theme(self):
        """Alterna tema."""
        current = ctk.get_appearance_mode()
        ctk.set_appearance_mode("light" if current == "Dark" else "dark")
    
    def _open_hotkeys_settings(self):
        """Abre configurações de atalhos."""
        try:
            keyboard.unhook_all_hotkeys()
        except:
            pass
        
        def on_save(new_hotkeys):
            self.hotkeys = new_hotkeys
            self._update_hotkey_labels()
            self._setup_local_hotkeys()
            self.setup_global_hotkeys()
            self.save_config()
        
        HotkeySettingsDialog(self.root, self.hotkeys, on_save)
    
    def _update_hotkey_labels(self):
        """Atualiza labels com atalhos."""
        self.btn_region.configure(text=f"🎯 Selecionar Região ({self.hotkeys['region']})")
        self.btn_test.configure(text=f"🔍 Testar Captura ({self.hotkeys['test']})")
        self.start_button.configure(text=f"▶ INICIAR ({self.hotkeys['start']})")
        self.stop_button.configure(text=f"⬛ PARAR ({self.hotkeys['stop']})")
        self.tab_keys.update_instructions(self.hotkeys)
        self.tab_t7.update_instructions(self.hotkeys)
    
    def _check_updates_auto(self):
        """Verifica atualizações automaticamente ao iniciar."""
        def check():
            try:
                updater = AutoUpdater()
                result = updater.check_for_updates()
                
                if result.get('available'):
                    self.root.after(0, lambda: self._show_update_available(result, updater))
            except Exception as e:
                print(f"Erro ao verificar atualizações: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def _show_update_available(self, result, updater):
        """Mostra notificação de atualização disponível."""
        self.log(f"🆕 Nova versão disponível: v{result['version']}")
        UpdateDialog(
            self.root, result,
            lambda url: self._perform_update(updater, url)
        )
    
    def _check_updates_manual(self):
        """Verifica atualizações manualmente."""
        self.log("🔍 Verificando atualizações...")
        
        def check():
            updater = AutoUpdater()
            result = updater.check_for_updates()
            
            if result.get('available'):
                self.root.after(0, lambda: UpdateDialog(
                    self.root, result,
                    lambda url: self._perform_update(updater, url)
                ))
            elif result.get('error'):
                self.root.after(0, lambda: messagebox.showerror(
                    "Erro", f"Erro: {result['error']}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "✓ Atualizado", f"Versão {APP_VERSION} é a mais recente"
                ))
        
        threading.Thread(target=check, daemon=True).start()
    
    def _perform_update(self, updater, download_url):
        """Executa atualização."""
        progress_dialog = UpdateProgressDialog(self.root)
        
        def do_update():
            success = updater.download_and_install(
                download_url,
                progress_dialog.update_progress
            )
            if success:
                self.root.after(100, lambda: self._finish_update(progress_dialog))
            else:
                self.root.after(0, lambda: self._update_failed(progress_dialog))
        
        threading.Thread(target=do_update, daemon=True).start()
    
    def _finish_update(self, progress_dialog):
        """Finaliza atualização."""
        progress_dialog.destroy()
        messagebox.showinfo("✓ Atualização", "Atualização baixada! Reiniciando...")
        self.root.quit()
    
    def _update_failed(self, progress_dialog):
        """Trata falha na atualização."""
        progress_dialog.destroy()
        messagebox.showerror("Erro", "Falha ao instalar atualização")
    
    def _on_closing(self):
        """Callback ao fechar."""
        self.save_config()
        self.log("💾 Configurações salvas")
        self.root.destroy()
