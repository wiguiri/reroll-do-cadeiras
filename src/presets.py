"""
Módulo de gerenciamento de presets.
Responsável por salvar, carregar e gerenciar presets de configuração.
"""
import os
import json

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import PRESETS_FILE, CONFIG_FILE


class PresetManager:
    """Gerenciador de presets de configuração."""
    
    def __init__(self, presets_file=None, config_file=None):
        self.presets_file = presets_file or PRESETS_FILE
        self.config_file = config_file or CONFIG_FILE
    
    def load_all_presets(self):
        """
        Carrega todos os presets do arquivo.
        
        Returns:
            dict: Dicionário com todos os presets por tipo.
        """
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar presets: {e}")
        
        return {'values': {}, 'search': {}, 'keys': {}}
    
    def save_all_presets(self, presets):
        """
        Salva todos os presets no arquivo.
        
        Args:
            presets: Dicionário com todos os presets.
        """
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(presets, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar presets: {e}")
    
    def get_preset_names(self, tab_type):
        """
        Retorna lista de nomes de presets para um tipo de aba.
        
        Args:
            tab_type: Tipo da aba ('values', 'search', 'keys').
            
        Returns:
            list: Lista de nomes de presets.
        """
        presets = self.load_all_presets()
        return list(presets.get(tab_type, {}).keys())
    
    def get_preset(self, tab_type, name):
        """
        Retorna um preset específico.
        
        Args:
            tab_type: Tipo da aba.
            name: Nome do preset.
            
        Returns:
            dict ou list: Dados do preset ou None.
        """
        presets = self.load_all_presets()
        return presets.get(tab_type, {}).get(name)
    
    def save_preset(self, tab_type, name, data):
        """
        Salva um preset específico.
        
        Args:
            tab_type: Tipo da aba.
            name: Nome do preset.
            data: Dados do preset.
        """
        presets = self.load_all_presets()
        
        if tab_type not in presets:
            presets[tab_type] = {}
        
        presets[tab_type][name] = data
        self.save_all_presets(presets)
    
    def delete_preset(self, tab_type, name):
        """
        Exclui um preset.
        
        Args:
            tab_type: Tipo da aba.
            name: Nome do preset.
            
        Returns:
            bool: True se excluiu com sucesso.
        """
        presets = self.load_all_presets()
        
        if name in presets.get(tab_type, {}):
            del presets[tab_type][name]
            self.save_all_presets(presets)
            return True
        
        return False
    
    def ensure_default_presets(self):
        """
        Garante que existe pelo menos um preset padrão em cada tipo.
        """
        presets = self.load_all_presets()
        modified = False
        
        for tab_type in ['values', 'search', 'keys']:
            if 'Preset 1' not in presets.get(tab_type, {}):
                if tab_type not in presets:
                    presets[tab_type] = {}
                
                if tab_type == 'values':
                    presets[tab_type]['Preset 1'] = []
                else:
                    presets[tab_type]['Preset 1'] = {
                        'attributes': [],
                        'mode': 'ALL',
                        'min_count': '3' if tab_type == 'search' else '2'
                    }
                modified = True
        
        if modified:
            self.save_all_presets(presets)
        
        return presets


class ConfigManager:
    """Gerenciador de configurações do aplicativo."""
    
    def __init__(self, config_file=None):
        self.config_file = config_file or CONFIG_FILE
    
    def load_config(self):
        """
        Carrega configurações do arquivo.
        
        Returns:
            dict: Configurações carregadas ou dicionário vazio.
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
        
        return {}
    
    def save_config(self, config):
        """
        Salva configurações no arquivo.
        
        Args:
            config: Dicionário de configurações.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")
    
    def get(self, key, default=None):
        """
        Retorna um valor de configuração.
        
        Args:
            key: Chave da configuração.
            default: Valor padrão se não existir.
            
        Returns:
            Valor da configuração ou default.
        """
        config = self.load_config()
        return config.get(key, default)
    
    def set(self, key, value):
        """
        Define um valor de configuração.
        
        Args:
            key: Chave da configuração.
            value: Valor a definir.
        """
        config = self.load_config()
        config[key] = value
        self.save_config(config)


# Instâncias globais para uso conveniente
preset_manager = PresetManager()
config_manager = ConfigManager()
