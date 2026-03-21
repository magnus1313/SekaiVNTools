# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import json
import os
import base64
import shutil

class HgoToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HGO Tool - Extrator e Injetor (com filtro) - Por SekaiVN")
        self.root.geometry("720x680")
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Variáveis de Controle
        self.var_filtrar_ingles = tk.BooleanVar(value=True)  # Padrão: Ativado
        
        # === Layout Principal ===
        
        # Notebook (Abas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill='both')
        
        # Criar Abas
        self.tab_arquivo = ttk.Frame(self.notebook)
        self.tab_pasta = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_arquivo, text='Modo Arquivo Unico')
        self.notebook.add(self.tab_pasta, text='Modo Pasta (Lote)')
        
        # Configurar Abas
        self.setup_tab_arquivo()
        self.setup_tab_pasta()
        
        # Área de Log (Console)
        lbl_log = ttk.Label(root, text="Log de Execucao:", font=('Arial', 10, 'bold'))
        lbl_log.pack(anchor='w', padx=10)
        
        self.txt_log = scrolledtext.ScrolledText(root, height=12, state='disabled')
        self.txt_log.pack(padx=10, pady=(0, 10), fill='x')

    def log(self, mensagem):
        """Escreve na área de log da GUI"""
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, mensagem + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')
        self.root.update_idletasks()

    # ================= LAYOUT =================

    def setup_tab_arquivo(self):
        frame = ttk.Frame(self.tab_arquivo, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Arquivo HGO
        ttk.Label(frame, text="Arquivo HGO Original:").grid(row=0, column=0, sticky='w')
        self.ent_hgo_file = ttk.Entry(frame, width=55)
        self.ent_hgo_file.grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Procurar...", command=self.browse_hgo).grid(row=1, column=1, padx=5)
        
        # Arquivo JSON
        ttk.Label(frame, text="Arquivo JSON (Saida/Traducao):").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.ent_json_file = ttk.Entry(frame, width=55)
        self.ent_json_file.grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Procurar...", command=self.browse_json).grid(row=3, column=1, padx=5)
        
        # Opções
        frm_opts = ttk.LabelFrame(frame, text="Opcoes de Extracao", padding=10)
        frm_opts.grid(row=4, column=0, columnspan=2, sticky='ew', pady=15)
        
        chk_filtro = ttk.Checkbutton(frm_opts, text="Filtrar apenas textos uteis (Dialogos/Ingles)", variable=self.var_filtrar_ingles)
        chk_filtro.pack(anchor='w')
        ttk.Label(frm_opts, text="* Se desmarcado, extrai TUDO (nomes de arquivos, codigos, lixo).", font=("Arial", 8)).pack(anchor='w', padx=20)
        
        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="(v) EXTRAIR Texto", command=self.acao_extrair_arquivo).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="(^) INJETAR Traducao", command=self.acao_injetar_arquivo).pack(side='left', padx=10)

    def setup_tab_pasta(self):
        frame = ttk.Frame(self.tab_pasta, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Pasta HGO
        ttk.Label(frame, text="Pasta com arquivos HGO:").grid(row=0, column=0, sticky='w')
        self.ent_folder_hgo = ttk.Entry(frame, width=55)
        self.ent_folder_hgo.grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Procurar Pasta...", command=lambda: self.browse_folder(self.ent_folder_hgo)).grid(row=1, column=1, padx=5)
        
        # Pasta JSON
        ttk.Label(frame, text="Pasta com arquivos JSON:").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.ent_folder_json = ttk.Entry(frame, width=55)
        self.ent_folder_json.grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Procurar Pasta...", command=lambda: self.browse_folder(self.ent_folder_json)).grid(row=3, column=1, padx=5)

        # Opções (Compartilha a variável da outra aba)
        frm_opts = ttk.LabelFrame(frame, text="Opcoes de Extracao em Lote", padding=10)
        frm_opts.grid(row=4, column=0, columnspan=2, sticky='ew', pady=15)
        
        chk_filtro = ttk.Checkbutton(frm_opts, text="Filtrar apenas textos uteis (Dialogos/Ingles)", variable=self.var_filtrar_ingles)
        chk_filtro.pack(anchor='w')
        ttk.Label(frm_opts, text="* Se desmarcado, extrai TUDO (nomes de arquivos, codigos, lixo).", font=("Arial", 8)).pack(anchor='w', padx=20)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="(v) EXTRAIR Pasta", command=self.acao_extrair_pasta).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="(^) INJETAR Pasta", command=self.acao_injetar_pasta).pack(side='left', padx=10)

    # ================= AUXILIARES GUI =================

    def browse_hgo(self):
        f = filedialog.askopenfilename(filetypes=[("Arquivos HGO", "*.hgo"), ("Todos", "*.*")])
        if f:
            self.ent_hgo_file.delete(0, tk.END)
            self.ent_hgo_file.insert(0, f)
            json_path = f + ".json"
            self.ent_json_file.delete(0, tk.END)
            self.ent_json_file.insert(0, json_path)

    def browse_json(self):
        f = filedialog.askopenfilename(filetypes=[("Arquivos JSON", "*.json"), ("Todos", "*.*")])
        if f:
            self.ent_json_file.delete(0, tk.END)
            self.ent_json_file.insert(0, f)

    def browse_folder(self, entry_widget):
        d = filedialog.askdirectory()
        if d:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, d)

    # ================= LÓGICA DO SCRIPT (Adaptada) =================

    def looks_like_english_text(self, s: str) -> bool:
        """Heuristica para detectar se a string parece texto real."""
        if len(s) < 3: return False # Reduzi um pouco para pegar menus curtos
        if s.startswith(('$', '@', '#')): return False
        if re.match(r'^(BGM|SE|BG|V|EV|IMG|SC|SYS)[0-9_\.A-Za-z]*$', s): return False
        if re.search(r'\.(wav|ogg|bmp|png|jpg|psd|mp3|exe|bat|dll|txt)$', s, re.I): return False
        if re.match(r'^[A-Z0-9_\-]+$', s): return False # Só maiusculas e numeros geralmente é ID
        if not re.search(r'[a-z]', s): return False # Precisa ter minusculas
        if not re.search(r'[A-Z]', s) and len(s.split()) <= 2: return False
        return True

    def extract_logic(self, file_path):
        """Lógica central de extração"""
        with open(file_path, 'rb') as f:
            data = f.read()
        
        min_len = 4
        english_only = self.var_filtrar_ingles.get()
        
        pattern = re.compile(rb'[\x20-\x7e]{%d,}' % min_len)
        results = []
        
        for m in pattern.finditer(data):
            off = m.start()
            b = m.group(0)
            try:
                text = b.decode('utf-8')
            except Exception:
                text = b.decode('latin1', errors='replace')
            
            if english_only and not self.looks_like_english_text(text.strip()):
                continue
                
            results.append({
                'offset': off,
                'length': len(b),
                'text': text,
                'original': text # Mantido para referência
            })
        return results

    def inject_logic(self, hgo_path, json_path, out_path):
        """Lógica central de injeção"""
        with open(hgo_path, 'rb') as f:
            data = bytearray(f.read())
            
        with open(json_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)
            
        injections = 0
        warnings = 0
        
        for item in entries:
            off = int(item.get('offset'))
            orig_len = int(item.get('length'))
            
            # Suporta campo 'traducao' ou 'translated'
            traducao = item.get('traducao', item.get('text'))
            
            if traducao is None: continue
            
            # Tentar codificar
            try:
                encoded = traducao.encode('utf-8')
            except:
                encoded = traducao.encode('latin1', errors='replace')
                
            if len(encoded) <= orig_len:
                # Preencher com NULL (0x00) se for menor
                data[off:off+orig_len] = encoded.ljust(orig_len, b'\x00')
                injections += 1
            else:
                # Truncar se for maior (seguranca)
                data[off:off+orig_len] = encoded[:orig_len]
                injections += 1
                warnings += 1
                
        with open(out_path, 'wb') as f:
            f.write(data)
            
        return injections, warnings

    # ================= AÇÕES DOS BOTÕES =================

    def acao_extrair_arquivo(self):
        hgo = self.ent_hgo_file.get()
        jsn = self.ent_json_file.get()
        
        if not os.path.exists(hgo):
            messagebox.showerror("Erro", "Arquivo HGO nao encontrado.")
            return
            
        self.log(f"--- Extraindo: {os.path.basename(hgo)} ---")
        try:
            dados = self.extract_logic(hgo)
            
            with open(jsn, 'w', encoding='utf-8') as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
                
            self.log(f"Sucesso! {len(dados)} textos extraidos.")
            self.log(f"Salvo em: {jsn}")
            messagebox.showinfo("Sucesso", "Extracao concluida!")
            
        except Exception as e:
            self.log(f"ERRO: {e}")
            messagebox.showerror("Erro", str(e))

    def acao_injetar_arquivo(self):
        hgo = self.ent_hgo_file.get()
        jsn = self.ent_json_file.get()
        
        if not os.path.exists(hgo) or not os.path.exists(jsn):
            messagebox.showerror("Erro", "Arquivos de entrada nao encontrados.")
            return
            
        out = hgo.replace('.hgo', '_mod.hgo')
        self.log(f"--- Injetando: {os.path.basename(hgo)} ---")
        
        try:
            inj, warn = self.inject_logic(hgo, jsn, out)
            self.log(f"Injetados: {inj} | Truncados/Alertas: {warn}")
            self.log(f"Arquivo salvo: {out}")
            messagebox.showinfo("Sucesso", f"Arquivo criado:\n{out}")
        except Exception as e:
            self.log(f"ERRO: {e}")
            messagebox.showerror("Erro", str(e))

    def acao_extrair_pasta(self):
        dir_hgo = self.ent_folder_hgo.get()
        dir_json = self.ent_folder_json.get()
        
        if not os.path.exists(dir_hgo):
            messagebox.showerror("Erro", "Pasta HGO invalida.")
            return
        if not dir_json:
            dir_json = os.path.join(dir_hgo, "json_extracted")
            
        if not os.path.exists(dir_json):
            os.makedirs(dir_json)
            
        self.log(f"--- Processando pasta HGO... ---")
        arquivos = [f for f in os.listdir(dir_hgo) if f.lower().endswith('.hgo')]
        
        if not arquivos:
            self.log("Nenhum arquivo .hgo encontrado.")
            return
            
        sucessos = 0
        for arq in arquivos:
            caminho_hgo = os.path.join(dir_hgo, arq)
            caminho_json = os.path.join(dir_json, arq + ".json")
            
            try:
                dados = self.extract_logic(caminho_hgo)
                if dados:
                    with open(caminho_json, 'w', encoding='utf-8') as f:
                        json.dump(dados, f, ensure_ascii=False, indent=2)
                    self.log(f"OK: {arq} ({len(dados)} linhas)")
                    sucessos += 1
                else:
                    self.log(f"PULADO: {arq} (Sem texto util)")
            except Exception as e:
                self.log(f"FALHA {arq}: {e}")
                
        messagebox.showinfo("Fim", f"Processamento concluido.\n{sucessos} arquivos extraidos.")

    def acao_injetar_pasta(self):
        dir_hgo = self.ent_folder_hgo.get()
        dir_json = self.ent_folder_json.get()
        
        if not os.path.exists(dir_hgo) or not os.path.exists(dir_json):
            messagebox.showerror("Erro", "Pastas invalidas.")
            return
            
        dir_saida = os.path.join(dir_hgo, "HGO_Traduzidos")
        if not os.path.exists(dir_saida):
            os.makedirs(dir_saida)
            
        self.log(f"--- Injetando em Lote... ---")
        arquivos_json = [f for f in os.listdir(dir_json) if f.lower().endswith('.json')]
        
        sucessos = 0
        for arq_json in arquivos_json:
            # Tenta descobrir o nome do HGO original
            # Assume que o json é nome_arquivo.hgo.json ou apenas nome.json
            nome_hgo = arq_json.replace('.json', '')
            if not nome_hgo.lower().endswith('.hgo'):
                # Se o json não tinha .hgo no nome, tenta achar arquivo correspondente
                if os.path.exists(os.path.join(dir_hgo, nome_hgo + '.hgo')):
                    nome_hgo += '.hgo'
            
            caminho_hgo_orig = os.path.join(dir_hgo, nome_hgo)
            caminho_json_full = os.path.join(dir_json, arq_json)
            caminho_saida = os.path.join(dir_saida, nome_hgo)
            
            if not os.path.exists(caminho_hgo_orig):
                self.log(f"IGNORADO: {arq_json} (Original {nome_hgo} nao achado)")
                continue
                
            try:
                inj, warn = self.inject_logic(caminho_hgo_orig, caminho_json_full, caminho_saida)
                self.log(f"OK: {nome_hgo} (Inj: {inj})")
                sucessos += 1
            except Exception as e:
                self.log(f"ERRO {nome_hgo}: {e}")
                
        messagebox.showinfo("Fim", f"Injecao concluida.\n{sucessos} arquivos criados em 'HGO_Traduzidos'.")

if __name__ == "__main__":
    # Suporte a Splash Screen do PyInstaller
    try:
        import pyi_splash
        pyi_splash.update_text('Carregando HGO Tool...')
        pyi_splash.close()
    except ImportError:
        pass

    root = tk.Tk()
    app = HgoToolGUI(root)
    root.mainloop()