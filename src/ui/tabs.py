"""
Abas da interface principal.
"""
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config import UI_CONFIG
from src.ui.components import AttributeRow, PresetSelector, PositionCapture


class BaseTab:
    """Classe base para abas."""
    
    def __init__(self, parent, app):
        """
        Inicializa a aba.
        
        Args:
            parent: Widget pai (tab do CTkTabview).
            app: Referência para a aplicação principal.
        """
        self.parent = parent
        self.app = app
        self.entries = []
    
    def get_entries_data(self):
        """Retorna dados de todas as entradas."""
        return [entry.to_dict() for entry in self.entries if entry.get_name()]
    
    def clear_entries(self):
        """Remove todas as entradas."""
        for entry in self.entries[:]:
            entry.destroy()
        self.entries.clear()
    
    def _on_delete_entry(self, entry):
        """Callback para exclusão de entrada."""
        if len(self.entries) <= 1:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos um atributo")
            return
        
        self.entries.remove(entry)
        entry.destroy()
        self.app.log("✓ Atributo removido")
        self.app.save_config()


class ValuesTab(BaseTab):
    """Aba de busca por valores específicos."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.preset_selector = None
        self.inner_frame = None
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da aba."""
        # Header com título e presets
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text="📝 Atributos e Valores Alvos",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(side="left")
        
        # Seletor de presets
        self.preset_selector = PresetSelector(
            header_frame,
            on_select=lambda x: self.app.on_preset_selected('values', x),
            on_save=lambda: self.app.save_current_preset('values'),
            on_delete=lambda: self.app.delete_preset_dialog('values')
        )
        
        # Frame scrollável para atributos
        attr_frame = ctk.CTkScrollableFrame(self.parent, corner_radius=10, height=220)
        attr_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.inner_frame = attr_frame
        
        # Adicionar primeira linha
        self.add_row()
        
        # Botão adicionar
        ctk.CTkButton(
            self.parent, text="➕ ADICIONAR ATRIBUTO",
            command=self.add_row, height=40,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#2563eb", hover_color="#1d4ed8"
        ).pack(pady=10, padx=15, fill="x")
        
        # Instruções
        ctk.CTkLabel(
            self.parent,
            text="💡 Digite o nome do atributo e o valor desejado. Ex: Strength = 15",
            text_color="#6b7280", wraplength=600,
            font=(UI_CONFIG['font_family'], 10)
        ).pack(pady=(0, 15), padx=15)
    
    def add_row(self, name_val="", value_val=""):
        """Adiciona uma linha de atributo."""
        entry = AttributeRow(
            self.inner_frame,
            on_delete=self._on_delete_entry,
            name_val=name_val,
            value_val=value_val,
            show_value=True,
            show_required=False
        )
        self.entries.append(entry)
        
        if name_val or value_val:
            self.app.root.after(100, self.app.save_config)
    
    def load_data(self, data):
        """Carrega dados de um preset."""
        self.clear_entries()
        
        for attr in data:
            self.add_row(attr.get('name', ''), attr.get('value', ''))
        
        if not self.entries:
            self.add_row()


