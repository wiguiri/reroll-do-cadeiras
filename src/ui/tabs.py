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
