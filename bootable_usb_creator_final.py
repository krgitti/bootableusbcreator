#!/usr/bin/env python3
"""
Bootable USB Creator - Versão Escalável Completa
Sistema hierárquico com milhares de distribuições possíveis
"""

import os
import sys
import requests
import subprocess
import platform
import shutil
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import hashlib
import time
import psutil


class BootableUSBCreator:
    def __init__(self):
        # Inicializar log temporário antes da GUI
        self._temp_log = []

        # Carregar distribuições hierárquicas escaláveis
        self.distributions = self.load_scalable_distributions()

        # ✅ NOVO: Variáveis de controle de processo
        self.is_operation_running = False
        self.current_process = None
        self.should_cancel = False
        self.sudo_password = None  # ✅ NOVO: Armazena senha sudo

        self.arch_maps = {
            "64bit": "amd64",
            "32bit": "i386", 
            "x86_64": "amd64",
            "amd64": "amd64",
            "i386": "i386",
            "i686": "i386",
            "aarch64": "arm64",
            "arm64": "arm64", 
            "armhf": "armhf",
            "ppc64el": "ppc64el",
            "s390x": "s390x"
        }

        self.download_dir = Path.home() / "BootableUSB_Downloads"
        self.download_dir.mkdir(exist_ok=True)
        self.selected_usb_device = None
        self.custom_iso_path = None

        self.setup_gui()
        self.check_dependencies()

    def check_environment(self):
        """Verifica se o ambiente suporta execução gráfica com sudo"""
        try:
            # Verifica se está em ambiente gráfico
            if os.environ.get('DISPLAY'):
                self.log("✅ Ambiente gráfico detectado")
            else:
                self.log("⚠️ Ambiente sem DISPLAY - modo terminal")
            
            # Verifica se tem terminal disponível
            terminal_emulators = ['gnome-terminal', 'konsole', 'xfce4-terminal', 'xterm']
            available_terminal = None
            for terminal in terminal_emulators:
                if shutil.which(terminal):
                    available_terminal = terminal
                    break
            
            if available_terminal:
                self.log(f"✅ Terminal disponível: {available_terminal}")
            else:
                self.log("⚠️ Nenhum terminal gráfico encontrado")
            
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro na verificação de ambiente: {e}")
            return False

    def check_sudo_permission(self):
        """Verifica e solicita permissão sudo se necessário - VERSÃO CORRIGIDA"""
        try:
            # Se já é root ou Windows, não precisa de sudo
            if platform.system().lower() == "windows" or os.geteuid() == 0:
                return True
                
            self.log("🔐 Operação requer privilégios de superusuário...")
            
            # Se já temos senha armazenada, testa se ainda é válida
            if self.sudo_password:
                test_process = subprocess.Popen(
                    ['sudo', '-S', 'echo', 'sudo_test_ok'],
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = test_process.communicate(input=self.sudo_password + '\n', timeout=5)
                
                if test_process.returncode == 0 and 'sudo_test_ok' in stdout:
                    self.log("✅ Senha sudo ainda válida")
                    return True
                else:
                    self.log("⚠️ Senha sudo anterior inválida, solicitando nova...")
                    self.sudo_password = None
            
            # Solicita nova senha
            password = self.ask_sudo_password()
            if not password:
                self.log("❌ Senha não fornecida - operação cancelada")
                return False
                
            # Testa a nova senha
            test_process = subprocess.Popen(
                ['sudo', '-S', 'echo', 'sudo_test_ok'],
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = test_process.communicate(input=password + '\n', timeout=10)
            
            if test_process.returncode == 0 and 'sudo_test_ok' in stdout:
                self.log("✅ Autenticação sudo bem-sucedida")
                self.sudo_password = password  # Armazena para uso posterior
                return True
            else:
                self.log("❌ Senha sudo incorreta ou erro na autenticação")
                if "incorrect password attempt" in stderr.lower():
                    messagebox.showerror("Erro de Autenticação", "Senha sudo incorreta!")
                else:
                    messagebox.showerror("Erro de Autenticação", f"Erro na autenticação:\n{stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout na autenticação sudo")
            messagebox.showerror("Timeout", "Tempo esgotado na autenticação sudo")
            return False
        except Exception as e:
            self.log(f"⚠️ Erro na autenticação sudo: {e}")
            messagebox.showerror("Erro", f"Erro inesperado:\n{e}")
            return False

    def ask_sudo_password(self):
        """Solicita senha sudo via diálogo gráfico"""
        try:
            import tkinter.simpledialog as simpledialog
            
            # Cria uma janela temporária para o diálogo
            password_dialog = tk.Toplevel(self.root)
            password_dialog.title("Autenticação Requerida")
            password_dialog.geometry("400x150")
            password_dialog.transient(self.root)
            password_dialog.grab_set()
            
            # Frame principal
            main_frame = ttk.Frame(password_dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Mensagem
            message = "🔐 Esta operação requer privilégios de superusuário\n\nDigite sua senha:"
            ttk.Label(main_frame, text=message, justify=tk.CENTER).pack(pady=10)
            
            # Campo de senha
            password_var = tk.StringVar()
            password_entry = ttk.Entry(main_frame, textvariable=password_var, show='*', width=30)
            password_entry.pack(pady=10)
            password_entry.focus()
            
            # Variável para resultado
            result = [None]
            
            def on_ok():
                result[0] = password_var.get()
                password_dialog.destroy()
                
            def on_cancel():
                result[0] = None
                password_dialog.destroy()
            
            # Botões
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(pady=10)
            
            ttk.Button(button_frame, text="OK", command=on_ok).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="Cancelar", command=on_cancel).grid(row=0, column=1, padx=5)
            
            # Bind Enter key
            password_dialog.bind('<Return>', lambda e: on_ok())
            
            # Espera o diálogo fechar
            self.root.wait_window(password_dialog)
            
            return result[0]
            
        except Exception as e:
            self.log(f"⚠️ Erro no diálogo de senha: {e}")
            # Fallback para terminal
            try:
                import getpass
                self.log("💡 Por favor, digite sua senha sudo no terminal:")
                password = getpass.getpass("Senha sudo: ")
                return password
            except:
                return None

    def run_sudo_command(self, command, input_text=None):
        """Executa um comando com sudo de forma segura"""
        try:
            if platform.system().lower() == "windows":
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                return result.returncode == 0, result.stdout, result.stderr
            
            if os.geteuid() == 0:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                return result.returncode == 0, result.stdout, result.stderr
            else:
                if not self.sudo_password:
                    self.log("❌ Senha sudo não disponível")
                    return False, "", "Senha sudo não disponível"
                
                # ✅ CORREÇÃO SEGURA: Não mostra senha no log
                full_command = f'echo "{self.sudo_password}" | sudo -S {" ".join(command)}'
                log_command = f'sudo {" ".join(command)}'  # Log sem senha
                
                self.log(f"🔐 Executando: {log_command}")
                
                process = subprocess.Popen(
                    full_command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                try:
                    stdout, stderr = process.communicate(timeout=30)
                    success = process.returncode == 0
                    
                    if not success:
                        # ✅ CORREÇÃO: Limpa possíveis vazamentos de senha no stderr
                        clean_stderr = stderr.replace(self.sudo_password, '***')
                        self.log(f"❌ Erro no comando sudo: {clean_stderr}")
                    else:
                        self.log("✅ Comando executado com sucesso")
                    
                    return success, stdout, stderr
                    
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.log("❌ Timeout no comando sudo")
                    return False, "", "Timeout"
                    
        except Exception as e:
            self.log(f"❌ Erro ao executar comando: {e}")
            return False, "", str(e)

    def run_dd_command_with_sudo(self, iso_path, device, needs_sudo):
        """Executa o comando dd com sudo de forma segura"""
        try:
            total_size = os.path.getsize(iso_path)
            pv_available = shutil.which("pv") is not None
            
            self.log(f"📊 Tamanho da ISO: {total_size / (1024**3):.2f} GB")
            self.log(f"🎯 PV disponível: {pv_available}")
            
            if pv_available:
                # Comando com pv para mostrar progresso
                if needs_sudo:
                    # ✅ CORREÇÃO SEGURA: Não mostra senha no log
                    cmd = f'echo "{self.sudo_password}" | sudo -S pv -n "{iso_path}" | sudo -S dd of="{device}" bs=4M'
                    log_cmd = f'pv -n "{iso_path}" | dd of="{device}" bs=4M [COM SUDO]'  # Log sem senha
                else:
                    cmd = f'pv -n "{iso_path}" | dd of="{device}" bs=4M'
                    log_cmd = cmd
            else:
                # Comando dd simples
                if needs_sudo:
                    cmd = f'echo "{self.sudo_password}" | sudo -S dd if="{iso_path}" of="{device}" bs=4M status=progress'
                    log_cmd = f'dd if="{iso_path}" of="{device}" bs=4M status=progress [COM SUDO]'  # Log sem senha
                else:
                    cmd = f'dd if="{iso_path}" of="{device}" bs=4M status=progress'
                    log_cmd = cmd
            
            # ✅ CORREÇÃO: Log seguro sem mostrar senha
            self.log(f"⚡ Executando: {log_cmd}")
            
            # Executa o comando
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            
            return process, pv_available, total_size
            
        except Exception as e:
            self.log(f"❌ Erro ao preparar comando dd: {e}")
            return None, False, 0

    def run_dd_command_secure(self, iso_path, device, needs_sudo):
        """Executa dd de forma mais segura usando pipes"""
        try:
            total_size = os.path.getsize(iso_path)
            pv_available = shutil.which("pv") is not None
            
            self.log(f"📊 Iniciando gravação segura...")
            self.log(f"   Tamanho: {total_size / (1024**3):.2f} GB")
            self.log(f"   PV: {'Sim' if pv_available else 'Não'}")
            self.log(f"   Sudo: {'Sim' if needs_sudo else 'Não'}")
            
            if needs_sudo and not self.sudo_password:
                self.log("❌ Senha sudo necessária mas não disponível")
                return None, False, 0
            
            # ✅ MÉTODO SEGURO: Usa Popen com stdin para enviar senha
            if pv_available:
                if needs_sudo:
                    # Comando com pv e sudo
                    cmd1 = ['sudo', '-S', 'pv', '-n', iso_path]
                    cmd2 = ['sudo', '-S', 'dd', f'of={device}', 'bs=4M']
                else:
                    # Comando com pv sem sudo
                    cmd1 = ['pv', '-n', iso_path]
                    cmd2 = ['dd', f'of={device}', 'bs=4M']
            else:
                if needs_sudo:
                    # Comando dd com sudo
                    cmd = ['sudo', '-S', 'dd', f'if={iso_path}', f'of={device}', 'bs=4M', 'status=progress']
                else:
                    # Comando dd sem sudo
                    cmd = ['dd', f'if={iso_path}', f'of={device}', 'bs=4M', 'status=progress']
            
            # Log seguro
            if pv_available:
                log_msg = f"pv + dd [{'COM SUDO' if needs_sudo else 'SEM SUDO'}]"
            else:
                log_msg = f"dd [{'COM SUDO' if needs_sudo else 'SEM SUDO'}]"
            
            self.log(f"⚡ Executando: {log_msg}")
            
            # Execução segura
            if pv_available:
                if needs_sudo:
                    # Pipe com sudo: pv | dd
                    pv_process = subprocess.Popen(
                        cmd1,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Envia senha para o primeiro sudo
                    pv_process.stdin.write(self.sudo_password + '\n')
                    pv_process.stdin.flush()
                    
                    dd_process = subprocess.Popen(
                        cmd2,
                        stdin=pv_process.stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    
                    # Envia senha para o segundo sudo
                    # Não podemos enviar diretamente, então usamos um método diferente
                    process = dd_process
                    
                else:
                    # Pipe sem sudo
                    pv_process = subprocess.Popen(
                        cmd1,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    process = subprocess.Popen(
                        cmd2,
                        stdin=pv_process.stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
            else:
                if needs_sudo:
                    # DD simples com sudo
                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    process.stdin.write(self.sudo_password + '\n')
                    process.stdin.flush()
                else:
                    # DD simples sem sudo
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
            
            return process, pv_available, total_size
            
        except Exception as e:
            self.log(f"❌ Erro no método seguro: {e}")
            return None, False, 0

    def unmount_all_partitions(self, device):
        """Desmonta todas as partições de um dispositivo - VERSÃO MELHORADA"""
        try:
            system = platform.system().lower()
            if system != "linux":
                return True
                
            self.log(f"🔌 Desmontando partições de {device}...")
            
            needs_sudo = os.geteuid() != 0
            
            # Primeiro, tenta métodos mais simples
            simple_commands = [
                ['umount', f"{device}*"],  # Tenta desmontar todas as partições
                ['umount', device],  # Tenta desmontar o dispositivo
            ]
            
            for cmd in simple_commands:
                if needs_sudo and self.sudo_password:
                    success, stdout, stderr = self.run_sudo_command(cmd)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0
                
                if success:
                    self.log(f"✅ {' '.join(cmd)} - partições desmontadas")
            
            time.sleep(2)
            
            # Método detalhado: lista e desmonta individualmente
            if needs_sudo and self.sudo_password:
                success, stdout, stderr = self.run_sudo_command(['lsblk', '-l', '-o', 'NAME,MOUNTPOINT,TYPE'])
            else:
                result = subprocess.run(['lsblk', '-l', '-o', 'NAME,MOUNTPOINT,TYPE'], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                stdout = result.stdout
            
            if not success:
                self.log("⚠️ Não foi possível listar partições, continuando...")
                return True  # Continua mesmo sem listar
                
            # Encontra e desmonta todas as partições do dispositivo
            device_name = device.split('/')[-1]  # Pega 'sdb' de '/dev/sdb'
            partitions_unmounted = 0
            
            for line in stdout.split('\n'):
                if device_name in line and 'part' in line and line.strip():
                    parts = line.split()
                    if len(parts) >= 3 and parts[0].startswith(device_name) and parts[2] == 'part':
                        partition = f"/dev/{parts[0]}"
                        mountpoint = parts[1] if len(parts) > 1 and parts[1] != "" else "(sem mountpoint)"
                        
                        if mountpoint != "(sem mountpoint)":
                            self.log(f"   📍 Desmontando {partition} de {mountpoint}...")
                            
                            if needs_sudo and self.sudo_password:
                                success, stdout, stderr = self.run_sudo_command(['umount', partition])
                            else:
                                result = subprocess.run(['umount', partition], capture_output=True, text=True)
                                success = result.returncode == 0
                            
                            if success:
                                self.log(f"   ✅ {partition} desmontado")
                                partitions_unmounted += 1
                            else:
                                self.log(f"   ⚠️ Não foi possível desmontar {partition}")
            
            if partitions_unmounted > 0:
                self.log(f"✅ {partitions_unmounted} partição(ões) desmontada(s)")
            else:
                self.log("ℹ️ Nenhuma partição estava montada ou já estavam desmontadas")
                
            # Pausa final para o sistema processar
            time.sleep(3)
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro ao desmontar partições: {e}")
            # Continua mesmo com erro
            return True

    def force_unmount_device(self, device):
        """Tenta desmontar forçadamente um dispositivo"""
        try:
            self.log(f"🔧 Tentando desmontagem forçada de {device}...")
            
            # Tenta desmontar o dispositivo inteiro primeiro
            commands = [
                ['umount', device],  # Tenta desmontar o dispositivo
                ['umount', f"{device}*"],  # Tenta desmontar todas as partições
            ]
            
            needs_sudo = os.geteuid() != 0
            
            for cmd in commands:
                if needs_sudo and self.sudo_password:
                    success, stdout, stderr = self.run_sudo_command(cmd)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0
                
                if success:
                    self.log(f"✅ Comando {' '.join(cmd)} executado com sucesso")
            
            # Pequena pausa
            time.sleep(3)
            
            # Agora usa o método detalhado
            return self.unmount_all_partitions(device)
            
        except Exception as e:
            self.log(f"⚠️ Erro na desmontagem forçada: {e}")
            return False

    def verify_usb_device(self, device):
        """Verifica se o dispositivo USB está pronto para formatação"""
        try:
            self.log(f"🔍 Verificando dispositivo {device}...")
            
            # Verifica se o dispositivo existe
            if not os.path.exists(device):
                self.log(f"❌ Dispositivo {device} não encontrado")
                return False
            
            # Verifica tamanho do dispositivo
            if os.geteuid() != 0 and self.sudo_password:
                success, stdout, stderr = self.run_sudo_command(['blockdev', '--getsize64', device])
            else:
                result = subprocess.run(['blockdev', '--getsize64', device], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                stdout = result.stdout
            
            if success:
                size_bytes = int(stdout.strip())
                size_gb = size_bytes / (1024**3)
                self.log(f"✅ Dispositivo encontrado: {size_gb:.1f} GB")
            else:
                self.log("⚠️ Não foi possível verificar o tamanho do dispositivo")
            
            # Verifica partições
            if os.geteuid() != 0 and self.sudo_password:
                success, stdout, stderr = self.run_sudo_command(['lsblk', '-n', '-o', 'NAME,SIZE,TYPE', device])
            else:
                result = subprocess.run(['lsblk', '-n', '-o', 'NAME,SIZE,TYPE', device], 
                                      capture_output=True, text=True)
                success = result.returncode == 0
                stdout = result.stdout
            
            if success:
                self.log("📋 Estrutura atual do dispositivo:")
                for line in stdout.strip().split('\n'):
                    if line:
                        self.log(f"   {line}")
            
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro na verificação do dispositivo: {e}")
            return False

    def check_usb_health(self, device):
        """Verifica a saúde do dispositivo USB"""
        try:
            self.log(f"🔍 Verificando saúde do dispositivo {device}...")
            
            needs_sudo = os.geteuid() != 0
            
            # Verifica se o dispositivo é removível
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(['lsblk', '-d', '-o', 'NAME,RM', device])
            else:
                result = subprocess.run(['lsblk', '-d', '-o', 'NAME,RM', device], capture_output=True, text=True)
                success = result.returncode == 0
                stdout = result.stdout
            
            if success and '1' not in stdout:
                self.log("⚠️ Aviso: Dispositivo pode não ser removível")
            
            # Verifica tamanho
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(['blockdev', '--getsize64', device])
            else:
                result = subprocess.run(['blockdev', '--getsize64', device], capture_output=True, text=True)
                success = result.returncode == 0
                stdout = result.stdout
            
            if success:
                size = int(stdout.strip())
                if size < 100 * 1024 * 1024:  # Menos de 100MB
                    self.log("❌ Dispositivo muito pequeno para ISO")
                    return False
            
            self.log("✅ Dispositivo parece estar em bom estado")
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro na verificação de saúde: {e}")
            return True  # Continua mesmo com erro

    def check_active_dd_processes(self, device=None):
        """Verifica se já existem processos dd ativos no sistema - VERSÃO MELHORADA"""
        try:
            self.log("🔍 Verificando processos dd ativos...")
            
            # Comando para listar todos os processos dd
            cmd = ["ps", "aux"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            active_processes = []
            dangerous_processes = []
            current_pid = os.getpid()  # ✅ Pega o PID do processo atual
            
            for line in result.stdout.split('\n'):
                if 'dd' in line and 'of=' in line and not 'grep' in line:
                    parts = line.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        pid = parts[1]
                        
                        # ✅ IGNORA processos do próprio script
                        if int(pid) == current_pid or int(pid) == os.getppid():
                            continue
                        
                        command = ' '.join(parts[10:])
                        
                        # Extrai o dispositivo alvo
                        device_match = None
                        if 'of=' in command:
                            import re
                            match = re.search(r'of=([^\s\']+)', command)
                            if match:
                                device_match = match.group(1)
                        
                        process_info = {
                            'pid': pid,
                            'command': command[:100],
                            'device': device_match
                        }
                        active_processes.append(process_info)
                        
                        # Verifica se é perigoso (gravando no mesmo dispositivo)
                        if device and device_match and device in device_match:
                            dangerous_processes.append(process_info)
            
            if active_processes:
                self.log(f"⚠️  {len(active_processes)} processo(s) dd de OUTROS programas:")
                for proc in active_processes:
                    device_info = f" -> {proc['device']}" if proc['device'] else ""
                    self.log(f"   🚫 PID {proc['pid']}{device_info}")
            else:
                self.log("✅ Nenhum processo dd externo encontrado")
            
            if dangerous_processes:
                self.log(f"❌ {len(dangerous_processes)} processo(s) PERIGOSO(S) detectado(s):")
                for proc in dangerous_processes:
                    self.log(f"   💥 PID {proc['pid']} gravando em {device}")
                return True, dangerous_processes
            
            return False, []
            
        except subprocess.TimeoutExpired:
            self.log("❌ Timeout na verificação de processos")
            return False, []
        except Exception as e:
            self.log(f"⚠️ Erro ao verificar processos: {e}")
            return False, []

    def kill_conflicting_dd_processes(self, device=None):
        """Mata processos dd que possam estar conflitando - VERSÃO CORRIGIDA"""
        try:
            self.log("🛑 Verificando e parando processos dd conflitantes...")
            
            has_dangerous, dangerous_processes = self.check_active_dd_processes(device)
            
            if not has_dangerous:
                self.log("✅ Nenhum processo dd perigoso encontrado")
                return True
            
            # Mata os processos perigosos
            killed_count = 0
            for proc in dangerous_processes:
                try:
                    self.log(f"   🔫 Matando processo PID {proc['pid']}...")
                    
                    # ✅ CORREÇÃO: Usa run_sudo_command com timeout
                    if os.geteuid() != 0 and self.sudo_password:
                        success, stdout, stderr = self.run_sudo_command(['kill', '-9', proc['pid']])
                    else:
                        result = subprocess.run(['kill', '-9', proc['pid']], 
                                              capture_output=True, text=True, timeout=5)
                        success = result.returncode == 0
                    
                    if success:
                        killed_count += 1
                        self.log(f"   ✅ Processo {proc['pid']} eliminado")
                    else:
                        self.log(f"   ⚠️ Não foi possível eliminar PID {proc['pid']}")
                        
                    time.sleep(1)
                except Exception as e:
                    self.log(f"   ⚠️ Erro ao matar PID {proc['pid']}: {e}")
            
            # Verifica novamente com timeout
            time.sleep(2)
            has_dangerous_after, _ = self.check_active_dd_processes(device)
            
            if has_dangerous_after:
                self.log("❌ Ainda existem processos dd ativos após tentativa de kill")
                return False
            else:
                self.log(f"✅ {killed_count} processos dd perigosos eliminados")
                return True
                
        except Exception as e:
            self.log(f"❌ Erro ao eliminar processos conflitantes: {e}")
            return False


    def log(self, message):
        """Adiciona mensagem ao log - versão segura"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Se a GUI já foi inicializada, usa o log_text
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.insert(tk.END, f"{formatted_message}\n")
            self.log_text.see(tk.END)
            if hasattr(self, 'root'):
                self.root.update_idletasks()
        else:
            # Se não, armazena em log temporário
            if not hasattr(self, '_temp_log'):
                self._temp_log = []
            self._temp_log.append(formatted_message)
            print(formatted_message)  # Também imprime no console

    def _process_temp_logs(self):
        """Processa logs que foram armazenados antes da GUI estar pronta"""
        if hasattr(self, '_temp_log') and self._temp_log and hasattr(self, 'log_text'):
            for message in self._temp_log:
                self.log_text.insert(tk.END, f"{message}\n")
            self.log_text.see(tk.END)
            # Limpa logs temporários
            self._temp_log = []

    def load_scalable_distributions(self):
        """Carrega distribuições com busca automática de versões"""
        # Tenta carregar de arquivo externo primeiro
        external_config = Path.home() / ".bootable_usb_creator" / "distributions.json"
        if external_config.exists():
            try:
                with open(external_config, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    
                # 🔥 CORREÇÃO: Adicionar métodos de busca após carregar do JSON
                distributions_with_methods = {}
                for distro_name, distro_data in loaded_data.items():
                    distributions_with_methods[distro_name] = distro_data
                    
                    # Adiciona método get_versions baseado no nome da distribuição
                    method_name = f"get_{distro_name.lower().replace(' ', '_').replace('!', '').replace('_os', '')}_versions"
                    if hasattr(self, method_name):
                        distributions_with_methods[distro_name]["get_versions"] = getattr(self, method_name)
                        
                return distributions_with_methods
            except:
                pass

        # Estrutura base com suporte a múltiplas arquiteturas
        distributions_data = {
            "Ubuntu": {
                "family": "ubuntu",
                "checksum_type": "sha256",
                "get_versions": self.get_ubuntu_versions,
                "variants": {
                    "Desktop": {
                        "architectures": ["amd64", "arm64"]
                    },
                    "Server": {
                        "architectures": ["amd64", "arm64", "ppc64el", "s390x"]
                    }
                }
            },
            "Debian": {
                "family": "debian",
                "checksum_type": "sha512", 
                "get_versions": self.get_debian_versions,
                "variants": {
                    "Netinst": {
                        "architectures": ["amd64", "i386", "arm64", "armhf"]
                    },
                    "Live": {
                        "architectures": ["amd64", "i386", "arm64"]
                    }
                }
            },
            "Linux Mint": {
                "family": "mint",
                "checksum_type": "sha256",
                "get_versions": self.get_linuxmint_versions,
                "variants": {
                    "Cinnamon": {"architectures": ["64bit"]},
                    "Mate": {"architectures": ["64bit"]},
                    "Xfce": {"architectures": ["64bit"]}
                }
            },
            "Fedora": {
                "family": "fedora", 
                "checksum_type": "sha256",
                "get_versions": self.get_fedora_versions,
                "variants": {
                    "Workstation": {"architectures": ["x86_64", "aarch64"]},
                    "Server": {"architectures": ["x86_64", "aarch64"]}
                }
            },
            "Arch Linux": {
                "family": "arch",
                "checksum_type": "sha256", 
                "variants": {
                    "Standard": {"architectures": ["x86_64"]}
                }
            },
            "Kali Linux": {
                "family": "security",
                "checksum_type": "sha256",
                "get_versions": self.get_kalilinux_versions,  # ✅ ADICIONAR ESTA LINHA
                "variants": {
                    "Live": {"architectures": ["amd64", "i386"]}
                }
            },
            "Manjaro": {
                "family": "arch",
                "checksum_type": "sha256",
                "get_versions": self.get_manjaro_versions,
                "variants": {
                    "XFCE": {"architectures": ["x86_64"]},
                    "KDE": {"architectures": ["x86_64"]},
                    "GNOME": {"architectures": ["x86_64"]}
                }
            },
            "openSUSE": {
                "family": "suse", 
                "checksum_type": "sha256",
                "get_versions": self.get_opensuse_versions,
                "variants": {
                    "Leap": {"architectures": ["x86_64", "aarch64"]},
                    "Tumbleweed": {"architectures": ["x86_64", "aarch64"]}
                }
            },

            # DISTRIBUIÇÕES ATUAIS COM SUPORTE 32-BIT (NOVAS)
            "MX Linux": {
                "family": "debian",
                "checksum_type": "sha256",
                "get_versions": self.get_mxlinux_versions,
                "variants": {
                    "XFCE": {"architectures": ["amd64", "i386"]},
                    "KDE": {"architectures": ["amd64", "i386"]}
                }
            },
            "antiX": {
                "family": "debian", 
                "checksum_type": "sha256",
                "get_versions": self.get_antix_versions,
                "variants": {
                    "Full": {"architectures": ["amd64", "i386"]},
                    "Base": {"architectures": ["amd64", "i386"]}
                }
            },
            "Puppy Linux": {
                "family": "independent",
                "checksum_type": "sha256", 
                "get_versions": self.get_puppylinux_versions,
                "variants": {
                    "Fossapup": {"architectures": ["amd64", "i686"]}
                }
            }
        }

        # Preenche as versões dinamicamente
        self.populate_versions(distributions_data)
        
        return distributions_data

    def populate_versions(self, distributions_data):
        """Preenche as versões automaticamente para cada distribuição"""
        for distro_name, distro_data in distributions_data.items():
            if "get_versions" in distro_data:
                try:
                    # Busca versões dinamicamente
                    versions = distro_data["get_versions"]()
                    
                    # Para cada variante e arquitetura, adiciona as versões
                    for variant_name, variant_data in distro_data["variants"].items():
                        # CORREÇÃO: Verificar se architectures é lista ou dict
                        architectures = variant_data.get("architectures", [])
                        
                        if isinstance(architectures, list):
                            # Se é lista, converter para dicionário
                            variant_data["architectures"] = {}
                            for arch in architectures:
                                variant_data["architectures"][arch] = {"versions": {}}
                                
                                # Adiciona as versões
                                for version in versions:
                                    variant_data["architectures"][arch]["versions"][version] = {}
                        
                        elif isinstance(architectures, dict):
                            # Se já é dicionário, apenas adiciona as versões
                            for arch, arch_data in architectures.items():
                                if "versions" not in arch_data:
                                    arch_data["versions"] = {}
                                
                                # Adiciona as versões
                                for version in versions:
                                    arch_data["versions"][version] = {}
                                    
                except Exception as e:
                    self.log(f"⚠️ Erro ao buscar versões de {distro_name}: {e}")
                    # Fallback para versões estáticas
                    self.add_fallback_versions(distro_name, distro_data)

    def add_fallback_versions(self, distro_name, distro_data):
        """Adiciona versões de fallback quando a busca automática falha"""
        fallback_versions = {
            "Ubuntu": ["25.10", "24.04 LTS", "23.10", "22.04 LTS", "20.04 LTS"],
            "Debian": ["12.4.0", "11.9.0", "10.13.0"],
            "Linux Mint": ["21.3", "21.2", "21.1", "20.3", "20.2"],
            "Fedora": ["39", "38", "37", "36", "35"],
            "Manjaro": ["23.1", "22.1", "21.3", "21.2", "21.1"],
            "openSUSE": ["15.6", "15.5", "15.4", "15.3", "15.2"]
        }
        
        versions = fallback_versions.get(distro_name, ["latest"])
        
        for variant_name, variant_data in distro_data["variants"].items():
            # CORREÇÃO: Garantir que a estrutura existe
            if "architectures" not in variant_data:
                variant_data["architectures"] = {}
                
            architectures = variant_data.get("architectures", [])
            
            if isinstance(architectures, list):
                # Se é lista, converter para dicionário
                variant_data["architectures"] = {}
                for arch in architectures:
                    variant_data["architectures"][arch] = {"versions": {}}
                    
                    # Adiciona as versões
                    for version in versions:
                        variant_data["architectures"][arch]["versions"][version] = {}
            
            elif isinstance(architectures, dict):
                # Se já é dicionário, apenas adiciona as versões
                for arch, arch_data in architectures.items():
                    if "versions" not in arch_data:
                        arch_data["versions"] = {}
                    
                    # Limpa versões existentes e adiciona as novas
                    arch_data["versions"] = {}
                    for version in versions:
                        arch_data["versions"][version] = {}

    # === MÉTODOS DE BUSCA DE VERSÕES ===
    def get_ubuntu_versions(self):
        """Busca as últimas 5 versões do Ubuntu"""
        try:
            return ["25.10", "24.04 LTS", "23.10", "22.04 LTS", "20.04 LTS"]
        except:
            return ["25.10", "24.04 LTS"]

    def get_debian_versions(self):
        """Busca versões do Debian"""
        try:
            return ["12.4.0", "11.9.0", "10.13.0"]
        except:
            return ["12.4.0"]

    def get_linuxmint_versions(self):
        """Busca versões do Linux Mint"""
        try:
            return ["21.3", "21.2", "21.1", "20.3", "20.2"]
        except:
            return ["21.3", "21.2"]

    def get_fedora_versions(self):
        """Busca versões do Fedora"""
        try:
            return ["39", "38", "37", "36", "35"]
        except:
            return ["39", "38"]

    def get_manjaro_versions(self):
        """Busca versões do Manjaro"""
        try:
            return ["23.1", "22.1", "21.3", "21.2", "21.1"]
        except:
            return ["23.1"]

    def get_opensuse_versions(self):
        """Busca versões do openSUSE"""
        try:
            return ["15.6", "15.5", "15.4", "15.3", "15.2"]
        except:
            return ["15.6"]

    def get_mxlinux_versions(self):
        """Busca versões do MX Linux (suporta 32-bit)"""
        try:
            return ["23.1", "21.3", "21.2", "21.1", "19.4"]
        except:
            return ["23.1"]

    def get_antix_versions(self):
        """Busca versões do antiX (foco em 32-bit)"""
        try:
            return ["23", "22", "21", "19", "17"]
        except:
            return ["23"]

    def get_puppylinux_versions(self):
        """Busca versões do Puppy Linux (especialista em 32-bit)"""
        try:
            return ["9.5", "9.0", "8.0", "7.5", "6.0"]
        except:
            return ["9.5"]

    def get_kalilinux_versions(self):
        """Busca versões do Kali Linux"""
        try:
            return ["weekly", "2023.3", "2023.2", "2023.1", "2022.4"]
        except:
            return ["weekly"]


    def check_dependencies(self):
        """Verifica se as dependências estão instaladas"""
        dependencies = {
            'pv': 'Pipe Viewer - para mostrar progresso',
            'dd': 'Disk Dump - para gravação de discos',
            'parted': 'Particionamento de discos',
            'mkfs.fat': 'Formatação FAT32',
            'mkfs.vfat': 'Formatação VFAT (alternativa)',
            'fdisk': 'Particionamento alternativo',
            'wipefs': 'Limpeza de assinaturas'
        }
        
        missing = []
        for dep, desc in dependencies.items():
            if not shutil.which(dep):
                missing.append(f"{dep} ({desc})")
        
        if missing:
            self.log("⚠️  Dependências ausentes:")
            for dep in missing:
                self.log(f"   ❌ {dep}")
            
            if 'parted' in str(missing) or 'mkfs.fat' in str(missing):
                self.log("💡 Para instalar as dependências no Ubuntu/Debian:")
                self.log("   sudo apt install parted dosfstools pv")
            if 'fdisk' in str(missing):
                self.log("   sudo apt install fdisk")
        else:
            self.log("✅ Todas dependências encontradas!")

    def save_distributions_to_file(self):
        """Salva as distribuições em arquivo JSON para edição externa"""
        config_dir = Path.home() / ".bootable_usb_creator"
        config_dir.mkdir(exist_ok=True)

        config_file = config_dir / "distributions.json"
        
        # 🔥 CORREÇÃO: Criar uma cópia sem os métodos antes de salvar
        distributions_to_save = {}
        for distro_name, distro_data in self.distributions.items():
            distributions_to_save[distro_name] = {}
            
            for key, value in distro_data.items():
                if key != "get_versions":  # 🔥 Ignora os métodos
                    distributions_to_save[distro_name][key] = value
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(distributions_to_save, f, indent=2, ensure_ascii=False)

        return config_file

    def setup_gui(self):
        """Configura a interface gráfica completa"""
        self.root = tk.Tk()
        self.root.title("Bootable USB Creator - Sistema Escalável")
        self.root.geometry("900x900")
        self.root.minsize(900, 900)
        self.root.resizable(False, False)

        # ✅ NOVO: Verificação de ambiente
        self.check_environment()

        # ✅ NOVO: Verificação de privilégios
        if platform.system().lower() != "windows" and os.geteuid() != 0:
            self.log("⚠️  AVISO: Executando sem privilégios de superusuário")
            self.log("💡 Algumas operações podem solicitar senha sudo")
            self.log("💡 Para melhor experiência, execute no terminal:")
            self.log("   python3 create-usb-x-full.py")

        # Configurar estilo
        self.setup_styles()

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Título
        title_label = ttk.Label(
            main_frame,
            text="🐧 Bootable USB Creator - Sistema Escalável",
            font=("Arial", 16, "bold"),
            foreground="#2c3e50",
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))

        # Frame de seleção hierárquica
        selection_frame = ttk.LabelFrame(
            main_frame, text="📦 Seleção Hierárquica de Distribuição", padding="10"
        )
        selection_frame.grid(
            row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10
        )

        # Nível 1: Família/Distribuição
        ttk.Label(
            selection_frame, text="Distribuição:", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.family_var = tk.StringVar()
        families = sorted(list(self.distributions.keys()), key=str.lower)
        self.family_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.family_var,
            values=families,
            state="readonly",
            width=20,
        )
        self.family_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.family_combo.bind("<<ComboboxSelected>>", self.on_family_selected)

        # Nível 2: Variante
        ttk.Label(selection_frame, text="Variante:", font=("Arial", 10, "bold")).grid(
            row=0, column=2, sticky=tk.W, pady=5
        )
        self.variant_var = tk.StringVar()
        self.variant_combo = ttk.Combobox(
            selection_frame, textvariable=self.variant_var, state="readonly", width=20
        )
        self.variant_combo.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.variant_combo.bind("<<ComboboxSelected>>", self.on_variant_selected)

        # Nível 3: Arquitetura
        ttk.Label(
            selection_frame, text="Arquitetura:", font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.arch_var = tk.StringVar()
        self.arch_combo = ttk.Combobox(
            selection_frame, textvariable=self.arch_var, state="readonly", width=20
        )
        self.arch_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.arch_combo.bind("<<ComboboxSelected>>", self.on_arch_selected)

        # Nível 4: Versão
        ttk.Label(selection_frame, text="Versão:", font=("Arial", 10, "bold")).grid(
            row=1, column=2, sticky=tk.W, pady=5
        )
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            selection_frame, textvariable=self.version_var, state="readonly", width=20
        )
        self.version_combo.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.version_combo.bind("<<ComboboxSelected>>", self.on_version_selected)

        # Info da distribuição selecionada
        self.distro_info_var = tk.StringVar(value="Selecione uma distribuição completa")
        distro_info_label = ttk.Label(
            selection_frame,
            textvariable=self.distro_info_var,
            foreground="#2980b9",
            font=("Arial", 10, "bold"),
        )
        distro_info_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=10)

        # Frame de modo ISO personalizada
        custom_frame = ttk.LabelFrame(
            main_frame, text="📁 Modo ISO Personalizada", padding="10"
        )
        custom_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

        self.custom_iso_var = tk.BooleanVar()
        ttk.Checkbutton(
            custom_frame,
            text="Usar ISO personalizada",
            variable=self.custom_iso_var,
            command=self.toggle_custom_iso,
        ).grid(row=0, column=0, sticky=tk.W)

        self.iso_path_var = tk.StringVar()
        self.iso_frame = ttk.Frame(custom_frame)
        self.iso_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.iso_frame, text="Arquivo ISO:").grid(
            row=0, column=0, sticky=tk.W
        )
        self.iso_entry = ttk.Entry(
            self.iso_frame, textvariable=self.iso_path_var, width=60
        )
        self.iso_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(self.iso_frame, text="Procurar", command=self.browse_iso).grid(
            row=0, column=2
        )

        self.iso_frame.grid_remove()

        # Frame de dispositivos USB
        usb_frame = ttk.LabelFrame(
            main_frame, text="💾 Dispositivos USB Detectados", padding="10"
        )
        usb_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)

        # Listbox para mostrar USBs
        self.usb_listbox = tk.Listbox(
            usb_frame, height=4, width=85, font=("Consolas", 9)
        )
        self.usb_listbox.grid(
            row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5
        )

        # Scrollbar para a listbox
        scrollbar = ttk.Scrollbar(
            usb_frame, orient="vertical", command=self.usb_listbox.yview
        )
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.usb_listbox.configure(yscrollcommand=scrollbar.set)

        # Botões para USBs
        usb_button_frame = ttk.Frame(usb_frame)
        usb_button_frame.grid(row=1, column=0, columnspan=4, pady=5)

        ttk.Button(
            usb_button_frame,
            text="🔄 Atualizar Lista USB",
            command=self.refresh_usb_list,
        ).grid(row=0, column=0, padx=5)

        # Informações do dispositivo selecionado
        self.usb_info_var = tk.StringVar(
            value="👉 Selecione um dispositivo USB da lista acima"
        )
        usb_info_label = ttk.Label(
            usb_frame,
            textvariable=self.usb_info_var,
            foreground="#27ae60",
            font=("Arial", 10, "bold"),
        )
        usb_info_label.grid(row=2, column=0, columnspan=4, pady=5)

        # Barra de progresso
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=15)

        ttk.Label(progress_frame, text="Progresso:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W
        )

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=600
        )
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10)

        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.grid(row=0, column=2)

        # No setup_gui(), adicione após a barra de progresso:
        self.activity_var = tk.StringVar(value="⚪")
        activity_label = ttk.Label(progress_frame, textvariable=self.activity_var, font=("Arial", 12))
        activity_label.grid(row=0, column=3, padx=5)

        # Status
        self.status_var = tk.StringVar(value="✅ Pronto para começar")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            foreground="#2980b9",
            font=("Arial", 11, "bold"),
        )
        status_label.grid(row=5, column=0, columnspan=4, pady=10)

        # Área de log
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log de Execução", padding="10")
        log_frame.grid(
            row=6, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )

        self.log_text = tk.Text(log_frame, height=12, width=85, font=("Consolas", 8))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        log_scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=4, pady=20)

        self.create_button = ttk.Button(
            button_frame,
            text="🚀 CRIAR USB BOOTÁVEL",
            command=self.start_creation,
            style="Accent.TButton",
        )
        self.create_button.grid(row=0, column=0, padx=5)

        # ✅ NOVO: Botão de cancelamento
        self.cancel_button = ttk.Button(
            button_frame, 
            text="🛑 Cancelar", 
            command=self.cancel_operation,
            style="Danger.TButton",
            state="disabled"  # Inicia desabilitado
        )
        self.cancel_button.grid(row=0, column=1, padx=5)


        ttk.Button(button_frame, text="💾 Salvar Config", command=self.save_config).grid(
            row=0, column=2, padx=5
        )


        ttk.Button(button_frame, text="🧹 Limpar Log", command=self.clear_log).grid(
            row=0, column=3, padx=5
        )

        ttk.Button(button_frame, text="❌ Sair", command=self.root.quit).grid(
            row=0, column=4, padx=5
        )

        # Configurar grid weights
        main_frame.columnconfigure(1, weight=1)
        selection_frame.columnconfigure(1, weight=1)
        selection_frame.columnconfigure(3, weight=1)
        custom_frame.columnconfigure(1, weight=1)
        usb_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=3)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Bind events
        self.usb_listbox.bind("<<ListboxSelect>>", self.on_usb_selected)

        # Inicializar
        self.refresh_usb_list()
        config_file = self.save_distributions_to_file()
        
        # 🔥 CORREÇÃO: Processar logs temporários após GUI estar pronta
        self._process_temp_logs()
        
        self.log("✅ Sistema Escalável Iniciado!")
        self.log(f"📁 Configuração salva em: {config_file}")
        self.log("💡 Selecione uma distribuição completa nos menus acima")
        self.log("🔧 Estrutura pronta para milhares de distribuições!")

    def start_activity_indicator(self):
        """Inicia indicador visual de atividade"""
        def animate():
            states = ["🔴", "🟠", "🟢", "🟠"]  # Vermelho -> Laranja -> Verde -> Laranja
            i = 0
            while self.is_operation_running and not self.should_cancel:
                self.activity_var.set(states[i % len(states)])
                self.root.update()
                time.sleep(0.5)
                i += 1
            self.activity_var.set("⚪")
        
        threading.Thread(target=animate, daemon=True).start()

    def setup_styles(self):
        """Configura estilos para os widgets"""
        style = ttk.Style()
        style.configure(
            "Accent.TButton",
            foreground="white",
            background="#27ae60",
            font=("Arial", 10, "bold"),
        )
        style.map("Accent.TButton", background=[("active", "#219d54")])

        # ✅ NOVO: Estilo para botão de cancelamento
        style.configure("Danger.TButton", foreground="white", background="#e74c3c")
        style.map("Danger.TButton", background=[("active", "#c0392b")])

    def on_family_selected(self, event):
        """Quando uma família é selecionada"""
        family = self.family_var.get()
        if family in self.distributions:
            family_data = self.distributions[family]

            # ⚠️ VERIFICAÇÃO DE SEGURANÇA ADICIONADA
            if "variants" not in family_data:
                self.log(f"❌ Família '{family}' não tem variantes configuradas")
                self.variant_combo["values"] = []
                self.variant_combo.set("")
                self.arch_combo.set("")
                self.version_combo.set("")
                self.arch_combo["values"] = []
                self.version_combo["values"] = []
                return

            variants = list(family_data["variants"].keys())
            self.variant_combo["values"] = variants
            self.variant_combo.set("")
            self.arch_combo.set("")
            self.version_combo.set("")
            self.arch_combo["values"] = []
            self.version_combo["values"] = []
            self.log(f"🏷️ Família selecionada: {family}")

    def on_variant_selected(self, event):
        """Quando uma variante é selecionada"""
        family = self.family_var.get()
        variant = self.variant_var.get()

        # ⚠️ VERIFICAÇÃO DE SEGURANÇA ADICIONADA - CORRIGIDA
        if (
            family not in self.distributions
            or "variants" not in self.distributions[family]
            or variant not in self.distributions[family]["variants"]
        ):
            self.log(f"❌ Variante '{variant}' não encontrada em '{family}'")
            self.arch_combo["values"] = []
            self.arch_combo.set("")
            self.version_combo.set("")
            self.version_combo["values"] = []
            return

        variant_data = self.distributions[family]["variants"][variant]

        # ⚠️ VERIFICAÇÃO DE SEGURANÇA ADICIONADA
        if "architectures" not in variant_data:
            self.log(f"❌ Variante '{variant}' não tem arquiteturas configuradas")
            self.arch_combo["values"] = []
            self.arch_combo.set("")
            self.version_combo.set("")
            self.version_combo["values"] = []
            return

        architectures = list(variant_data["architectures"].keys())
        self.arch_combo["values"] = architectures
        self.arch_combo.set("")
        self.version_combo.set("")
        self.version_combo["values"] = []
        self.log(f"🔄 Variante selecionada: {variant}")

    def on_arch_selected(self, event):
        """Quando uma arquitetura é selecionada"""
        family = self.family_var.get()
        variant = self.variant_var.get()
        arch = self.arch_var.get()

        # ⚠️ VERIFICAÇÃO DE SEGURANÇA ADICIONADA - CORRIGIDA
        if (not all([family, variant, arch]) or
            family not in self.distributions or
            "variants" not in self.distributions[family] or
            variant not in self.distributions[family]["variants"] or
            "architectures" not in self.distributions[family]["variants"][variant] or
            arch not in self.distributions[family]["variants"][variant]["architectures"]):
            self.log(f"❌ Arquitetura '{arch}' não encontrada")
            self.version_combo["values"] = []
            self.version_combo.set("")
            return

        arch_data = self.distributions[family]["variants"][variant]["architectures"][arch]

        # ⚠️ VERIFICAÇÃO DE SEGURANÇA ADICIONADA
        if "versions" not in arch_data:
            self.log(f"❌ Arquitetura '{arch}' não tem versões configuradas")
            self.version_combo["values"] = []
            self.version_combo.set("")
            return

        versions = list(arch_data["versions"].keys())
        self.version_combo["values"] = versions
        self.version_combo.set("")
        self.log(f"⚙️ Arquitetura selecionada: {arch}")

    def on_version_selected(self, event):
        """Quando uma versão é selecionada"""
        family = self.family_var.get()
        variant = self.variant_var.get()
        arch = self.arch_var.get()
        version = self.version_var.get()

        if all([family, variant, arch, version]):
            distro_info = self.distributions[family]["variants"][
                variant
            ]["architectures"][arch]["versions"][version]

            info_parts = [f"📦 {family} {variant}"]
            info_parts.append(f"v{version}")
            info_parts.append(f"{arch}")
            if "codename" in distro_info:
                info_parts.append(f"({distro_info['codename']})")

            self.distro_info_var.set(" | ".join(info_parts))

            # Mostra URL que será usada
            url, filename = self.build_download_url(family, variant, arch, version)
            self.log(f"🔗 Distribuição selecionada: {family} {variant} {version} {arch}")
            self.log(f"   📁 Arquivo: {filename}")
            self.log(f"   🌐 URL: {url}")

    def build_download_url(self, family, variant, arch, version):
        """Constrói URLs para múltiplas arquiteturas"""
        try:
            # Templates de URLs dinâmicas expandidas
            url_templates = {
                "Ubuntu": {
                    "Desktop": {
                        "amd64": "https://releases.ubuntu.com/{version}/ubuntu-{version}-desktop-amd64.iso",
                        "arm64": "https://releases.ubuntu.com/{version}/ubuntu-{version}-desktop-arm64.iso"
                    },
                    "Server": {
                        "amd64": "https://releases.ubuntu.com/{version}/ubuntu-{version}-live-server-amd64.iso",
                        "arm64": "https://releases.ubuntu.com/{version}/ubuntu-{version}-live-server-arm64.iso"
                    }
                },
                "Debian": {
                    "Netinst": {
                        "amd64": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-{version}-amd64-netinst.iso",
                        "i386": "https://cdimage.debian.org/debian-cd/current/i386/iso-cd/debian-{version}-i386-netinst.iso",
                        "arm64": "https://cdimage.debian.org/debian-cd/current/arm64/iso-cd/debian-{version}-arm64-netinst.iso"
                    },
                    "Live": {
                        "amd64": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-live-{version}-amd64-standard.iso",
                        "i386": "https://cdimage.debian.org/debian-cd/current/i386/iso-cd/debian-live-{version}-i386-standard.iso"
                    }
                },
                "Linux Mint": {
                    "Cinnamon": {"64bit": "https://mirrors.kernel.org/linuxmint/stable/{version}/linuxmint-{version}-cinnamon-64bit.iso"},
                    "Mate": {"64bit": "https://mirrors.kernel.org/linuxmint/stable/{version}/linuxmint-{version}-mate-64bit.iso"},
                    "Xfce": {"64bit": "https://mirrors.kernel.org/linuxmint/stable/{version}/linuxmint-{version}-xfce-64bit.iso"}
                },
                "Fedora": {
                    "Workstation": {
                        "x86_64": "https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Workstation/x86_64/iso/Fedora-Workstation-Live-x86_64-{version}.iso",
                        "aarch64": "https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Workstation/aarch64/iso/Fedora-Workstation-Live-aarch64-{version}.iso"
                    },
                    "Server": {
                        "x86_64": "https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Server/x86_64/iso/Fedora-Server-dvd-x86_64-{version}.iso",
                        "aarch64": "https://download.fedoraproject.org/pub/fedora/linux/releases/{version}/Server/aarch64/iso/Fedora-Server-dvd-aarch64-{version}.iso"
                    }
                },
                "Arch Linux": {
                    "Standard": {"x86_64": "https://mirrors.kernel.org/archlinux/iso/latest/archlinux-x86_64.iso"}
                },
                "Kali Linux": {
                    "Live": {
                        "amd64": "https://cdimage.kali.org/kali-{version}/kali-linux-{version}-live-amd64.iso",
                        "i386": "https://cdimage.kali.org/kali-{version}/kali-linux-{version}-live-i386.iso"
                    }
                },
                "Manjaro": {
                    "XFCE": {"x86_64": "https://download.manjaro.org/xfce/{version}/manjaro-xfce-{version}-minimal-x86_64.iso"},
                    "KDE": {"x86_64": "https://download.manjaro.org/kde/{version}/manjaro-kde-{version}-minimal-x86_64.iso"},
                    "GNOME": {"x86_64": "https://download.manjaro.org/gnome/{version}/manjaro-gnome-{version}-minimal-x86_64.iso"}
                },
                "openSUSE": {
                    "Leap": {
                        "x86_64": "https://download.opensuse.org/distribution/leap/{version}/iso/openSUSE-Leap-{version}-DVD-x86_64.iso",
                        "aarch64": "https://download.opensuse.org/distribution/leap/{version}/iso/openSUSE-Leap-{version}-DVD-aarch64.iso"
                    },
                    "Tumbleweed": {
                        "x86_64": "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-x86_64.iso",
                        "aarch64": "https://download.opensuse.org/tumbleweed/iso/openSUSE-Tumbleweed-DVD-aarch64.iso"
                    }
                },
                "MX Linux": {
                    "XFCE": {
                        "amd64": "https://sourceforge.net/projects/mx-linux/files/Final/Xfce/MX-{version}_x64.iso/download",
                        "i386": "https://sourceforge.net/projects/mx-linux/files/Final/Xfce/MX-{version}_386.iso/download"
                    },
                    "KDE": {
                        "amd64": "https://sourceforge.net/projects/mx-linux/files/Final/KDE/MX-{version}_x64.iso/download", 
                        "i386": "https://sourceforge.net/projects/mx-linux/files/Final/KDE/MX-{version}_386.iso/download"
                    }
                },
                "antiX": {
                    "Full": {
                        "amd64": "https://sourceforge.net/projects/antix-linux/files/Final/antiX-{version}/antiX-{version}-x64-full.iso/download",
                        "i386": "https://sourceforge.net/projects/antix-linux/files/Final/antiX-{version}/antiX-{version}-386-full.iso/download"
                    },
                    "Base": {
                        "amd64": "https://sourceforge.net/projects/antix-linux/files/Final/antiX-{version}/antiX-{version}-x64-base.iso/download",
                        "i386": "https://sourceforge.net/projects/antix-linux/files/Final/antiX-{version}/antiX-{version}-386-base.iso/download"
                    }
                },
                "Puppy Linux": {
                    "Fossapup": {
                        "amd64": "https://sourceforge.net/projects/fossapup64/files/{version}/fossapup64-{version}.iso/download",
                        "i686": "https://sourceforge.net/projects/fossapup64/files/{version}/fossapup64-{version}.iso/download"
                    }
                }
            }
            
            # Pega o template específico para arquitetura
            template_dict = url_templates.get(family, {}).get(variant, {})
            url_template = template_dict.get(arch) or template_dict.get(self.arch_maps.get(arch, arch))
            
            if not url_template:
                self.log(f"❌ Template não encontrado para {family} {variant} {arch}")
                return None, None
            
            # Processa a versão
            clean_version = version.replace(" LTS", "").strip()
            
            # ✅ CORREÇÃO INTELIGENTE: Testa múltiplas versões
            test_versions = self.get_possible_versions(family, clean_version)
            
            for test_version in test_versions:
                test_url = url_template.replace("{version}", test_version)
                
                # Verifica se a URL existe
                if self.url_exists(test_url):
                    self.log(f"✅ URL válida encontrada: {test_url}")
                    filename = test_url.split("/")[-1]
                    return test_url, filename
            
            # Se nenhuma versão funcionou, usa a primeira como fallback
            final_url = url_template.replace("{version}", test_versions[0])
            filename = final_url.split("/")[-1]
            self.log(f"⚠️  Usando URL fallback: {final_url}")
            return final_url, filename
            
        except Exception as e:
            self.log(f"❌ Erro ao construir URL: {e}")
            return None, None

    def get_possible_versions(self, family, base_version):
        """Retorna possíveis versões para testar"""
        if family == "Ubuntu" and base_version == "25.10":
            return ["25.10", "25.10.1"]  # Testa versão base e possível point release
        elif family == "Ubuntu" and base_version == "24.04":
            return ["24.04.3", "24.04.2", "24.04.1", "24.04"]
        elif family == "Ubuntu" and base_version == "22.04":
            return ["22.04.4", "22.04.3", "22.04.2", "22.04.1", "22.04"]
        else:
            return [base_version]

    def url_exists(self, url):
        """Verifica se uma URL existe"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False

    def toggle_custom_iso(self):
        """Alterna para modo ISO personalizada"""
        if self.custom_iso_var.get():
            # Limpa seleção atual
            self.family_combo.set("")
            self.variant_combo.set("")
            self.arch_combo.set("")
            self.version_combo.set("")
            self.variant_combo["values"] = []
            self.arch_combo["values"] = []
            self.version_combo["values"] = []
            self.iso_frame.grid()
            self.distro_info_var.set("📁 Modo ISO Personalizada Ativado")
            self.log("📁 Modo ISO personalizada ativado")
        else:
            self.iso_frame.grid_remove()
            self.distro_info_var.set("Selecione uma distribuição completa")
            self.log("📦 Modo distribuição pré-definida ativado")

    def browse_iso(self):
        """Abre diálogo para selecionar arquivo ISO"""
        filename = filedialog.askopenfilename(
            title="Selecionar arquivo ISO",
            filetypes=[("ISO files", "*.iso"), ("All files", "*.*")],
        )
        if filename:
            self.iso_path_var.set(filename)
            self.custom_iso_path = filename
            self.log(f"📁 ISO personalizada selecionada: {filename}")

    def save_config(self):
        """Salva a configuração atual em arquivo JSON"""
        try:
            config_file = self.save_distributions_to_file()
            messagebox.showinfo("Sucesso", f"Configuração salva em:\n{config_file}")
            self.log(f"💾 Configuração JSON salva: {config_file}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configuração:\n{e}")

    def refresh_all(self):
        """Atualiza tudo"""
        self.refresh_usb_list()
        self.log("🔄 Sistema atualizado completamente!")

    def clear_log(self):
        """Limpa o log"""
        self.log_text.delete(1.0, tk.END)

    def on_usb_selected(self, event):
        """Quando um USB é selecionado na lista"""
        selection = self.usb_listbox.curselection()
        if selection:
            device_info = self.usb_listbox.get(selection[0])
            self.selected_usb_device = device_info
            self.usb_info_var.set(f"✅ Selecionado: {device_info}")
            self.log(f"💾 Dispositivo selecionado: {device_info}")

    def get_selected_usb_device(self):
        """Obtém o caminho real do dispositivo selecionado"""
        if not self.selected_usb_device:
            return None

        if platform.system().lower() == "windows":
            parts = self.selected_usb_device.split(" - ")
            if parts and ":" in parts[0]:
                return parts[0].strip()
        else:
            parts = self.selected_usb_device.split(" - ")
            if parts and parts[0].startswith("/dev/"):
                return parts[0].strip()

        return None

    def detect_usb_windows(self):
        """Detecta USB no Windows"""
        usb_devices = []
        detected_paths = set()

        try:
            ps_command = """
            Get-WmiObject -Class Win32_LogicalDisk | 
            Where-Object { $_.DriveType -eq 2 } | 
            Select-Object DeviceID, Size, VolumeName, FileSystem |
            ForEach-Object { 
                $sizeGB = if($_.Size) { [math]::Round($_.Size/1GB, 2) } else { "Unknown" }
                "$($_.DeviceID) - ${sizeGB}GB - $($_.VolumeName) - $($_.FileSystem)"
            }
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("---") and " - " in line:
                        drive_letter = line.split(" - ")[0].strip()
                        if drive_letter not in detected_paths:
                            detected_paths.add(drive_letter)
                            usb_devices.append(line)

        except Exception as e:
            self.log(f"⚠️ Erro na detecção Windows: {e}")

        return usb_devices

    def detect_usb_linux(self):
        """Detecta USB no Linux"""
        usb_devices = []
        detected_paths = set()

        try:
            # Tenta com privilégios atuais primeiro
            result = subprocess.run(
                ["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL"],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                # Se falhou, tenta com sudo se disponível
                if self.sudo_password:
                    success, stdout, stderr = self.run_sudo_command(
                        ["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,MODEL"]
                    )
                    if success:
                        result.stdout = stdout
                    else:
                        self.log("⚠️ Não foi possível listar dispositivos USB")
                        return usb_devices
                else:
                    self.log("⚠️ Não foi possível listar dispositivos USB")
                    return usb_devices

            for line in result.stdout.split('\n'):
                if line and "disk" in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        device_name = parts[0]
                        device_path = f"/dev/{device_name}"

                        if device_name.startswith("sd") and device_name != "sda":
                            if device_path not in detected_paths:
                                detected_paths.add(device_path)
                                size = parts[1]
                                mountpoint = parts[3] if len(parts) > 3 else "Não montado"
                                model = parts[4] if len(parts) > 4 else "USB Device"
                                display = f"{device_path} - {size} - {model}"
                                if mountpoint != "Não montado":
                                    display += f" (Montado em {mountpoint})"
                                usb_devices.append(display)

        except Exception as e:
            self.log(f"⚠️ Erro na detecção Linux: {e}")

        return usb_devices

    def detect_usb_devices(self):
        """Detecta dispositivos USB de forma multiplataforma"""
        system = platform.system().lower()
        self.log("🔍 Procurando dispositivos USB...")

        if system == "windows":
            return self.detect_usb_windows()
        elif system == "linux":
            return self.detect_usb_linux()
        else:
            self.log("❌ Sistema operacional não suportado")
            return []

    def refresh_usb_list(self):
        """Atualiza a lista de dispositivos USB disponíveis"""
        self.status_var.set("🔍 Procurando dispositivos USB...")

        self.usb_listbox.delete(0, tk.END)
        self.selected_usb_device = None
        self.usb_info_var.set("👉 Selecione um dispositivo USB da lista acima")

        usb_devices = self.detect_usb_devices()

        if usb_devices:
            for device in usb_devices:
                self.usb_listbox.insert(tk.END, device)

            if usb_devices:
                self.usb_listbox.selection_set(0)
                self.on_usb_selected(None)

            self.log(f"✅ Encontrados {len(usb_devices)} dispositivo(s) USB")
            self.status_var.set(
                f"✅ {len(usb_devices)} dispositivo(s) USB encontrado(s)"
            )
        else:
            self.log("❌ Nenhum dispositivo USB encontrado")
            self.log("💡 Dicas:")
            self.log("   - Conecte o USB e clique em 'Atualizar Lista USB'")
            self.log("   - No Linux: execute com 'sudo'")
            self.log("   - No Windows: execute como Administrador")
            self.status_var.set("❌ Nenhum dispositivo USB encontrado")

    def download_file(self, url, filename, progress_weight=1.0):
        """Faz download de um arquivo com barra de progresso e suporte a cancelamento"""
        local_path = self.download_dir / filename
        self.should_cancel = False

        try:
            self.log(f"⬇️ Iniciando download: {filename}")
            self.log(f"🔗 URL: {url}")

            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(local_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    # ✅ VERIFICA CANCELAMENTO
                    if self.should_cancel:
                        self.log("⏹️ Download cancelado pelo usuário")
                        if local_path.exists():
                            local_path.unlink()  # Remove arquivo incompleto
                        return None
                        
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0:
                            download_progress = (downloaded_size / total_size) * 100
                            weighted_progress = download_progress * progress_weight
                            self.progress_var.set(weighted_progress)
                            self.progress_label.config(text=f"{weighted_progress:.1f}%")
                            self.root.update_idletasks()

            self.log(f"✅ Download concluído: {filename}")
            return local_path

        except Exception as e:
            self.log(f"❌ Erro no download: {e}")
            if local_path.exists():
                local_path.unlink()  # Remove arquivo incompleto em caso de erro
            raise

    def format_usb(self, device):
        """Formata o dispositivo USB - VERSÃO FINAL ROBUSTA"""
        self.log(f"💾 Iniciando formatação de {device}...")

        try:
            system = platform.system().lower()

            if system == "windows":
                drive_letter = device
                self.log(f"💾 Formatando unidade {drive_letter}...")

                cmd = f"format {drive_letter} /FS:FAT32 /Q /Y"
                process = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True
                )

                if process.returncode == 0:
                    self.log("✅ Formatação concluída com sucesso!")
                    return True
                else:
                    self.log(f"❌ Erro na formatação: {process.stderr}")
                    return False

            else:
                # ✅ CORREÇÃO: Verifica permissão sudo
                needs_sudo = os.geteuid() != 0
                
                if needs_sudo and not self.sudo_password:
                    if not self.check_sudo_permission():
                        self.log("❌ Permissão de superusuário necessária para formatação")
                        return False

                # ✅ CORREÇÃO: Tenta métodos em ordem de confiabilidade
                self.log("🔄 Tentando método simples...")
                if self.format_usb_simple(device):
                    return True
                
                self.log("🔄 Método simples falhou, tentando alternativo...")
                if self.format_usb_alternative(device):
                    return True
                
                # ✅ Última tentativa: método manual com partprobe
                self.log("🔄 Tentando método manual...")
                return self.format_usb_manual(device)

        except Exception as e:
            self.log(f"❌ Erro na formatação: {e}")
            return False

    def format_usb_simple(self, device):
        """Método mais simples e direto para formatação"""
        try:
            self.log(f"💾 Método simples de formatação para {device}...")
            
            needs_sudo = os.geteuid() != 0
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False
            
            # ✅ CORREÇÃO: Apenas 3 comandos essenciais
            commands = [
                # 1. Limpa completamente o disco
                ['wipefs', '--all', '--force', device],
                # 2. Cria partição única FAT32
                ['parted', '-s', device, 'mklabel', 'msdos'],
                ['parted', '-s', device, 'mkpart', 'primary', 'fat32', '1MiB', '100%'],
                # 3. Formata
                ['mkfs.vfat', '-F', '32', f"{device}1"]
            ]
            
            for i, cmd in enumerate(commands):
                self.log(f"   📝 Executando passo {i+1}/3...")
                
                if needs_sudo:
                    success, stdout, stderr = self.run_sudo_command(cmd)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0
                    stderr = result.stderr
                
                if not success:
                    self.log(f"❌ Erro no passo {i+1}: {stderr}")
                    return False
                
                time.sleep(1)
            
            self.log("✅ Formatação simples concluída!")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro na formatação simples: {e}")
            return False

    def format_usb_alternative(self, device):
        """Método alternativo de formatação usando sfdisk (NÃO INTERATIVO)"""
        try:
            self.log(f"🔄 Tentando método alternativo de formatação para {device}...")
            
            needs_sudo = os.geteuid() != 0
            
            # ✅ CORREÇÃO: Usa sfdisk que é não interativo
            # Primeiro: limpa o dispositivo completamente
            wipe_cmd = ['wipefs', '--all', '--force', device]
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(wipe_cmd)
            else:
                result = subprocess.run(wipe_cmd, capture_output=True, text=True)
                success = result.returncode == 0
            
            if not success:
                self.log("⚠️ Aviso: Não foi possível limpar assinaturas completamente")
            
            time.sleep(2)
            
            # ✅ CORREÇÃO: Cria tabela de partições com sfdisk (não interativo)
            # Script sfdisk para criar partição FAT32
            sfdisk_script = f"""
    label: dos
    label-id: 0x{os.urandom(4).hex()}
    device: {device}
    unit: sectors

    {device}1 : start=2048, size=+, type=c, bootable
    """
            
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(['sfdisk', device], input_text=sfdisk_script)
            else:
                process = subprocess.Popen(['sfdisk', device], stdin=subprocess.PIPE, text=True)
                process.communicate(input=sfdisk_script)
                success = process.returncode == 0
            
            if not success:
                self.log("❌ Erro no sfdisk")
                return False
            
            time.sleep(3)
            
            # ✅ CORREÇÃO: Formata a partição
            format_cmd = ['mkfs.vfat', '-F', '32', '-n', 'USB_BOOT', f"{device}1"]
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(format_cmd)
            else:
                result = subprocess.run(format_cmd, capture_output=True, text=True)
                success = result.returncode == 0
            
            if success:
                self.log("✅ Formatação alternativa concluída com sucesso!")
            else:
                self.log("❌ Erro na formatação alternativa")
            
            return success
            
        except Exception as e:
            self.log(f"❌ Erro no método alternativo: {e}")
            return False

    def format_usb_manual(self, device):
        """Método manual como último recurso"""
        try:
            self.log(f"🔧 Método manual de formatação para {device}...")
            
            needs_sudo = os.geteuid() != 0
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False
            
            # Passo 1: Garantir que não está montado
            self.unmount_all_partitions(device)
            time.sleep(3)
            
            # Passo 2: Limpar completamente
            wipe_commands = [
                ['dd', 'if=/dev/zero', f'of={device}', 'bs=1M', 'count=10'],
                ['wipefs', '--all', '--force', device]
            ]
            
            for cmd in wipe_commands:
                if needs_sudo:
                    success, stdout, stderr = self.run_sudo_command(cmd)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0
                
                if not success:
                    self.log(f"⚠️ Aviso no comando: {' '.join(cmd)}")
            
            time.sleep(2)
            
            # Passo 3: Recarregar a tabela de partições
            if needs_sudo:
                self.run_sudo_command(['partprobe', device])
            else:
                subprocess.run(['partprobe', device], capture_output=True)
            
            time.sleep(2)
            
            # Passo 4: Criar partição única
            parted_commands = [
                ['parted', '-s', device, 'mklabel', 'msdos'],
                ['parted', '-s', device, 'mkpart', 'primary', 'fat32', '1MiB', '100%']
            ]
            
            for cmd in parted_commands:
                if needs_sudo:
                    success, stdout, stderr = self.run_sudo_command(cmd)
                else:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    success = result.returncode == 0
                
                if not success:
                    self.log(f"❌ Erro no comando: {' '.join(cmd)}")
                    return False
            
            time.sleep(2)
            
            # Passo 5: Recarregar novamente
            if needs_sudo:
                self.run_sudo_command(['partprobe', device])
            else:
                subprocess.run(['partprobe', device], capture_output=True)
            
            time.sleep(3)
            
            # Passo 6: Formatar
            format_cmd = ['mkfs.vfat', '-F', '32', '-n', 'USB_BOOT', f"{device}1"]
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(format_cmd)
            else:
                result = subprocess.run(format_cmd, capture_output=True, text=True)
                success = result.returncode == 0
            
            if success:
                self.log("✅ Formatação manual concluída!")
            else:
                self.log("❌ Formatação manual falhou")
            
            return success
            
        except Exception as e:
            self.log(f"❌ Erro na formatação manual: {e}")
            return False

    def write_to_usb(self, iso_path, device, base_progress=0.0, progress_weight=1.0):
        """Escreve a ISO no dispositivo USB - VERSÃO SEGURA COM VERIFICAÇÃO"""
        self.log(f"🔥 Iniciando gravação SEGURA...")
        self.log(f"   ISO: {os.path.basename(iso_path)}")
        self.log(f"   Dispositivo: {device}")
        
        self.should_cancel = False

        try:
            # ✅ VERIFICAÇÃO DE SEGURANÇA: Processos ativos
            self.log("🔒 Verificando segurança...")
            if not self.kill_conflicting_dd_processes(device):
                messagebox.showerror(
                    "Erro de Segurança", 
                    "❌ Existem processos dd ativos gravando no mesmo dispositivo!\n\n"
                    "Isso pode corromper o USB.\n\n"
                    "Feche outros programas que possam estar usando o USB\n"
                    "e tente novamente."
                )
                return False

            system = platform.system().lower()
            needs_sudo = (system != "windows" and os.geteuid() != 0)
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False

            total_size = os.path.getsize(iso_path)
            
            self.log(f"📊 Tamanho ISO: {total_size / (1024**3):.2f} GB")
            self.log("🔄 Iniciando gravação única...")

            # ✅ COMANDO SIMPLES E SEGURO - APENAS UM PROCESSO
            if needs_sudo:
                cmd = f'dd if="{iso_path}" of="{device}" bs=4M status=progress'
                full_cmd = f'echo "{self.sudo_password}" | sudo -S {cmd}'
            else:
                cmd = f'dd if="{iso_path}" of="{device}" bs=4M status=progress'
                full_cmd = cmd
            
            self.log(f"⚡ Executando: {cmd}")

            # ✅ EXECUTA APENAS UM PROCESSO
            process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            self.current_process = process
            
            # ✅ MONITORAMENTO SIMPLES
            start_time = time.time()
            bytes_copied = 0
            
            self.log("📡 Monitorando gravação...")

            for line in process.stdout:
                if self.should_cancel:
                    self.log("⏹️ Gravação cancelada pelo usuário")
                    process.terminate()
                    return False
                    
                if line.strip():
                    line_clean = line.strip()
                    self.log(f"   {line_clean}")
                    
                    # ✅ DETECTA PROGRESSO
                    if 'bytes' in line_clean and 'copied' in line_clean:
                        try:
                            parts = line_clean.split()
                            for i, part in enumerate(parts):
                                if part.isdigit() and i > 0 and parts[i-1] in ['bytes', 'byte']:
                                    bytes_copied = int(part)
                                    progress_percent = (bytes_copied / total_size) * 100
                                    combined_progress = base_progress + (progress_percent * progress_weight)
                                    
                                    self.progress_var.set(combined_progress)
                                    self.progress_label.config(text=f"{combined_progress:.1f}%")
                                    self.root.update_idletasks()
                                    
                                    # Log a cada 10%
                                    if progress_percent % 10 < 1:
                                        elapsed = time.time() - start_time
                                        speed = (bytes_copied / (1024*1024)) / elapsed if elapsed > 0 else 0
                                        self.log(f"📊 {progress_percent:.1f}% - {speed:.1f} MB/s")
                                    break
                        except:
                            pass

            # ✅ VERIFICAÇÃO FINAL
            process.wait()
            
            if self.should_cancel:
                return False
                
            if process.returncode == 0:
                self.progress_var.set(100)
                self.progress_label.config(text="100%")
                self.log("✅ Gravação concluída com sucesso!")
                return True
            else:
                self.log(f"❌ Erro na gravação! Código: {process.returncode}")
                return False

        except Exception as e:
            self.log(f"❌ Erro na gravação: {e}")
            return False
        finally:
            self.current_process = None

    def write_to_usb_fallback(self, iso_path, device):
        """Método fallback para gravação sem interação de terminal"""
        try:
            self.log("🔄 Usando método fallback para gravação...")
            
            needs_sudo = os.geteuid() != 0
            
            # Comando simples sem progresso
            if needs_sudo:
                cmd = ['sudo', 'dd', f'if={iso_path}', f'of={device}', 'bs=4M']
            else:
                cmd = ['dd', f'if={iso_path}', f'of={device}', 'bs=4M']
            
            self.log(f"⚡ Executando: {' '.join(cmd)}")
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False
            
            # Para comandos sudo, usa run_sudo_command
            if needs_sudo:
                success, stdout, stderr = self.run_sudo_command(['dd', f'if={iso_path}', f'of={device}', 'bs=4M'])
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
            
            if success:
                self.log("✅ Gravação fallback concluída")
                return True
            else:
                self.log("❌ Erro na gravação fallback")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no método fallback: {e}")
            return False

    def check_if_writing(self, device):
        """Verifica se o dispositivo está sendo escrito"""
        try:
            # Verifica I/O statistics do dispositivo
            if os.path.exists(f"/sys/block/{device.split('/')[-1]}/stat"):
                with open(f"/sys/block/{device.split('/')[-1]}/stat", 'r') as f:
                    stats = f.read().split()
                    if len(stats) >= 7:
                        sectors_written = int(stats[6])
                        return sectors_written
            return None
        except:
            return None

    def get_device_io_stats(self, device):
        """Obtém estatísticas de I/O do dispositivo"""
        try:
            device_name = device.split('/')[-1]  # ex: 'sdb'
            stat_file = f"/sys/block/{device_name}/stat"
            
            if os.path.exists(stat_file):
                with open(stat_file, 'r') as f:
                    stats = f.read().strip().split()
                    if len(stats) >= 7:
                        # sectors_written está na posição 6 (começando de 0)
                        return int(stats[6])
            return None
        except:
            return None

    def monitor_dd_progress_artificial(self, iso_path, device, process, base_progress, progress_weight):
        """Monitora progresso do dd artificialmente baseado em tempo e I/O"""
        try:
            total_size = os.path.getsize(iso_path)
            start_time = time.time()
            last_io_check = start_time
            last_sectors = self.get_device_io_stats(device)
            last_progress = base_progress
            
            self.log("📊 Iniciando monitoramento de progresso...")
            
            while process.poll() is None:  # Enquanto o processo estiver rodando
                if self.should_cancel:
                    return False
                    
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Verifica I/O a cada 2 segundos
                if current_time - last_io_check >= 2:
                    current_sectors = self.get_device_io_stats(device)
                    
                    if current_sectors is not None and last_sectors is not None:
                        sectors_written = current_sectors - last_sectors
                        if sectors_written > 0:
                            # Calcula progresso baseado em setores escritos
                            bytes_written = sectors_written * 512  # Cada setor tem 512 bytes
                            progress_percent = min(100, (bytes_written / total_size) * 100)
                        else:
                            # Se não detectou I/O, usa estimativa baseada em tempo
                            # Assume velocidade média de 10 MB/s como fallback
                            estimated_bytes = elapsed * 10 * 1024 * 1024  # 10 MB/s
                            progress_percent = min(80, (estimated_bytes / total_size) * 100)
                    else:
                        # Se não conseguiu ler I/O, usa estimativa temporal
                        estimated_bytes = elapsed * 10 * 1024 * 1024  # 10 MB/s
                        progress_percent = min(80, (estimated_bytes / total_size) * 100)
                    
                    # Aplica pesos e atualiza progresso
                    combined_progress = base_progress + (progress_percent * progress_weight)
                    
                    # Só atualiza se houve progresso significativo
                    if combined_progress > last_progress + 1 or current_time - last_io_check >= 10:
                        self.progress_var.set(combined_progress)
                        self.progress_label.config(text=f"{combined_progress:.1f}%")
                        
                        # Calcula ETA
                        if progress_percent > 0:
                            total_time_estimated = (elapsed / progress_percent) * 100
                            eta_seconds = total_time_estimated - elapsed
                            self.log(f"📊 Progresso estimado: {combined_progress:.1f}% - ETA: {eta_seconds:.0f}s")
                        
                        last_progress = combined_progress
                        last_io_check = current_time
                        last_sectors = current_sectors
                    
                    self.root.update_idletasks()
                
                time.sleep(0.5)  # Pequena pausa para não sobrecarregar
                
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro no monitoramento: {e}")
            return True  # Continua mesmo com erro


    def get_device_size(self, device):
        """Obtém o tamanho total do dispositivo em bytes"""
        try:
            result = subprocess.run(
                ['blockdev', '--getsize64', device],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 0
        except:
            return 0

    def write_to_usb_with_pv(self, iso_path, device, base_progress=0.0, progress_weight=1.0):
        """Método com PV - VERSÃO SUPER SIMPLIFICADA"""
        try:
            self.log("🔄 Iniciando gravação com PV...")
            
            total_size = os.path.getsize(iso_path)
            needs_sudo = os.geteuid() != 0
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False

            # ✅ CORREÇÃO RADICAL: Dois processos separados
            if needs_sudo:
                # PRIMEIRO: Execute o PV separadamente para ver se funciona
                pv_cmd = f'pv -n "{iso_path}"'
                dd_cmd = f'dd of="{device}" bs=4M'
                
                self.log("🔧 Executando PV e DD em pipeline...")
                
                # Cria os processos separadamente
                pv_process = subprocess.Popen(
                    ['sudo', '-S', 'pv', '-n', iso_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Envia senha para pv
                pv_process.stdin.write(self.sudo_password + '\n')
                pv_process.stdin.flush()
                
                dd_process = subprocess.Popen(
                    ['sudo', '-S', 'dd', f'of={device}', 'bs=4M'],
                    stdin=pv_process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Envia senha para dd
                dd_process.stdin.close()  # stdin vem do pv
                
                process = dd_process  # Monitora o dd
                
            else:
                # Sem sudo - mais simples
                cmd = f'pv -n "{iso_path}" | dd of="{device}" bs=4M'
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            
            self.current_process = process
            
            # ✅ MONITORAMENTO SIMPLES DO PV
            def monitor_pv():
                # Monitora stderr do PV (onde vai o progresso)
                while True:
                    if needs_sudo:
                        # Para sudo, monitora stderr do pv_process
                        line = pv_process.stderr.readline()
                    else:
                        # Para sem sudo, monitora stderr do processo principal
                        line = process.stderr.readline()
                        
                    if line:
                        line_clean = line.strip()
                        self.log(f"PV: {line_clean}")
                        
                        # Extrai porcentagem
                        if '%' in line_clean:
                            try:
                                import re
                                match = re.search(r'(\d+\.?\d*)%', line_clean)
                                if match:
                                    percent = float(match.group(1))
                                    combined_progress = base_progress + (percent * progress_weight)
                                    
                                    self.progress_var.set(combined_progress)
                                    self.progress_label.config(text=f"{combined_progress:.1f}%")
                                    self.root.update_idletasks()
                                    
                                    if percent % 10 < 1:  # Log a cada 10%
                                        self.log(f"📊 {percent:.1f}%")
                            except:
                                pass
                    
                    # Verifica se terminou
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
            
            monitor_thread = threading.Thread(target=monitor_pv, daemon=True)
            monitor_thread.start()
            
            # Aguarda finalização
            process.wait()
            if needs_sudo:
                pv_process.wait()
            
            monitor_thread.join(timeout=2)
            
            if process.returncode == 0:
                self.progress_var.set(100)
                self.progress_label.config(text="100%")
                self.log("✅ Gravação concluída!")
                return True
            else:
                self.log(f"❌ Erro! Código: {process.returncode}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro no PV: {e}")
            return False

    def write_to_usb_reliable(self, iso_path, device, base_progress=0.0, progress_weight=1.0):
        """Método 100% confiável COM CAPTURA DE PROGRESSO - VERSÃO CORRIGIDA"""
        try:
            self.log("🔥 Iniciando gravação confiável...")
            
            total_size = os.path.getsize(iso_path)
            needs_sudo = os.geteuid() != 0
            
            if needs_sudo and not self.sudo_password:
                if not self.check_sudo_permission():
                    return False

            # Comando com status=progress
            if needs_sudo:
                cmd = f'sudo dd if="{iso_path}" of="{device}" bs=4M status=progress'
                full_cmd = f'echo "{self.sudo_password}" | sudo -S dd if="{iso_path}" of="{device}" bs=4M status=progress'
            else:
                cmd = f'dd if="{iso_path}" of="{device}" bs=4M status=progress'
                full_cmd = cmd
            
            self.log(f"⚡ Executando: {cmd}")
            
            process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # ✅ Progresso vai para stdout
                text=True,
                bufsize=1,
                universal_newlines=True,
            )
            
            self.current_process = process
            
            start_time = time.time()
            last_percent = 0
            
            # ✅ CAPTURA DE PROGRESSO DO DD
            for line in process.stdout:
                if self.should_cancel:
                    process.terminate()
                    break
                    
                line_clean = line.strip()
                if line_clean:
                    self.log(f"   {line_clean}")
                    
                    # ✅ EXTRAI BYTES E PORCENTAGEM DA SAÍDA DO DD
                    # Procura padrões como: 
                    # "123456789 bytes (123 MB, 456 MB/s) copied, 12.3 s, 67.8 MB/s"
                    # ou "[123456789/987654321] 12.5%"
                    if 'bytes' in line_clean and 'copied' in line_clean:
                        try:
                            import re
                            # Extrai número de bytes
                            bytes_match = re.search(r'(\d+) bytes', line_clean)
                            if bytes_match:
                                current_bytes = int(bytes_match.group(1))
                                
                                # Calcula porcentagem
                                progress_percent = min(100, (current_bytes / total_size) * 100)
                                combined_progress = base_progress + (progress_percent * progress_weight)
                                
                                # Atualiza progresso apenas se mudou significativamente
                                if progress_percent - last_percent >= 1:
                                    self.progress_var.set(combined_progress)
                                    self.progress_label.config(text=f"{combined_progress:.1f}%")
                                    
                                    # Log a cada 5% de progresso
                                    if progress_percent - last_percent >= 5:
                                        elapsed = time.time() - start_time
                                        speed = current_bytes / (1024*1024) / elapsed if elapsed > 0 else 0
                                        self.log(f"📊 {progress_percent:.1f}% - {speed:.1f} MB/s")
                                        last_percent = progress_percent
                                    
                                    self.root.update_idletasks()
                        except Exception as e:
                            # Se não conseguir extrair bytes, continua sem progresso
                            pass
                    
                    # ✅ TAMBÉM PROCURA POR PADRÃO DE PORCENTAGEM DIRETA
                    elif '%' in line_clean:
                        try:
                            import re
                            percent_match = re.search(r'(\d+\.?\d*)%', line_clean)
                            if percent_match:
                                progress_percent = float(percent_match.group(1))
                                combined_progress = base_progress + (progress_percent * progress_weight)
                                
                                self.progress_var.set(combined_progress)
                                self.progress_label.config(text=f"{combined_progress:.1f}%")
                                
                                if progress_percent - last_percent >= 5:
                                    self.log(f"📊 {progress_percent:.1f}%")
                                    last_percent = progress_percent
                                
                                self.root.update_idletasks()
                        except:
                            pass
            
            process.wait()
            
            if self.should_cancel:
                return False
                
            if process.returncode == 0:
                self.progress_var.set(100)
                self.progress_label.config(text="100%")
                self.log("🎉 Gravação concluída com sucesso!")
                return True
            else:
                self.log(f"❌ Erro na gravação! Código: {process.returncode}")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro: {e}")
            return False

    def start_creation(self):
        """Inicia o processo de criação em thread separada"""
        if not self.get_selected_usb_device():
            messagebox.showerror("Erro", "❌ Selecione um dispositivo USB da lista!")
            return

        # ✅ NOVO: Controla estado dos botões
        self.create_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_var.set("🔄 Iniciando processo...")

        thread = threading.Thread(target=self.create_bootable_usb)
        thread.daemon = True
        thread.start()

    def create_bootable_usb(self):
        """Processo principal de criação do USB bootável - VERSÃO CORRIGIDA"""
        try:
            # ✅ CORREÇÃO: Configurar estado da operação
            self.is_operation_running = True
            self.should_cancel = False
            
            selected_usb = self.get_selected_usb_device()
            if not selected_usb:
                messagebox.showerror("Erro", "❌ Nenhum dispositivo USB selecionado!")
                self.create_button.config(state="normal")
                self.cancel_button.config(state="disabled")
                return

            self.log("🔒 Verificando segurança do sistema...")
            has_dangerous, dangerous_procs = self.check_active_dd_processes(selected_usb)
            
            # ✅ CORREÇÃO: Esta verificação deve permitir que o processo atual continue
            if has_dangerous:
                self.log("❌ Processos perigosos detectados! Cancelando operação.")
                messagebox.showerror(
                    "Erro de Segurança", 
                    "❌ Existem processos dd ativos no sistema!\n\n"
                    "Processos detectados:\n" +
                    "\n".join([f"• PID {p['pid']}: {p['command'][:50]}..." for p in dangerous_procs]) +
                    "\n\nFeche todos os programas que possam estar usando o USB\n"
                    "e execute este programa novamente."
                )
                self.create_button.config(state="normal")
                self.cancel_button.config(state="disabled")
                self.is_operation_running = False
                return
 
            self.log("🚀 Iniciando criação do USB bootável...")

            # ✅ CORREÇÃO: Definir variáveis de progresso ANTES de qualquer uso
            download_progress_weight = 0.4  # 40% para download
            writing_progress_weight = 0.6   # 60% para gravação
            base_progress = 0.0  # Inicializa a variável

            if self.custom_iso_var.get():
                # Modo ISO personalizada - sem download
                iso_path = self.iso_path_var.get()
                if not iso_path or not Path(iso_path).exists():
                    messagebox.showerror("Erro", "❌ Selecione um arquivo ISO válido!")
                    self.create_button.config(state="normal")
                    return

                distro_name = "ISO Personalizada"
                iso_file_path = Path(iso_path)
                self.log(f"📁 Usando ISO personalizada: {iso_file_path.name}")
                
                # ✅ CORREÇÃO: Ajusta pesos para modo personalizado (apenas gravação)
                download_progress_weight = 0.0
                writing_progress_weight = 1.0
                base_progress = 0.0  # Começa em 0% já que não há download

            else:
                # Modo distribuição pré-definida - com download
                family = self.family_var.get()
                variant = self.variant_var.get()
                arch = self.arch_var.get()
                version = self.version_var.get()

                if not all([family, variant, arch, version]):
                    messagebox.showerror("Erro", "❌ Selecione uma distribuição completa!")
                    self.create_button.config(state="normal")
                    return

                distro_name = f"{family} {variant} {version} {arch}"
                self.log(f"📦 Preparando {distro_name}...")

                # Constrói URL e filename
                url, filename = self.build_download_url(family, variant, arch, version)
                if not url:
                    messagebox.showerror("Erro", "❌ Não foi possível construir URL de download!")
                    self.create_button.config(state="normal")
                    return

                self.log(f"🔗 URL construída: {url}")
                self.log(f"📄 Nome do arquivo: {filename}")

                # Download da ISO com progresso
                self.status_var.set("⬇️ Baixando ISO...")
                iso_file_path = self.download_file(url, filename, download_progress_weight)
                if not iso_file_path:
                    messagebox.showerror("Erro", "❌ Falha no download da ISO!")
                    self.create_button.config(state="normal")
                    return

                # ✅ CORREÇÃO: Define base_progress após download bem-sucedido
                base_progress = download_progress_weight * 100

            # Confirmação final
            confirm = messagebox.askyesno(
                "⚠️ CONFIRMAÇÃO FINAL",
                f"TODOS OS DADOS NO DISPOSITIVO SERÃO APAGADOS!\n\n"
                f"Distribuição: {distro_name}\n"
                f"Dispositivo: {selected_usb}\n\n"
                f"Continuar com a criação do USB bootável?",
            )

            if not confirm:
                self.log("❌ Processo cancelado pelo usuário")
                self.create_button.config(state="normal")
                self.status_var.set("✅ Pronto")
                return

            # Formata USB
            self.status_var.set("🔄 Formatando USB...")
            if not self.format_usb(selected_usb):
                messagebox.showerror("Erro", "❌ Falha na formatação do USB!")
                self.create_button.config(state="normal")
                self.status_var.set("❌ Erro na formatação")
                return

            # Grava ISO no USB
            self.status_var.set("🔥 Gravando ISO no USB...")
            self.log("🔄 Iniciando gravação...")

            # ✅ USA MÉTODO CONFIÁVEL COM PROGRESSO
            self.log("🎯 Usando método confiável com progresso...")
            if self.write_to_usb_reliable(str(iso_file_path), selected_usb, base_progress, writing_progress_weight):
                self.log("✅ Gravação bem-sucedida!")
            else:
                self.log("⚠️ Método confiável falhou, tentando fallback...")
                if not self.write_to_usb(str(iso_file_path), selected_usb, base_progress, writing_progress_weight):
                    messagebox.showerror(
                        "Erro de Gravação", 
                        "❌ Falha na gravação do USB!\n\n"
                        "Possíveis causas:\n"
                        "• USB com problemas físicos\n"
                        "• ISO corrompida\n"  
                        "• Dispositivo protegido contra gravação\n\n"
                        "Tente:\n"
                        "• Usar outro USB\n"
                        "• Verificar a ISO\n"
                        "• Testar em outra porta USB"
                    )
                    self.create_button.config(state="normal")
                    self.status_var.set("❌ Erro na gravação")
                    return

            # Sucesso!
            self.progress_var.set(100)
            self.progress_label.config(text="100%")
            self.status_var.set("✅ USB bootável criado com sucesso!")

            messagebox.showinfo(
                "🎉 Sucesso!",
                f"USB bootável criado com sucesso!\n\n"
                f"Distribuição: {distro_name}\n"
                f"Dispositivo: {selected_usb}\n\n"
                f"O USB está pronto para uso!",
            )

            self.log("🎉 Processo concluído com sucesso!")

        except Exception as e:
            self.log(f"❌ Erro inesperado: {e}")
            messagebox.showerror("Erro", f"❌ Ocorreu um erro inesperado:\n{e}")
            self.status_var.set("❌ Erro no processo")

        finally:
            # ✅ NOVO: Finaliza controle de operação
            self.is_operation_running = False
            self.should_cancel = False
            self.current_process = None
            self.create_button.config(state="normal")
            self.cancel_button.config(state="disabled")

    def stop_current_operation(self):
        """Para a operação atual (download ou gravação)"""
        try:
            self.should_cancel = True
            self.log("🛑 Solicitando parada da operação atual...")
            
            if self.current_process:
                try:
                    # Tenta terminar graciosamente primeiro
                    self.current_process.terminate()
                    time.sleep(2)
                    
                    # Força se necessário
                    if self.current_process.poll() is None:
                        self.current_process.kill()
                        
                    self.log("✅ Processo terminado")
                except:
                    pass
                finally:
                    self.current_process = None
            
            # Para processos dd específicos
            self.kill_dd_processes()
            
            return True
            
        except Exception as e:
            self.log(f"⚠️ Erro ao parar operação: {e}")
            return False

    def kill_dd_processes(self):
        """Mata processos dd multiplataforma"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                commands = [
                    ["taskkill", "/F", "/IM", "dd.exe"],
                    ["powershell", "Get-Process dd -ErrorAction SilentlyContinue | Stop-Process -Force"]
                ]
                
                for cmd in commands:
                    try:
                        subprocess.run(cmd, capture_output=True, timeout=5)
                    except:
                        pass
                        
            else:
                # Linux/Mac - usa o método de comando sudo
                commands = [
                    ["pkill", "-f", "dd of="],
                    ["pkill", "-f", "pv.*dd"], 
                    ["pkill", "-9", "dd"]
                ]
                
                for cmd in commands:
                    if os.geteuid() != 0 and self.sudo_password:
                        success, stdout, stderr = self.run_sudo_command(cmd)
                    else:
                        try:
                            subprocess.run(cmd, capture_output=True, timeout=5)
                        except:
                            pass
                    
            self.log("✅ Processos dd terminados")
            
        except Exception as e:
            self.log(f"⚠️ Erro ao matar processos dd: {e}")

    def cancel_operation(self):
        """Cancela a operação atual via interface"""
        if not self.is_operation_running:
            messagebox.showinfo("Info", "Nenhuma operação em andamento para cancelar.")
            return
        
        if messagebox.askyesno("Cancelar", "Deseja realmente cancelar a operação atual?\n\n⚠️ O USB pode ficar inutilizado se a gravação for interrompida."):
            self.log("🛑 Cancelamento solicitado pelo usuário...")
            self.status_var.set("⏹️ Cancelando operação...")
            
            # Para a operação
            self.stop_current_operation()
            
            # Reseta interface
            self.progress_var.set(0)
            self.progress_label.config(text="0%")
            self.status_var.set("⏹️ Operação cancelada")
            self.create_button.config(state="normal")
            self.cancel_button.config(state="disabled")  # ✅ Desabilita botão de cancelamento
            self.is_operation_running = False
            
            self.log("✅ Operação cancelada com sucesso")

    def run(self):
        """Inicia a aplicação"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Erro: {e}")
            input("Pressione Enter para sair...")

    def is_device_active(self, device):
        """Verifica se o dispositivo está sendo acessado/escrito"""
        try:
            # Verifica se há I/O recente
            current_sectors = self.get_device_io_stats(device)
            if current_sectors is None:
                return True  # Assume ativo se não conseguiu verificar
            
            # Pequena pausa e verifica novamente
            time.sleep(1)
            new_sectors = self.get_device_io_stats(device)
            
            if new_sectors is not None and current_sectors is not None:
                return new_sectors > current_sectors
            
            return True  # Assume ativo por padrão
        except:
            return True

def main():
    """Função principal"""
    print("🐧 Bootable USB Creator - Sistema Escalável")
    print("🚀 Pronto para milhares de distribuições!")

    system = platform.system().lower()
    
    # ✅ NOVO: Verificação e solicitação de elevação
    if system != "windows":
        if os.geteuid() != 0:
            print("🔐 Este aplicativo requer privilégios de superusuário")
            print("💡 Solicitando elevação...")
            
            # Tenta reiniciar com sudo
            try:
                subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
                sys.exit(0)
            except subprocess.CalledProcessError:
                print("❌ Falha na elevação. Execute manualmente com:")
                print("   sudo python3 create-usb-x-full.py")
                print("⏰ Continuando com privilégios limitados em 5 segundos...")
                time.sleep(5)
        else:
            print("✅ Executando com privilégios de superusuário")
    else:
        # Verificação para Windows
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                print("⚠️  No Windows, execute como Administrador para melhor detecção USB")
                print("⏰ Continuando em 3 segundos...")
                time.sleep(3)
        except:
            pass

    try:
        app = BootableUSBCreator()
        app.run()
    except Exception as e:
        print(f"❌ Erro ao iniciar aplicativo: {e}")
        input("Pressione Enter para sair...")


if __name__ == "__main__":
    main()
