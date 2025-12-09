"""
Módulo de automação.
Contém a lógica dos loops de automação para cada modo.
"""
import time
import threading
import pyautogui
import keyboard
from tkinter import messagebox

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ocr_engine import OCREngine


class AutomationEngine:
    """Motor de automação para os diferentes modos."""
    
    def __init__(self, app):
        """
        Inicializa o motor de automação.
        
        Args:
            app: Referência para a aplicação principal.
        """
        self.app = app
        self.ocr = OCREngine()
        self.is_running = False
        self._thread = None
    
    def start(self, mode):
        """
        Inicia a automação no modo especificado.
        
        Args:
            mode: Modo de automação ('values', 'attributes', 'keys').
        """
        if self.is_running:
            return False
        
        self.is_running = True
        
        if mode == 'values':
            self._thread = threading.Thread(target=self._loop_values, daemon=True)
        elif mode == 'attributes':
            self._thread = threading.Thread(target=self._loop_attributes, daemon=True)
        elif mode == 'keys':
            self._thread = threading.Thread(target=self._loop_keys, daemon=True)
        elif mode == 't7':
            self._thread = threading.Thread(target=self._loop_t7, daemon=True)
        else:
            self.is_running = False
            return False
        
        self._thread.start()
        return True
    
    def stop(self):
        """Para a automação."""
        self.is_running = False
        time.sleep(0.1)  # Aguarda threads pararem
    
    def _get_delay(self):
        """Retorna o delay configurado."""
        return float(self.app.delay_var.get())
    
    def _get_click_delay(self):
        """Retorna o delay de click em segundos."""
        return float(self.app.click_delay_var.get()) / 1000.0
    
    def _get_max_attempts(self):
        """Retorna o número máximo de tentativas."""
        return int(self.app.max_attempts_var.get())
    
    def _do_shift_click(self):
        """Executa Shift+Click."""
        click_delay = self._get_click_delay()
        
        keyboard.press('shift')
        time.sleep(click_delay)
        pyautogui.mouseDown(button='left')
        time.sleep(click_delay)
        pyautogui.mouseUp(button='left')
        time.sleep(click_delay)
        keyboard.release('shift')
    
    def _loop_values(self):
        """Loop de automação para busca por valores específicos."""
        delay = self._get_delay()
        max_attempts = self._get_max_attempts()
        attempts = 0
        
        self.app.log("Iniciando automação (Busca por VALORES específicos)...")
        self.app.log_to_detail("="*60, 'header')
        self.app.log_to_detail("🎯 AUTOMAÇÃO INICIADA - BUSCA POR VALORES", 'header')
        self.app.log_to_detail("="*60, 'header')
        
        while self.is_running and attempts < max_attempts:
            try:
                # Captura a tela
                screenshot = self.ocr.capture_region(self.app.region)
                text, current_values = self.ocr.extract_text_with_processing(screenshot)
                
                self.app.log_to_detail(f"\n--- Tentativa #{attempts + 1} ---", 'header')
                
                if not current_values:
                    self.app.log_to_detail("⏸️ Aguardando... Nenhum valor identificado", 'warning')
                    time.sleep(0.5)
                    continue
                
                self.app.log_to_detail(f"✓ Valores capturados: {current_values}", 'info')
                
                # Verifica se atingiu o alvo
                reached, message = self.app.check_target_reached(current_values)
                self.app.log_to_detail(message, 'success' if reached else 'warning')
                self.app.update_status(f"Tentativa {attempts + 1}: {'Atingido!' if reached else 'Continuando...'}")
                
                if reached:
                    self._on_success_values(attempts + 1)
                    break
                
                # Shift + Click
                current_pos = pyautogui.position()
                self._do_shift_click()
                self.app.log_to_detail(f"🖱️ Shift+Click (pos: {current_pos.x}, {current_pos.y})", 'info')
                attempts += 1
                
                time.sleep(delay)
                
                # Verificação extra pós-click
                if self._check_post_click_values():
                    self._on_success_values(attempts)
                    break
                
            except Exception as e:
                self.app.log(f"Erro: {e}")
                self.app.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if attempts >= max_attempts:
            self._on_max_attempts(max_attempts)
    
    def _check_post_click_values(self):
        """Verifica valores após o click."""
        try:
            screenshot = self.ocr.capture_region(self.app.region)
            _, values = self.ocr.extract_text_with_processing(screenshot)
            
            if values:
                reached, _ = self.app.check_target_reached(values)
                return reached
        except:
            pass
        return False
    
    def _on_success_values(self, attempts):
        """Callback de sucesso para modo valores."""
        self.app.log(f"✓ SUCESSO! Valores atingidos após {attempts} tentativas")
        self.app.log_to_detail("\n" + "="*60, 'success')
        self.app.log_to_detail("🎉 SUCESSO! TODOS OS VALORES ATINGIDOS!", 'success')
        self.app.log_to_detail("="*60, 'success')
        self.app.stop_automation()
        messagebox.showinfo("Sucesso", f"Valores desejados atingidos!\n\nTentativas: {attempts}")
    
    def _loop_attributes(self):
        """Loop de automação para busca por presença de atributos."""
        delay = self._get_delay()
        max_attempts = self._get_max_attempts()
        attempts = 0
        
        self.app.log("Iniciando automação (Busca por PRESENÇA de atributos)...")
        self.app.log_to_detail("="*60, 'header')
        self.app.log_to_detail("🔍 AUTOMAÇÃO INICIADA - BUSCA POR ATRIBUTOS", 'header')
        self.app.log_to_detail("="*60, 'header')
        
        while self.is_running and attempts < max_attempts:
            try:
                screenshot = self.ocr.capture_region(self.app.region)
                _, current_values = self.ocr.extract_text_with_processing(screenshot)
                
                self.app.log_to_detail(f"\n--- Tentativa #{attempts + 1} ---", 'header')
                
                if not current_values:
                    self.app.log_to_detail("⏸️ Aguardando... Nenhum valor identificado", 'warning')
                    time.sleep(0.5)
                    continue
                
                self.app.log_to_detail(f"✓ Atributos encontrados: {list(current_values.keys())}", 'info')
                
                found, message = self.app.check_attributes_found(current_values)
                self.app.log_to_detail(message, 'success' if found else 'warning')
                self.app.update_status(f"Tentativa {attempts + 1}: {'Todos encontrados!' if found else 'Procurando...'}")
                
                if found:
                    self._on_success_attributes(attempts + 1)
                    break
                
                current_pos = pyautogui.position()
                self._do_shift_click()
                self.app.log_to_detail(f"🖱️ Shift+Click (pos: {current_pos.x}, {current_pos.y})", 'info')
                attempts += 1
                
                time.sleep(delay)
                
                # Verificação extra
                if self._check_post_click_attributes():
                    self._on_success_attributes(attempts)
                    break
                
            except Exception as e:
                self.app.log(f"Erro: {e}")
                self.app.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if attempts >= max_attempts:
            self._on_max_attempts(max_attempts)
    
    def _check_post_click_attributes(self):
        """Verifica atributos após o click."""
        try:
            screenshot = self.ocr.capture_region(self.app.region)
            _, values = self.ocr.extract_text_with_processing(screenshot)
            
            if values:
                found, _ = self.app.check_attributes_found(values)
                return found
        except:
            pass
        return False
    
    def _on_success_attributes(self, attempts):
        """Callback de sucesso para modo atributos."""
        self.app.log(f"✓ SUCESSO! Todos os atributos encontrados após {attempts} tentativas")
        self.app.log_to_detail("\n" + "="*60, 'success')
        self.app.log_to_detail("🎉 SUCESSO! TODOS OS ATRIBUTOS ENCONTRADOS!", 'success')
        self.app.log_to_detail("="*60, 'success')
        self.app.stop_automation()
        messagebox.showinfo("Sucesso", f"Todos os atributos encontrados!\n\nTentativas: {attempts}")
    
    def _loop_keys(self):
        """Loop de automação para rolagem de chaves."""
        delay = self._get_delay()
        click_delay = self._get_click_delay()
        
        keys_processed = 0
        empty_attempts = 0
        max_empty_attempts = 5
        
        self.app.log("Iniciando automação de CHAVES...")
        self.app.log_to_detail("="*60, 'header')
        self.app.log_to_detail("🔑 AUTOMAÇÃO DE CHAVES INICIADA", 'header')
        self.app.log_to_detail("="*60, 'header')
        
        while self.is_running:
            try:
                self.app.log(f"🔍 Processando chave #{keys_processed + 1}...")
                self.app.log_to_detail(f"\n{'='*50}", 'header')
                self.app.log_to_detail(f"🔍 CHAVE #{keys_processed + 1}", 'header')
                
                if not self.is_running:
                    break
                
                # Move para posição da chave
                pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
                time.sleep(0.5)
                
                if not self.is_running:
                    break
                
                # Captura atributos
                screenshot = self.ocr.capture_region(self.app.region)
                _, current_values = self.ocr.extract_text_with_processing(screenshot)
                
                if not current_values:
                    empty_attempts += 1
                    self.app.log_to_detail(f"⚠️ Nenhum atributo ({empty_attempts}/{max_empty_attempts})", 'warning')
                    
                    if empty_attempts >= max_empty_attempts:
                        self._on_keys_finished(keys_processed)
                        break
                    
                    time.sleep(delay)
                    continue
                
                empty_attempts = 0
                self.app.log_to_detail(f"✓ Atributos: {list(current_values.keys())}", 'info')
                
                found, message = self.app.check_keys_attributes(current_values)
                self.app.log_to_detail(message, 'success' if found else 'warning')
                
                if found:
                    # Chave boa - mover para BP
                    if not self.is_running:
                        break
                    
                    self.app.log("🎉 CHAVE BOA! Movendo para BP...")
                    self.app.log_to_detail("🎉 CHAVE PERFEITA! Movendo para BP...", 'success')
                    
                    pyautogui.click(button='right')
                    time.sleep(0.15)
                    
                    if not self.is_running:
                        break
                    
                    # Drag and drop
                    pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
                    time.sleep(0.1)
                    pyautogui.mouseDown(button='left')
                    time.sleep(0.1)
                    pyautogui.moveTo(self.app.bp_position[0], self.app.bp_position[1], duration=0.3)
                    time.sleep(0.1)
                    pyautogui.mouseUp(button='left')
                    
                    keys_processed += 1
                    self.app.update_status(f"Chaves processadas: {keys_processed}")
                    
                    time.sleep(0.3)
                    pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
                    time.sleep(delay)
                    
                else:
                    # Chave ruim - rolar
                    self._roll_key(delay, click_delay, keys_processed)
                
            except Exception as e:
                self.app.log(f"Erro: {e}")
                self.app.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if keys_processed > 0:
            self.app.log(f"✓ Automação concluída! {keys_processed} chave(s) processada(s)")
    
    def _roll_key(self, delay, click_delay, keys_processed):
        """Rola uma chave com Orb of Chance."""
        self.app.log_to_detail("❌ Atributos não desejados. Rolando...", 'info')
        
        # Clica no Orb
        pyautogui.moveTo(self.app.orb_position[0], self.app.orb_position[1])
        time.sleep(0.1)
        pyautogui.click(button='right')
        time.sleep(0.2)
        
        max_roll_attempts = 100
        roll_attempt = 0
        
        while self.is_running and roll_attempt < max_roll_attempts:
            if not self.is_running:
                break
            
            pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
            time.sleep(0.05)
            
            self._do_shift_click()
            roll_attempt += 1
            
            time.sleep(delay)
            
            if not self.is_running:
                break
            
            # Verifica atributos
            pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
            time.sleep(0.5)
            
            screenshot = self.ocr.capture_region(self.app.region)
            _, values = self.ocr.extract_text_with_processing(screenshot)
            
            if values:
                found, msg = self.app.check_keys_attributes(values)
                
                if roll_attempt % 10 == 0:
                    self.app.log_to_detail(f"  Roll #{roll_attempt}: {list(values.keys())}", 'info')
                
                if found:
                    if not self.is_running:
                        break
                    
                    self.app.log(f"🎉 ATRIBUTOS CONSEGUIDOS após {roll_attempt} rolagens!")
                    self.app.log_to_detail(f"🎉 SUCESSO após {roll_attempt} rolagens!", 'success')
                    
                    pyautogui.click(button='right')
                    time.sleep(0.15)
                    
                    if not self.is_running:
                        break
                    
                    # Mover para BP
                    pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
                    time.sleep(0.1)
                    pyautogui.mouseDown(button='left')
                    time.sleep(0.1)
                    pyautogui.moveTo(self.app.bp_position[0], self.app.bp_position[1], duration=0.3)
                    time.sleep(0.1)
                    pyautogui.mouseUp(button='left')
                    
                    self.app.log("✓ Chave BOA salva na BP!")
                    
                    time.sleep(0.3)
                    pyautogui.moveTo(self.app.key_position[0], self.app.key_position[1])
                    break
        
        if roll_attempt >= max_roll_attempts:
            self.app.log(f"⚠️ Limite de {max_roll_attempts} rolagens atingido")
            
            # Desseleciona o orb antes de continuar para próxima chave
            pyautogui.click(button='right')
            time.sleep(0.15)
        
        time.sleep(delay * 0.5)
    
    def _on_keys_finished(self, keys_processed):
        """Callback quando as chaves acabam."""
        self.app.log("⚠️ Chaves acabaram")
        self.app.log_to_detail("\n" + "="*60, 'warning')
        self.app.log_to_detail("⚠️ CHAVES ACABARAM", 'warning')
        self.app.stop_automation()
        messagebox.showinfo(
            "Automação Concluída",
            f"Chaves processadas: {keys_processed}\n\nNão foi possível detectar mais atributos."
        )
    
    def _on_max_attempts(self, max_attempts):
        """Callback quando atinge máximo de tentativas."""
        self.app.log(f"⚠ Máximo de tentativas ({max_attempts}) atingido")
        self.app.log_to_detail(f"\n⚠️ Máximo de tentativas ({max_attempts}) atingido", 'warning')
        self.app.stop_automation()
    
    def _loop_t7(self):
        """Loop de automação para busca por atributos T7."""
        delay = self._get_delay()
        max_attempts = self._get_max_attempts()
        attempts = 0
        
        # Pega configurações da aba T7
        t7_mode = self.app.tab_t7.get_mode()
        specific_attrs = self.app.tab_t7.get_specific_attributes()
        
        mode_text = "QUALQUER T7" if t7_mode == "ANY" else f"T7 em: {', '.join(specific_attrs)}"
        
        self.app.log(f"Iniciando automação T7 ({mode_text})...")
        self.app.log_to_detail("="*60, 'header')
        self.app.log_to_detail(f"⭐ AUTOMAÇÃO T7 INICIADA - {mode_text}", 'header')
        self.app.log_to_detail("="*60, 'header')
        
        while self.is_running and attempts < max_attempts:
            try:
                # Captura a tela
                screenshot = self.ocr.capture_region(self.app.region)
                
                # Tenta múltiplos métodos de OCR para melhor resultado
                from PIL import ImageEnhance, ImageOps
                
                all_results = []
                
                # Método 1: Normal
                text1 = self.ocr.extract_text(screenshot)
                tiers1 = self.ocr.extract_attributes_with_tiers(text1)
                all_results.append(tiers1)
                
                # Método 2: Contraste
                gray = screenshot.convert('L')
                enhanced = ImageEnhance.Contrast(gray).enhance(2.5)
                text2 = self.ocr.extract_text(enhanced, '--psm 6')
                tiers2 = self.ocr.extract_attributes_with_tiers(text2)
                all_results.append(tiers2)
                
                # Método 3: Inversão (bom para texto claro em fundo escuro)
                inverted = ImageOps.invert(gray)
                inv_contrast = ImageEnhance.Contrast(inverted).enhance(3.0)
                text3 = self.ocr.extract_text(inv_contrast, '--psm 6')
                tiers3 = self.ocr.extract_attributes_with_tiers(text3)
                all_results.append(tiers3)
                
                # Pega o melhor resultado (mais atributos)
                all_tiers = max(all_results, key=len)
                t7_attrs = [a for a in all_tiers if a['tier'] == 7]
                
                # Também verifica T7 em todos os resultados (pode ter sido detectado em outro método)
                for result in all_results:
                    for attr in result:
                        if attr['tier'] == 7:
                            # Verifica se já não está na lista
                            if not any(t['name'] == attr['name'] for t in t7_attrs):
                                t7_attrs.append(attr)
                
                self.app.log_to_detail(f"\n--- Tentativa #{attempts + 1} ---", 'header')
                
                # Mostra todos os tiers encontrados
                if all_tiers:
                    for attr in all_tiers:
                        tier = attr['tier']
                        name = attr['name'].upper()
                        value = attr['value']
                        
                        if tier == 7:
                            self.app.log_to_detail(f"  ⭐ T{tier} {name}: +{value}", 'success')
                        elif tier >= 5:
                            self.app.log_to_detail(f"  🔶 T{tier} {name}: +{value}", 'warning')
                        else:
                            self.app.log_to_detail(f"  ⚪ T{tier} {name}: +{value}", 'info')
                else:
                    self.app.log_to_detail("  (nenhum atributo com tier detectado)", 'warning')
                
                # Verifica se encontrou T7
                found_t7 = False
                found_attr = None
                
                if t7_attrs:
                    if t7_mode == "ANY":
                        # Qualquer T7 serve
                        found_t7 = True
                        found_attr = t7_attrs[0]
                    else:
                        # Precisa ser T7 de atributo específico
                        for t7 in t7_attrs:
                            attr_name = t7['name'].lower()
                            for specific in specific_attrs:
                                if specific in attr_name or attr_name in specific:
                                    found_t7 = True
                                    found_attr = t7
                                    break
                            if found_t7:
                                break
                
                if t7_attrs:
                    self.app.log_to_detail(f"🎯 T7 DETECTADO!", 'success')
                else:
                    self.app.log_to_detail("❌ Nenhum T7 nesta tentativa", 'warning')
                
                self.app.update_status(f"Tentativa {attempts + 1}: {'T7 ENCONTRADO!' if found_t7 else 'Procurando T7...'}")
                
                if found_t7:
                    self._on_success_t7(attempts + 1, found_attr)
                    break
                
                # Shift + Click para rolar
                current_pos = pyautogui.position()
                self._do_shift_click()
                self.app.log_to_detail(f"🖱️ Shift+Click (pos: {current_pos.x}, {current_pos.y})", 'info')
                attempts += 1
                
                time.sleep(delay)
                
                # Verificação extra pós-click
                if self._check_post_click_t7(t7_mode, specific_attrs):
                    # Recaptura para pegar o atributo
                    screenshot = self.ocr.capture_region(self.app.region)
                    _, t7_attrs = self.ocr.extract_t7_attributes(screenshot)
                    if t7_attrs:
                        self._on_success_t7(attempts, t7_attrs[0])
                    else:
                        self._on_success_t7(attempts, {'name': 'desconhecido', 'value': '?'})
                    break
                
            except Exception as e:
                self.app.log(f"Erro: {e}")
                self.app.log_to_detail(f"❌ ERRO: {e}", 'error')
                time.sleep(delay)
        
        if attempts >= max_attempts:
            self._on_max_attempts(max_attempts)
    
    def _check_post_click_t7(self, t7_mode, specific_attrs):
        """Verifica se encontrou T7 após o click."""
        try:
            screenshot = self.ocr.capture_region(self.app.region)
            _, t7_attrs = self.ocr.extract_t7_attributes(screenshot)
            
            if not t7_attrs:
                return False
            
            if t7_mode == "ANY":
                return True
            
            # Verifica se é o T7 específico
            for t7 in t7_attrs:
                attr_name = t7['name'].lower()
                for specific in specific_attrs:
                    if specific in attr_name or attr_name in specific:
                        return True
            
            return False
        except:
            return False
    
    def _on_success_t7(self, attempts, t7_attr):
        """Callback de sucesso para modo T7."""
        attr_name = t7_attr.get('name', 'desconhecido').upper()
        attr_value = t7_attr.get('value', '?')
        
        self.app.log(f"⭐ T7 ENCONTRADO! {attr_name}: {attr_value} após {attempts} tentativas")
        self.app.log_to_detail("\n" + "="*60, 'success')
        self.app.log_to_detail(f"⭐ T7 ENCONTRADO: {attr_name}: +{attr_value}", 'success')
        self.app.log_to_detail(f"🎉 SUCESSO após {attempts} tentativas!", 'success')
        self.app.log_to_detail("="*60, 'success')
        self.app.stop_automation()
        messagebox.showinfo(
            "⭐ T7 Encontrado!",
            f"Atributo T7 encontrado!\n\n"
            f"T7 {attr_name}: +{attr_value}\n\n"
            f"Tentativas: {attempts}"
        )
