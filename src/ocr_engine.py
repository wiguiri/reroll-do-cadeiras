"""
Módulo de OCR e extração de atributos.
Responsável por captura de tela e processamento de texto.
"""
import re
import pytesseract
from PIL import Image, ImageGrab, ImageEnhance, ImageOps

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import (
    get_tesseract_path,
    SPECIAL_ATTRIBUTES,
    OCR_CORRECTIONS
)

# Configura o caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()


class OCREngine:
    """Motor de OCR para extração de atributos de imagens."""
    
    def __init__(self):
        self.special_attributes = SPECIAL_ATTRIBUTES
        self.ocr_corrections = OCR_CORRECTIONS
    
    def capture_region(self, region):
        """
        Captura uma região específica da tela.
        
        Args:
            region: Tupla (left, top, right, bottom) da região.
            
        Returns:
            PIL.Image: Imagem capturada.
        """
        return ImageGrab.grab(bbox=region)
    
    def capture_fullscreen(self):
        """
        Captura a tela inteira.
        
        Returns:
            PIL.Image: Imagem da tela completa.
        """
        return ImageGrab.grab()
    
    def extract_text(self, image, config=''):
        """
        Extrai texto de uma imagem usando OCR.
        
        Args:
            image: Imagem PIL para processar.
            config: Configuração adicional do Tesseract.
            
        Returns:
            str: Texto extraído.
        """
        return pytesseract.image_to_string(image, lang='eng', config=config)
    
    def extract_text_with_processing(self, image):
        """
        Extrai texto tentando múltiplas configurações de processamento.
        
        Args:
            image: Imagem PIL para processar.
            
        Returns:
            tuple: (texto, valores_extraídos)
        """
        # Tenta primeiro com imagem normal
        text = self.extract_text(image)
        values = self.extract_attributes_from_text(text)
        
        # Se leu menos de 6 atributos, tenta com processamento
        if len(values) < 6:
            best_values = values
            
            # Tentativa 1: Escala de cinza + contraste alto
            gray = image.convert('L')
            enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
            text_enhanced = self.extract_text(enhanced, '--psm 6')
            retry_values = self.extract_attributes_from_text(text_enhanced)
            if len(retry_values) > len(best_values):
                best_values = retry_values
            
            # Tentativa 2: Brightness aumentado
            if len(best_values) < 6:
                bright = ImageEnhance.Brightness(gray).enhance(1.5)
                text_bright = self.extract_text(bright, '--psm 6')
                retry_values2 = self.extract_attributes_from_text(text_bright)
                if len(retry_values2) > len(best_values):
                    best_values = retry_values2
            
            # Tentativa 3: Inversão (para texto laranja em fundo escuro)
            if len(best_values) < 6:
                inverted = ImageOps.invert(gray)
                inverted_contrast = ImageEnhance.Contrast(inverted).enhance(3.0)
                text_inv = self.extract_text(inverted_contrast, '--psm 6')
                retry_values3 = self.extract_attributes_from_text(text_inv)
                if len(retry_values3) > len(best_values):
                    best_values = retry_values3
            
            values = best_values
        
        return text, values
    
    def extract_attributes_from_text(self, text):
        """
        Extrai atributos e valores numéricos do texto capturado.
        
        Args:
            text: Texto para processar.
            
        Returns:
            dict: Dicionário {nome_atributo: valor}
        """
        attributes = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verifica atributos especiais primeiro
            if self._check_special_attribute(line, attributes):
                continue
            
            # Tenta extrair atributos com valores numéricos
            if self._extract_numeric_attribute(line, attributes):
                continue
            
            # Tenta extrair atributos sem valor (booleanos)
            self._extract_boolean_attribute(line, attributes)
        
        return attributes
    
    def _check_special_attribute(self, line, attributes):
        """
        Verifica se a linha contém um atributo especial.
        
        Returns:
            bool: True se encontrou atributo especial.
        """
        line_lower = line.lower()
        # Remove prefixos de tier
        line_clean = re.sub(r'^t\d+\s+', '', line_lower, flags=re.IGNORECASE).strip()
        
        for special_name in self.special_attributes.keys():
            if line_clean == special_name:
                attributes[special_name] = 1
                return True
        
        return False
    
    def _extract_numeric_attribute(self, line, attributes):
        """
        Extrai atributo com valor numérico da linha.
        
        Returns:
            bool: True se extraiu um atributo.
        """
        # Padrão 1: "Nome: [+/-/4]valor[%]"
        match = re.search(r'([A-Za-z\s]+?)\s*:\s*[+\-4]?(\d{1,3})%?', line, re.IGNORECASE)
        if match:
            return self._process_numeric_match(match, attributes)
        
        # Padrão 2: "Nome [+/-/4]valor" (sem dois pontos)
        match = re.search(r'([A-Za-z\s]+?)\s+[+\-4]?(\d{1,3})%?', line, re.IGNORECASE)
        if match:
            return self._process_numeric_match(match, attributes)
        
        return False
    
    def _process_numeric_match(self, match, attributes):
        """
        Processa um match de regex para atributo numérico.
        
        Returns:
            bool: True se o atributo foi adicionado.
        """
        attr_name = match.group(1).strip()
        attr_value_str = match.group(2)
        attr_value = int(attr_value_str)
        
        # Correção: OCR confunde "+" com "4"
        if attr_value > 100 and attr_value_str.startswith('4'):
            corrected = int(attr_value_str[1:]) if len(attr_value_str) > 1 else attr_value
            if corrected <= 100:
                attr_value = corrected
        
        # Ignora valores muito altos (erro de OCR)
        if attr_value >= 500:
            return False
        
        # Normaliza o nome
        normalized_name = self._normalize_attribute_name(attr_name)
        
        # Validações para ignorar lixo do OCR
        if not self._is_valid_attribute_name(normalized_name):
            return False
        
        attributes[normalized_name] = attr_value
        return True
    
    def _extract_boolean_attribute(self, line, attributes):
        """
        Extrai atributo booleano (sem valor numérico) da linha.
        """
        if re.search(r'\d', line):
            return
        
        cleaned = line.strip()
        
        # Validações básicas
        if len(cleaned) < 3:
            return
        if not re.search(r'[aeiou]', cleaned, re.IGNORECASE):
            return
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{6,}', cleaned, re.IGNORECASE):
            return
        if re.search(r'\b[a-z]{1,2}\b.*\b[a-z]{1,2}\b.*\b[a-z]{1,2}\b', cleaned, re.IGNORECASE):
            if not re.search(r'(i+\s+r+\s*e+\s*r+|realm\s+le)', cleaned, re.IGNORECASE):
                return
        
        normalized_name = self._normalize_attribute_name(cleaned)
        
        # Aplica correções de OCR
        if normalized_name in self.ocr_corrections:
            normalized_name = self.ocr_corrections[normalized_name]
        
        # Correção por similaridade para atributos especiais
        normalized_name = self._correct_special_attribute(normalized_name)
        
        known_specials = list(self.special_attributes.keys())
        
        if normalized_name in known_specials:
            attributes[normalized_name] = 1
        elif len(normalized_name.split()) >= 2:
            attributes[normalized_name] = 1
    
    def _normalize_attribute_name(self, name):
        """
        Normaliza o nome de um atributo.
        
        Args:
            name: Nome para normalizar.
            
        Returns:
            str: Nome normalizado.
        """
        normalized = ' '.join(name.lower().split())
        # Remove prefixos de tier
        normalized = re.sub(r'^t\S*\s+', '', normalized, flags=re.IGNORECASE)
        # Remove dois pontos no final
        normalized = normalized.rstrip(':')
        return normalized
    
    def _is_valid_attribute_name(self, name):
        """
        Verifica se o nome do atributo é válido (não é lixo de OCR).
        
        Args:
            name: Nome para validar.
            
        Returns:
            bool: True se o nome é válido.
        """
        # Muitas consoantes seguidas
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{5,}', name):
            return False
        # Muito curto
        if len(name.replace(' ', '')) < 3:
            return False
        # Letras soltas repetidas
        if re.search(r'\b[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}', name):
            return False
        # Deve ter pelo menos uma palavra de 3+ letras
        if not any(len(w) >= 3 for w in name.split()):
            return False
        return True
    
    def _correct_special_attribute(self, name):
        """
        Tenta corrigir nome para atributo especial conhecido.
        
        Args:
            name: Nome para corrigir.
            
        Returns:
            str: Nome corrigido ou original.
        """
        known_specials = list(self.special_attributes.keys())
        
        if name in known_specials:
            return name
        
        # Verifica se contém palavras-chave
        if 'realm' in name or 'reaim' in name or 'clone' in name:
            if any(x in name for x in ['tar', 'tai', 'ta ', 'tae', 'lr', 'rr']):
                return 'tar realm'
            elif any(x in name for x in ['ice', 'iced', 'ic']):
                return 'iced realm'
            elif any(x in name for x in ['thunder', 'thunde']):
                return 'thunder realm'
            elif any(x in name for x in ['gold', 'golden', 'goiden']):
                return 'golden realm'
            elif 'clone' in name or 'boss' in name:
                return 'boss clone'
        
        return name


# Instância global para uso conveniente
ocr_engine = OCREngine()
