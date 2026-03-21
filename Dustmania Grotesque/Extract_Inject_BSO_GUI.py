# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import json
import os

class BsoToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BSO Tool - Extrator e Injetor")
        self.root.geometry("700x700")  # Aumentei um pouco a altura
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Vari?vel de Encoding (Compartilhada entre as abas)
        self.encoding_var = tk.StringVar(value="utf-8")
        
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
        
        # ?rea de Log (Console)
        lbl_log = ttk.Label(root, text="Log de Execucao:", font=('Arial', 10, 'bold'))
        lbl_log.pack(anchor='w', padx=10)
        
        self.txt_log = scrolledtext.ScrolledText(root, height=10, state='disabled')
        self.txt_log.pack(padx=10, pady=(0, 10), fill='x')

    def log(self, mensagem):
        """Escreve na ?rea de log da GUI"""
        self.txt_log.config(state='normal')
        self.txt_log.insert(tk.END, mensagem + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state='disabled')
        self.root.update_idletasks()

    def setup_tab_arquivo(self):
        frame = ttk.Frame(self.tab_arquivo, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Sele??o de Arquivo BSO
        ttk.Label(frame, text="Arquivo BSO Original:").grid(row=0, column=0, sticky='w')
        self.ent_bso_file = ttk.Entry(frame, width=50)
        self.ent_bso_file.grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Procurar...", command=self.browse_bso).grid(row=1, column=1, padx=5)
        
        # Sele??o de Arquivo JSON
        ttk.Label(frame, text="Arquivo JSON (Traducao/Saida):").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.ent_json_file = ttk.Entry(frame, width=50)
        self.ent_json_file.grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Procurar...", command=self.browse_json).grid(row=3, column=1, padx=5)
        
        # Op??es de Encoding
        lbl_enc = ttk.Label(frame, text="Encoding de Saida (para Injecao):")
        lbl_enc.grid(row=4, column=0, sticky='w', pady=(15, 0))
        
        opcoes_encoding = ['utf-8', 'shift-jis', 'cp932', 'latin-1', 'cp1252']
        cb_encoding = ttk.Combobox(frame, values=opcoes_encoding, textvariable=self.encoding_var, state="readonly")
        cb_encoding.grid(row=5, column=0, sticky='w', pady=5)
        
        # Bot?es de A??o
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Removi as setas Unicode e usei texto simples para evitar erros de caractere
        ttk.Button(btn_frame, text="(v) EXTRAIR Texto", command=self.acao_extrair_arquivo).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="(^) INJETAR Texto", command=self.acao_injetar_arquivo).pack(side='left', padx=10)

    def setup_tab_pasta(self):
        frame = ttk.Frame(self.tab_pasta, padding="20")
        frame.pack(fill='both', expand=True)
        
        # Pasta BSO
        ttk.Label(frame, text="Pasta com arquivos BSO:").grid(row=0, column=0, sticky='w')
        self.ent_folder_bso = ttk.Entry(frame, width=50)
        self.ent_folder_bso.grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Procurar Pasta...", command=lambda: self.browse_folder(self.ent_folder_bso)).grid(row=1, column=1, padx=5)
        
        # Pasta JSON
        ttk.Label(frame, text="Pasta com arquivos JSON:").grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.ent_folder_json = ttk.Entry(frame, width=50)
        self.ent_folder_json.grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Procurar Pasta...", command=lambda: self.browse_folder(self.ent_folder_json)).grid(row=3, column=1, padx=5)

        # === NOVO: Op??es de Encoding na Aba Pasta ===
        lbl_enc = ttk.Label(frame, text="Encoding de Saida (para Injecao):")
        lbl_enc.grid(row=4, column=0, sticky='w', pady=(15, 0))
        
        opcoes_encoding = ['utf-8', 'shift-jis', 'cp932', 'latin-1', 'cp1252']
        # Nota: Usa a mesma vari?vel self.encoding_var, ent?o se mudar numa aba, muda na outra
        cb_encoding = ttk.Combobox(frame, values=opcoes_encoding, textvariable=self.encoding_var, state="readonly")
        cb_encoding.grid(row=5, column=0, sticky='w', pady=5)

        # Bot?es de A??o Pasta
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="(v) EXTRAIR Tudo da Pasta", command=self.acao_extrair_pasta).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="(^) INJETAR Tudo na Pasta", command=self.acao_injetar_pasta).pack(side='left', padx=10)

    # === Fun??es Auxiliares de Interface ===
    def browse_bso(self):
        f = filedialog.askopenfilename(filetypes=[("Arquivos BSO", "*.bso"), ("Todos", "*.*")])
        if f:
            self.ent_bso_file.delete(0, tk.END)
            self.ent_bso_file.insert(0, f)
            json_path = f.replace('.bso', '.json')
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

    # === L?GICA DO SCRIPT ORIGINAL ===
    
    def detectar_encoding(self, arquivo):
        encodings = ['utf-8', 'shift-jis', 'cp932', 'latin-1', 'iso-8859-1']
        for enc in encodings:
            try:
                with open(arquivo, 'r', encoding=enc) as f:
                    f.read()
                return enc
            except UnicodeDecodeError:
                continue
        return 'latin-1'

    def acao_extrair_arquivo(self):
        bso = self.ent_bso_file.get()
        jsn = self.ent_json_file.get()
        
        if not bso or not os.path.exists(bso):
            messagebox.showerror("Erro", "Arquivo BSO nao encontrado!")
            return
            
        self.log(f"--- Iniciando Extracao: {os.path.basename(bso)} ---")
        try:
            encoding = self.detectar_encoding(bso)
            self.log(f"Encoding detectado: {encoding}")
            
            with open(bso, 'r', encoding=encoding) as f:
                conteudo = f.read()
            
            padrao = r'\(a3:send-string\s+"(\[.*?\$K\].*?\$N)"\s+\d+\)'
            textos = []
            for match in re.finditer(padrao, conteudo):
                texto = match.group(1)
                textos.append({'original': texto, 'traducao': texto})
            
            with open(jsn, 'w', encoding='utf-8') as f:
                json.dump(textos, f, ensure_ascii=False, indent=2)
                
            self.log(f"Sucesso! {len(textos)} linhas extraidas.")
            self.log(f"Salvo em: {jsn}")
            messagebox.showinfo("Concluido", "Extracao finalizada com sucesso!")
            
        except Exception as e:
            self.log(f"Erro: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def acao_injetar_arquivo(self):
        bso = self.ent_bso_file.get()
        jsn = self.ent_json_file.get()
        enc_saida = self.encoding_var.get()
        
        if not bso or not os.path.exists(bso):
            messagebox.showerror("Erro", "Arquivo BSO nao encontrado!")
            return
        if not jsn or not os.path.exists(jsn):
            messagebox.showerror("Erro", "Arquivo JSON nao encontrado!")
            return

        arquivo_saida = bso.replace('.bso', '_traduzido.bso')
        
        self.log(f"--- Iniciando Injecao: {os.path.basename(bso)} ---")
        self.log(f"Encoding de saida escolhido: {enc_saida}")
        
        try:
            encoding_orig = self.detectar_encoding(bso)
            with open(bso, 'r', encoding=encoding_orig) as f:
                conteudo = f.read()
            
            with open(jsn, 'r', encoding='utf-8') as f:
                traducoes = json.load(f)
            
            mapa = {item['original']: item['traducao'] for item in traducoes}
            
            padrao = r'(\(a3:send-string\s+)"(\[.*?\$K\].*?\$N)"(\s+\d+\))'
            
            def substituir(m):
                orig = m.group(2)
                trad = mapa.get(orig, orig)
                return f'{m.group(1)}"{trad}"{m.group(3)}'
            
            conteudo_novo = re.sub(padrao, substituir, conteudo)
            
            # Substitui??es de caracteres especiais
            conteudo_novo = conteudo_novo.replace('?', '~~')
            
            with open(arquivo_saida, 'w', encoding=enc_saida, errors='replace') as f:
                f.write(conteudo_novo)
                
            self.log("Injecao concluida!")
            self.log(f"Arquivo criado: {arquivo_saida}")
            messagebox.showinfo("Concluido", f"Arquivo traduzido criado:\n{arquivo_saida}")
            
        except Exception as e:
            self.log(f"Erro fatal: {str(e)}")
            messagebox.showerror("Erro", str(e))

    def acao_extrair_pasta(self):
        pasta_bso = self.ent_folder_bso.get()
        pasta_json = self.ent_folder_json.get() or os.path.join(pasta_bso, "json_output")
        
        if not os.path.exists(pasta_bso):
            messagebox.showerror("Erro", "Pasta BSO invalida")
            return
            
        if not os.path.exists(pasta_json):
            os.makedirs(pasta_json)
            
        self.log(f"--- Processando pasta: {pasta_bso} ---")
        arquivos = [f for f in os.listdir(pasta_bso) if f.endswith('.bso')]
        
        if not arquivos:
            self.log("Nenhum arquivo .bso encontrado.")
            return

        for arq in arquivos:
            caminho_bso = os.path.join(pasta_bso, arq)
            caminho_json = os.path.join(pasta_json, arq.replace('.bso', '.json'))
            
            try:
                encoding = self.detectar_encoding(caminho_bso)
                with open(caminho_bso, 'r', encoding=encoding) as f:
                    conteudo = f.read()
                
                padrao = r'\(a3:send-string\s+"(\[.*?\$K\].*?\$N)"\s+\d+\)'
                textos = []
                for match in re.finditer(padrao, conteudo):
                    textos.append({'original': match.group(1), 'traducao': match.group(1)})
                
                with open(caminho_json, 'w', encoding='utf-8') as f:
                    json.dump(textos, f, ensure_ascii=False, indent=2)
                self.log(f"OK: {arq}")
            except Exception as e:
                self.log(f"FALHA {arq}: {e}")
                
        self.log("--- Processamento de pasta finalizado ---")
        messagebox.showinfo("Fim", "Processamento em lote concluido!")

    def acao_injetar_pasta(self):
        pasta_bso = self.ent_folder_bso.get()
        pasta_json = self.ent_folder_json.get()
        pasta_saida = os.path.join(pasta_bso, "traduzidos")
        enc_saida = self.encoding_var.get()
        
        if not os.path.exists(pasta_bso) or not os.path.exists(pasta_json):
            messagebox.showerror("Erro", "Verifique os caminhos das pastas!")
            return

        if not os.path.exists(pasta_saida):
            os.makedirs(pasta_saida)
            
        arquivos_json = [f for f in os.listdir(pasta_json) if f.endswith('.json')]
        self.log(f"--- Injetando traducoes em lote (Enc: {enc_saida}) ---")
        
        for arq_json in arquivos_json:
            nome_bso = arq_json.replace('.json', '.bso')
            caminho_bso_orig = os.path.join(pasta_bso, nome_bso)
            caminho_json_full = os.path.join(pasta_json, arq_json)
            caminho_saida = os.path.join(pasta_saida, nome_bso)
            
            if not os.path.exists(caminho_bso_orig):
                self.log(f"PULADO: {nome_bso} (Original nao encontrado)")
                continue
                
            try:
                encoding_orig = self.detectar_encoding(caminho_bso_orig)
                with open(caminho_bso_orig, 'r', encoding=encoding_orig) as f:
                    conteudo = f.read()
                
                with open(caminho_json_full, 'r', encoding='utf-8') as f:
                    traducoes = json.load(f)
                
                mapa = {item['original']: item['traducao'] for item in traducoes}
                
                padrao = r'(\(a3:send-string\s+)"(\[.*?\$K\].*?\$N)"(\s+\d+\))'
                conteudo_novo = re.sub(padrao, lambda m: f'{m.group(1)}"{mapa.get(m.group(2), m.group(2))}"{m.group(3)}', conteudo)
                conteudo_novo = conteudo_novo.replace('?', '~~')
                
                with open(caminho_saida, 'w', encoding=enc_saida, errors='replace') as f:
                    f.write(conteudo_novo)
                self.log(f"OK: {nome_bso}")
                
            except Exception as e:
                self.log(f"FALHA {nome_bso}: {e}")

        self.log(f"Arquivos salvos em: {pasta_saida}")
        messagebox.showinfo("Fim", "Injecao em lote concluida!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BsoToolGUI(root)
    root.mainloop()