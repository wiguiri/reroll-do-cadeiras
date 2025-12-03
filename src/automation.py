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