class SearchTab(BaseTab):
    """Aba de busca por presença de atributos."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.preset_selector = None
        self.inner_frame = None
        self.min_mode_var = None
        self.min_count_entry = None
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da aba."""
        # Header
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text="📋 Atributos para Buscar",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(side="left")
        
        # Seletor de presets
        self.preset_selector = PresetSelector(
            header_frame,
            on_select=lambda x: self.app.on_preset_selected('search', x),
            on_save=lambda: self.app.save_current_preset('search'),
            on_delete=lambda: self.app.delete_preset_dialog('search')
        )
        
        # Frame scrollável
        search_frame = ctk.CTkScrollableFrame(self.parent, corner_radius=10, height=190)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.inner_frame = search_frame
        
        # Adicionar primeira linha
        self.add_row()
        
        # Botão adicionar
        ctk.CTkButton(
            self.parent, text="➕ ADICIONAR ATRIBUTO",
            command=self.add_row, height=40,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#2563eb", hover_color="#1d4ed8"
        ).pack(pady=10, padx=15, fill="x")
        
        # Configuração de modo
        count_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        count_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            count_frame, text="🎯 Modo:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        self.min_mode_var = tk.StringVar(value="ALL")
        
        ctk.CTkRadioButton(
            count_frame, text="TODOS", variable=self.min_mode_var,
            value="ALL", font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            count_frame, text="Mínimo:", variable=self.min_mode_var,
            value="MIN", font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        self.min_count_entry = ctk.CTkEntry(count_frame, width=60, placeholder_text="3", height=35)
        self.min_count_entry.insert(0, "3")
        self.min_count_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            count_frame, text="atributo(s)",
            font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        # Instruções
        ctk.CTkLabel(
            self.parent,
            text="💡 Busca PRESENÇA de atributos | ⭐ Obrigatório = sempre deve aparecer no modo MÍNIMO",
            text_color="#6b7280", wraplength=600,
            font=(UI_CONFIG['font_family'], 10)
        ).pack(pady=(0, 15), padx=15)
    
    def add_row(self, name_val="", required_val=False):
        """Adiciona uma linha de atributo."""
        entry = AttributeRow(
            self.inner_frame,
            on_delete=self._on_delete_entry,
            name_val=name_val,
            show_value=False,
            show_required=True
        )
        if required_val:
            entry.set_required(required_val)
        self.entries.append(entry)
        
        if name_val:
            self.app.root.after(100, self.app.save_config)
    
    def load_data(self, data):
        """Carrega dados de um preset."""
        self.clear_entries()
        
        for attr in data.get('attributes', []):
            self.add_row(attr.get('name', ''), attr.get('required', False))
        
        if not self.entries:
            self.add_row()
        
        # Carrega modo
        self.min_mode_var.set(data.get('mode', 'ALL'))
        self.min_count_entry.delete(0, 'end')
        self.min_count_entry.insert(0, data.get('min_count', '3'))
    
    def get_mode(self):
        """Retorna o modo selecionado."""
        return self.min_mode_var.get()
    
    def get_min_count(self):
        """Retorna a contagem mínima."""
        return self.min_count_entry.get()


class KeysTab(BaseTab):
    """Aba de automação de chaves."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.preset_selector = None
        self.inner_frame = None
        self.min_mode_var = None
        self.min_count_entry = None
        self.key_capture = None
        self.orb_capture = None
        self.bp_capture = None
        self.instructions_label = None
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da aba."""
        # Header
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text="🔑 Atributos Desejados nas Chaves",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(side="left")
        
        # Seletor de presets
        self.preset_selector = PresetSelector(
            header_frame,
            on_select=lambda x: self.app.on_preset_selected('keys', x),
            on_save=lambda: self.app.save_current_preset('keys'),
            on_delete=lambda: self.app.delete_preset_dialog('keys')
        )
        
        # Frame scrollável
        search_frame = ctk.CTkScrollableFrame(self.parent, corner_radius=10, height=150)
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        self.inner_frame = search_frame
        
        # Adicionar primeira linha
        self.add_row()
        
        # Botão adicionar
        ctk.CTkButton(
            self.parent, text="➕ ADICIONAR ATRIBUTO",
            command=self.add_row, height=40,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#2563eb", hover_color="#1d4ed8"
        ).pack(pady=10, padx=15, fill="x")
        
        # Configuração de modo
        count_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        count_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            count_frame, text="🎯 Modo:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        self.min_mode_var = tk.StringVar(value="ALL")
        
        ctk.CTkRadioButton(
            count_frame, text="TODOS", variable=self.min_mode_var,
            value="ALL", font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            count_frame, text="Mínimo:", variable=self.min_mode_var,
            value="MIN", font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        self.min_count_entry = ctk.CTkEntry(count_frame, width=60, placeholder_text="2", height=35)
        self.min_count_entry.insert(0, "2")
        self.min_count_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            count_frame, text="atributo(s)",
            font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=5)
        
        # Configuração de Posições
        pos_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        pos_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            pos_frame, text="📍 Configurar Posições",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(anchor="w", pady=15, padx=15)
        
        # Posição da Chave
        self.key_capture = PositionCapture(
            pos_frame, "📍 CAPTURAR CHAVE",
            lambda: self.app.capture_key_position()
        )
        
        # Posição do Orb
        self.orb_capture = PositionCapture(
            pos_frame, "🔮 CAPTURAR ORB",
            lambda: self.app.capture_orb_position()
        )
        
        # Posição da BP
        self.bp_capture = PositionCapture(
            pos_frame, "🎒 CAPTURAR BP",
            lambda: self.app.capture_bp_position()
        )
        
        # Instruções
        self.instructions_label = ctk.CTkLabel(
            self.parent,
            text="💡 1. Configure região (F1) | 2. Capture posições | 3. F5 inicia automação",
            text_color="#6b7280", wraplength=600,
            font=(UI_CONFIG['font_family'], 10)
        )
        self.instructions_label.pack(pady=(0, 15), padx=15)
    
    def add_row(self, name_val="", required_val=False):
        """Adiciona uma linha de atributo."""
        entry = AttributeRow(
            self.inner_frame,
            on_delete=self._on_delete_entry,
            name_val=name_val,
            show_value=False,
            show_required=True
        )
        if required_val:
            entry.set_required(required_val)
        self.entries.append(entry)
        
        if name_val:
            self.app.root.after(100, self.app.save_config)
    
    def load_data(self, data):
        """Carrega dados de um preset."""
        self.clear_entries()
        
        for attr in data.get('attributes', []):
            self.add_row(attr.get('name', ''), attr.get('required', False))
        
        if not self.entries:
            self.add_row()
        
        # Carrega modo
        self.min_mode_var.set(data.get('mode', 'ALL'))
        self.min_count_entry.delete(0, 'end')
        self.min_count_entry.insert(0, data.get('min_count', '2'))
    
    def get_mode(self):
        """Retorna o modo selecionado."""
        return self.min_mode_var.get()
    
    def get_min_count(self):
        """Retorna a contagem mínima."""
        return self.min_count_entry.get()
    
    def update_instructions(self, hotkeys):
        """Atualiza o texto de instruções com os atalhos."""
        self.instructions_label.configure(
            text=f"💡 1. Configure região ({hotkeys['region']}) | 2. Capture posições | 3. {hotkeys['start']} inicia automação"
        )


class T7Tab(BaseTab):
    """Aba de busca por atributos T7."""
    
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.preset_selector = None
        self.inner_frame = None
        self.mode_var = None
        self.specific_attr_entry = None
        self.instructions_label = None
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da aba."""
        # Header
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text="⭐ Buscar Atributo T7",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(side="left")
        
        # Seletor de presets
        self.preset_selector = PresetSelector(
            header_frame,
            on_select=lambda x: self.app.on_preset_selected('t7', x),
            on_save=lambda: self.app.save_current_preset('t7'),
            on_delete=lambda: self.app.delete_preset_dialog('t7')
        )
        
        # Explicação
        info_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray85", "gray25"))
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            info_frame,
            text="🎯 Esta aba rola até encontrar um atributo com tier T7.\n"
                 "T7 é o tier mais alto e aparece como 'T7' antes do nome do atributo.",
            font=(UI_CONFIG['font_family'], 11),
            text_color=("gray30", "gray70"),
            justify="left"
        ).pack(padx=15, pady=15, anchor="w")
        
        # Modo de busca
        mode_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        mode_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            mode_frame, text="🔍 Modo de Busca:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.mode_var = tk.StringVar(value="ANY")
        
        # Opção 1: Qualquer T7
        any_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        any_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkRadioButton(
            any_frame, text="🌟 Qualquer atributo T7",
            variable=self.mode_var, value="ANY",
            font=(UI_CONFIG['font_family'], 12),
            command=self._on_mode_change
        ).pack(side="left")
        
        ctk.CTkLabel(
            any_frame, text="(para quando qualquer T7 aparecer)",
            font=(UI_CONFIG['font_family'], 10),
            text_color="gray50"
        ).pack(side="left", padx=10)
        
        # Opção 2: T7 Específico
        specific_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        specific_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkRadioButton(
            specific_frame, text="🎯 T7 em atributo específico:",
            variable=self.mode_var, value="SPECIFIC",
            font=(UI_CONFIG['font_family'], 12),
            command=self._on_mode_change
        ).pack(side="left")
        
        self.specific_attr_entry = ctk.CTkEntry(
            specific_frame, width=200, height=35,
            placeholder_text="Ex: Mana, Strength, Life...",
            font=(UI_CONFIG['font_family'], 11),
            state="disabled"
        )
        self.specific_attr_entry.pack(side="left", padx=10)
        
        # Frame para múltiplos atributos específicos
        multi_frame = ctk.CTkFrame(mode_frame, fg_color="transparent")
        multi_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        ctk.CTkLabel(
            multi_frame,
            text="💡 Para múltiplos atributos, separe por vírgula: Mana, Life, Strength",
            font=(UI_CONFIG['font_family'], 10),
            text_color="gray50"
        ).pack(anchor="w", padx=25)
        
        # Exemplos de T7
        examples_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        examples_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            examples_frame, text="📋 Exemplos de atributos T7:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        examples = [
            "T7 Mana: +274",
            "T7 Mana Percent: +113%",
            "T7 Life: +350",
            "T7 Strength: +45",
            "T7 Energy Shield Percent: +50%"
        ]
        
        for example in examples:
            ctk.CTkLabel(
                examples_frame,
                text=f"  • {example}",
                font=(UI_CONFIG['font_family'], 10),
                text_color=("#d97706", "#fbbf24")  # Cor laranja/amarela como no jogo
            ).pack(anchor="w", padx=15, pady=2)
        
        ctk.CTkFrame(examples_frame, height=10, fg_color="transparent").pack()
        
        # Botão de teste
        test_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        test_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        self.test_button = ctk.CTkButton(
            test_frame, text="🔍 TESTAR CAPTURA T7",
            command=lambda: self.app.test_t7_capture(),
            height=40, width=200,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#7c3aed", hover_color="#6d28d9"
        )
        self.test_button.pack(side="left")
        
        self.test_result_label = ctk.CTkLabel(
            test_frame, text="",
            font=(UI_CONFIG['font_family'], 10),
            text_color="#6b7280"
        )
        self.test_result_label.pack(side="left", padx=15)
        
        # Instruções
        self.instructions_label = ctk.CTkLabel(
            self.parent,
            text="💡 1. Configure a região (F1) | 2. Escolha o modo | 3. F5 para iniciar",
            text_color="#6b7280", wraplength=600,
            font=(UI_CONFIG['font_family'], 10)
        )
        self.instructions_label.pack(pady=(5, 15), padx=15)
    
    def _on_mode_change(self):
        """Callback quando o modo muda."""
        if self.mode_var.get() == "SPECIFIC":
            self.specific_attr_entry.configure(state="normal")
        else:
            self.specific_attr_entry.configure(state="disabled")
    
    def get_mode(self):
        """Retorna o modo selecionado."""
        return self.mode_var.get()
    
    def get_specific_attributes(self):
        """Retorna lista de atributos específicos."""
        text = self.specific_attr_entry.get().strip()
        if not text:
            return []
        # Separa por vírgula e limpa espaços
        return [attr.strip().lower() for attr in text.split(',') if attr.strip()]
    
    def load_data(self, data):
        """Carrega dados de um preset."""
        if isinstance(data, dict):
            self.mode_var.set(data.get('mode', 'ANY'))
            self.specific_attr_entry.delete(0, 'end')
            attrs = data.get('specific_attributes', [])
            if attrs:
                self.specific_attr_entry.insert(0, ', '.join(attrs))
            self._on_mode_change()
    
    def get_entries_data(self):
        """Retorna dados da configuração."""
        return {
            'mode': self.get_mode(),
            'specific_attributes': self.get_specific_attributes()
        }
    
    def update_instructions(self, hotkeys):
        """Atualiza o texto de instruções com os atalhos."""
        self.instructions_label.configure(
            text=f"💡 1. Configure a região ({hotkeys['region']}) | 2. Escolha o modo | 3. {hotkeys['start']} para iniciar"
        )


class SkillRow:
    """Linha de configuração de skill para spam."""
    
    def __init__(self, parent, on_delete, key_val="", interval_val="100"):
        """
        Cria uma linha de skill.
        
        Args:
            parent: Widget pai.
            on_delete: Callback para exclusão.
            key_val: Tecla inicial.
            interval_val: Intervalo em ms.
        """
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.frame.pack(fill="x", pady=5, padx=5)
        
        # Tecla
        ctk.CTkLabel(
            self.frame, text="Tecla:",
            font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=(0, 5))
        
        self.key_entry = ctk.CTkEntry(
            self.frame, width=70, height=35,
            placeholder_text="F1, 1, Q",
            font=(UI_CONFIG['font_family'], 11)
        )
        self.key_entry.pack(side="left", padx=2)
        if key_val:
            self.key_entry.insert(0, key_val)
        
        # Botão capturar tecla
        self.capture_btn = ctk.CTkButton(
            self.frame, text="⌨️", width=35, height=35,
            command=self._capture_key,
            fg_color="#7c3aed", hover_color="#6d28d9"
        )
        self.capture_btn.pack(side="left", padx=2)
        
        # Intervalo
        ctk.CTkLabel(
            self.frame, text="Intervalo (ms):",
            font=(UI_CONFIG['font_family'], 11)
        ).pack(side="left", padx=(10, 5))
        
        self.interval_entry = ctk.CTkEntry(
            self.frame, width=70, height=35,
            placeholder_text="100",
            font=(UI_CONFIG['font_family'], 11)
        )
        self.interval_entry.pack(side="left", padx=5)
        self.interval_entry.insert(0, interval_val)
        
        # Checkbox ativo
        self.active_var = tk.BooleanVar(value=True)
        self.active_check = ctk.CTkCheckBox(
            self.frame, text="Ativo",
            variable=self.active_var,
            font=(UI_CONFIG['font_family'], 10),
            width=60
        )
        self.active_check.pack(side="left", padx=10)
        
        # Botão remover
        self.delete_btn = ctk.CTkButton(
            self.frame, text="✕", width=35, height=35,
            fg_color="#dc2626", hover_color="#b91c1c",
            command=lambda: on_delete(self)
        )
        self.delete_btn.pack(side="right", padx=5)
    
    def _capture_key(self):
        """Captura uma tecla pressionada."""
        self.capture_btn.configure(text="...")
        self.key_entry.delete(0, 'end')
        
        import keyboard
        
        def on_key(event):
            key = event.name
            self.key_entry.insert(0, key.upper())
            self.capture_btn.configure(text="⌨️")
            keyboard.unhook(hook)
        
        hook = keyboard.on_press(on_key)
    
    def get_key(self):
        """Retorna a tecla."""
        return self.key_entry.get().strip().lower()
    
    def get_interval(self):
        """Retorna o intervalo em ms."""
        try:
            return int(self.interval_entry.get())
        except:
            return 100
    
    def is_active(self):
        """Retorna se está ativo."""
        return self.active_var.get()
    
    def to_dict(self):
        """Retorna dados como dicionário."""
        return {
            'key': self.get_key(),
            'interval': self.get_interval(),
            'active': self.is_active()
        }
    
    def destroy(self):
        """Remove o widget."""
        self.frame.destroy()


class SkillSpamTab:
    """Aba de spam de skills."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.skill_rows = []
        self.target_window = None
        self._build_ui()
    
    def _build_ui(self):
        """Constrói a interface da aba."""
        # Header
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))
        
        ctk.CTkLabel(
            header_frame, text="⚡ Spam de Skills",
            font=(UI_CONFIG['font_family'], 14, "bold")
        ).pack(side="left")
        
        # Explicação
        info_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray85", "gray25"))
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            info_frame,
            text="🎮 Envia teclas automaticamente para o programa selecionado.\n"
                 "Configure as teclas e intervalos, depois inicie o spam.",
            font=(UI_CONFIG['font_family'], 11),
            text_color=("gray30", "gray70"),
            justify="left"
        ).pack(padx=15, pady=15, anchor="w")
        
        # Seleção de programa
        program_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        program_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            program_frame, text="🖥️ Programa Alvo:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(side="left", padx=15, pady=15)
        
        self.program_combo = ctk.CTkComboBox(
            program_frame, width=300, height=35,
            values=["Clique para atualizar..."],
            font=(UI_CONFIG['font_family'], 11),
            state="readonly"
        )
        self.program_combo.pack(side="left", padx=10, pady=15)
        self.program_combo.set("Selecione um programa")
        
        self.refresh_btn = ctk.CTkButton(
            program_frame, text="🔄", width=40, height=35,
            command=self._refresh_programs,
            fg_color="#3b82f6", hover_color="#2563eb"
        )
        self.refresh_btn.pack(side="left", padx=5, pady=15)
        
        # Hotkey para iniciar/parar
        hotkey_frame = ctk.CTkFrame(self.parent, corner_radius=10, fg_color=("gray90", "gray20"))
        hotkey_frame.pack(fill="x", pady=10, padx=15)
        
        ctk.CTkLabel(
            hotkey_frame, text="⌨️ Tecla Iniciar/Parar:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(side="left", padx=15, pady=15)
        
        self.hotkey_entry = ctk.CTkEntry(
            hotkey_frame, width=100, height=35,
            placeholder_text="F8",
            font=(UI_CONFIG['font_family'], 11)
        )
        self.hotkey_entry.pack(side="left", padx=10, pady=15)
        self.hotkey_entry.insert(0, "F8")
        # Atualiza hotkeys quando o usuário sair do campo
        self.hotkey_entry.bind('<FocusOut>', lambda e: self.app.setup_global_hotkeys())
        
        self.hotkey_btn = ctk.CTkButton(
            hotkey_frame, text="📝 Capturar",
            command=self._capture_hotkey,
            width=100, height=35,
            fg_color="#7c3aed", hover_color="#6d28d9"
        )
        self.hotkey_btn.pack(side="left", padx=5, pady=15)
        
        # Status
        self.status_label = ctk.CTkLabel(
            hotkey_frame, text="⏹️ Parado",
            font=(UI_CONFIG['font_family'], 11, "bold"),
            text_color="#6b7280"
        )
        self.status_label.pack(side="right", padx=15, pady=15)
        
        # Frame de skills
        skills_header = ctk.CTkFrame(self.parent, fg_color="transparent")
        skills_header.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            skills_header, text="🎯 Skills para Spam:",
            font=(UI_CONFIG['font_family'], 12, "bold")
        ).pack(side="left")
        
        # Frame scrollável para skills
        self.skills_frame = ctk.CTkScrollableFrame(self.parent, corner_radius=10, height=150)
        self.skills_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Adicionar primeira skill
        self.add_skill_row()
        
        # Botões
        buttons_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkButton(
            buttons_frame, text="➕ Adicionar Skill",
            command=self.add_skill_row,
            height=40, width=150,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#2563eb", hover_color="#1d4ed8"
        ).pack(side="left", padx=5)
        
        self.start_btn = ctk.CTkButton(
            buttons_frame, text="▶️ INICIAR SPAM",
            command=lambda: self.app.toggle_skill_spam(),
            height=40, width=180,
            font=(UI_CONFIG['font_family'], 12, "bold"),
            fg_color="#22c55e", hover_color="#16a34a"
        )
        self.start_btn.pack(side="right", padx=5)
        
        # Instruções
        ctk.CTkLabel(
            self.parent,
            text="💡 Teclas: a-z, 0-9, F1-F12, Insert, Delete, Home, End, PageUp/Down, Setas, Numpad | Mín: 50ms",
            text_color="#6b7280", wraplength=600,
            font=(UI_CONFIG['font_family'], 10)
        ).pack(pady=(5, 15), padx=15)
        
        # Atualiza lista de programas
        self.app.root.after(500, self._refresh_programs)
    
    def add_skill_row(self, key_val="", interval_val="100"):
        """Adiciona uma linha de skill."""
        row = SkillRow(
            self.skills_frame,
            on_delete=self._on_delete_skill,
            key_val=key_val,
            interval_val=str(interval_val)
        )
        self.skill_rows.append(row)
    
    def _on_delete_skill(self, row):
        """Remove uma skill."""
        if len(self.skill_rows) <= 1:
            messagebox.showwarning("Aviso", "É necessário ter pelo menos uma skill")
            return
        
        self.skill_rows.remove(row)
        row.destroy()
    
    def _refresh_programs(self):
        """Atualiza lista de programas abertos."""
        try:
            import win32gui
            
            windows = []
            
            def enum_handler(hwnd, results):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title and len(title) > 1:
                        results.append(title)
            
            win32gui.EnumWindows(enum_handler, windows)
            
            # Remove duplicatas e ordena
            windows = sorted(list(set(windows)))
            
            if windows:
                self.program_combo.configure(values=windows)
                self.app.log(f"✓ {len(windows)} programas encontrados")
            else:
                self.program_combo.configure(values=["Nenhum programa encontrado"])
                
        except ImportError:
            # Fallback se win32gui não estiver disponível
            self.program_combo.configure(values=["Instale pywin32: pip install pywin32"])
            self.app.log("⚠️ pywin32 não instalado")
        except Exception as e:
            self.app.log(f"Erro ao listar programas: {e}")
    
    def _capture_hotkey(self):
        """Captura uma tecla para hotkey."""
        self.hotkey_btn.configure(text="Pressione...")
        self.hotkey_entry.delete(0, 'end')
        
        import keyboard
        
        def on_key(event):
            key = event.name
            self.hotkey_entry.insert(0, key.upper())
            self.hotkey_btn.configure(text="📝 Capturar")
            keyboard.unhook(hook)
            # Atualiza os hotkeys globais imediatamente
            self.app.root.after(100, self.app.setup_global_hotkeys)
        
        hook = keyboard.on_press(on_key)
    
    def get_selected_program(self):
        """Retorna o programa selecionado."""
        return self.program_combo.get()
    
    def get_hotkey(self):
        """Retorna a hotkey configurada."""
        return self.hotkey_entry.get().strip().lower()
    
    def get_skills_data(self):
        """Retorna dados de todas as skills ativas."""
        return [row.to_dict() for row in self.skill_rows if row.is_active() and row.get_key()]
    
    def set_running(self, is_running):
        """Atualiza o estado visual."""
        if is_running:
            self.start_btn.configure(
                text="⏹️ PARAR SPAM",
                fg_color="#dc2626",
                hover_color="#b91c1c"
            )
            self.status_label.configure(
                text="▶️ Rodando...",
                text_color="#22c55e"
            )
        else:
            self.start_btn.configure(
                text="▶️ INICIAR SPAM",
                fg_color="#22c55e",
                hover_color="#16a34a"
            )
            self.status_label.configure(
                text="⏹️ Parado",
                text_color="#6b7280"
            )
    
    def load_data(self, data):
        """Carrega dados salvos."""
        if not isinstance(data, dict):
            return
        
        # Limpa skills existentes
        for row in self.skill_rows[:]:
            row.destroy()
        self.skill_rows.clear()
        
        # Carrega skills
        skills = data.get('skills', [])
        for skill in skills:
            self.add_skill_row(
                key_val=skill.get('key', ''),
                interval_val=skill.get('interval', 100)
            )
        
        if not self.skill_rows:
            self.add_skill_row()
        
        # Carrega hotkey
        if data.get('hotkey'):
            self.hotkey_entry.delete(0, 'end')
            self.hotkey_entry.insert(0, data['hotkey'])
        
        # Carrega programa
        if data.get('program'):
            self.program_combo.set(data['program'])
    
    def get_entries_data(self):
        """Retorna dados para salvar."""
        return {
            'skills': self.get_skills_data(),
            'hotkey': self.get_hotkey(),
            'program': self.get_selected_program()
        }
