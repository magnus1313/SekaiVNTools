import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import re
import os
import shutil

class SCEditorBatchTool:
    def __init__(self, root):
        self.root = root
        self.root.title("SC Script Tool - Batch Mode (Fix)")
        self.root.geometry("650x550")

        # Tabela de substituição de caracteres (Expandida para evitar erros)
        # Adicionei 'í' minúsculo e outros comuns que causam o erro \xed
        self.char_map = str.maketrans({
            'Á': 'ﾁ', 'É': 'ﾉ', 'Í': 'ﾍ', 'Ó': 'ﾓ', 'Ú': 'ﾚ',
            'á': '$',  'ã': '^',  'à': '<',  'â': '>',  'ç': '&',
            'é': '%',  'ú': '(',  'ó': ')',  'õ': '*',
            'í': '?',  'ê': '?',  'ô': '?',  'î': '?',  # Adicionados placeholders para evitar crash
            '“': '"',  '”': '"',  '‘': "'",  '’': "'"   # Corrige aspas inteligentes (Word)
        })

        # Criação das Abas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Aba 1: Extração
        self.tab_extract = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_extract, text=" 1. Extração (.sc -> .txt) ")
        self.setup_extract_tab()

        # Aba 2: Injeção
        self.tab_inject = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inject, text=" 2. Injeção (.txt -> .sc) ")
        self.setup_inject_tab()

    # --- Configuração da GUI ---

    def setup_extract_tab(self):
        btn_frame = tk.Frame(self.tab_extract)
        btn_frame.pack(pady=10, fill='x')
        
        btn = tk.Button(btn_frame, text="Selecionar Arquivos .sc (Lote)", command=self.select_sc_files, bg="#e1f5fe", width=30)
        btn.pack()

        lbl_list = tk.Label(self.tab_extract, text="Arquivos na fila:", anchor="w")
        lbl_list.pack(fill='x', padx=10)
        
        self.list_extract = tk.Listbox(self.tab_extract, height=8)
        self.list_extract.pack(fill='x', padx=10, pady=5)
        
        btn_proc = tk.Button(self.tab_extract, text=">> INICIAR EXTRAÇÃO <<", command=self.run_extraction, bg="#b3e5fc", font=("Arial", 10, "bold"))
        btn_proc.pack(pady=10)

        self.log_extract = scrolledtext.ScrolledText(self.tab_extract, height=12, state='disabled', font=("Consolas", 9))
        self.log_extract.pack(fill='both', expand=True, padx=10, pady=5)

    def setup_inject_tab(self):
        btn_frame = tk.Frame(self.tab_inject)
        btn_frame.pack(pady=10, fill='x')
        
        btn = tk.Button(btn_frame, text="Selecionar Arquivos .txt (Lote)", command=self.select_txt_files, bg="#e8f5e9", width=30)
        btn.pack()

        lbl_list = tk.Label(self.tab_inject, text="Arquivos na fila:", anchor="w")
        lbl_list.pack(fill='x', padx=10)
        
        self.list_inject = tk.Listbox(self.tab_inject, height=8)
        self.list_inject.pack(fill='x', padx=10, pady=5)

        btn_proc = tk.Button(self.tab_inject, text=">> INICIAR INJEÇÃO <<", command=self.run_injection, bg="#c8e6c9", font=("Arial", 10, "bold"))
        btn_proc.pack(pady=10)

        self.log_inject = scrolledtext.ScrolledText(self.tab_inject, height=12, state='disabled', font=("Consolas", 9))
        self.log_inject.pack(fill='both', expand=True, padx=10, pady=5)

    def log(self, widget, message):
        widget.config(state='normal')
        widget.insert(tk.END, message + "\n")
        widget.see(tk.END)
        widget.config(state='disabled')
        self.root.update_idletasks()

    # --- Lógica de Extração ---

    def select_sc_files(self):
        files = filedialog.askopenfilenames(
            title="Selecione um ou mais arquivos .sc",
            filetypes=[("Arquivos SC", "*.sc"), ("Todos os arquivos", "*.*")]
        )
        if files:
            self.list_extract.delete(0, tk.END)
            self.sc_files_list = list(files)
            for f in self.sc_files_list:
                self.list_extract.insert(tk.END, os.path.basename(f))
            self.log(self.log_extract, f"{len(files)} arquivo(s) selecionado(s).")

    def extract_single_file(self, sc_path):
        try:
            base_name = os.path.splitext(sc_path)[0]
            txt_path = base_name + "_extraido.txt"
            pattern = re.compile(r'^\.message\s+(\d+)\s+(.*)$', re.MULTILINE)

            content = ""
            try:
                with open(sc_path, 'r', encoding='cp932') as f:
                    content = f.read()
                enc_detected = "Shift-JIS"
            except UnicodeDecodeError:
                with open(sc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                enc_detected = "UTF-8"

            matches = pattern.findall(content)
            
            if not matches:
                return "Nenhuma mensagem encontrada."

            with open(txt_path, 'w', encoding='utf-8') as f_out:
                f_out.write("=== INSTRUÇÕES ===\n")
                f_out.write("Edite em UTF-8. Formato: [ID] Texto\n")
                f_out.write("Cuidado com acentos não mapeados (virarão ?)\n")
                f_out.write("===================\n\n")
                for msg_id, msg_text in matches:
                    f_out.write(f"[{msg_id}] {msg_text}\n")

            return f"OK ({len(matches)} linhas) [{enc_detected}]"

        except Exception as e:
            return f"ERRO: {e}"

    def run_extraction(self):
        if not hasattr(self, 'sc_files_list') or not self.sc_files_list:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo .sc.")
            return

        self.log(self.log_extract, "--- Iniciando Extração em Lote ---")
        success_count = 0
        
        for sc_file in self.sc_files_list:
            name = os.path.basename(sc_file)
            self.log(self.log_extract, f"Processando: {name} ...")
            result = self.extract_single_file(sc_file)
            self.log(self.log_extract, f"  -> {result}")
            if "ERRO" not in result:
                success_count += 1
        
        self.log(self.log_extract, f"--- Concluído: {success_count}/{len(self.sc_files_list)} arquivos ---")

    # --- Lógica de Injeção ---

    def select_txt_files(self):
        files = filedialog.askopenfilenames(
            title="Selecione um ou mais arquivos .txt",
            filetypes=[("Arquivos de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        if files:
            self.list_inject.delete(0, tk.END)
            self.txt_files_list = list(files)
            for f in self.txt_files_list:
                self.list_inject.insert(tk.END, os.path.basename(f))
            self.log(self.log_inject, f"{len(files)} arquivo(s) selecionado(s).")

    def inject_single_file(self, txt_path):
        try:
            sc_path_guess = txt_path.replace("_extraido.txt", ".sc")
            
            if not os.path.exists(sc_path_guess):
                base = os.path.basename(txt_path).replace("_extraido", "").replace(".txt", "")
                dir_path = os.path.dirname(txt_path)
                potential_sc = os.path.join(dir_path, base + ".sc")
                if os.path.exists(potential_sc):
                    sc_path_guess = potential_sc
                else:
                    return "ERRO: Arquivo .sc correspondente não encontrado."

            sc_path = sc_path_guess

            # 1. Ler TXT e processar
            translations = {}
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or "INSTRUÇÕES" in line or line.startswith("==="):
                    continue
                
                match = re.match(r'^\[(\d+)\]\s+(.*)$', line)
                if match:
                    sc_id = match.group(1)
                    raw_text = match.group(2)
                    # Aplica o mapeamento
                    processed_text = raw_text.translate(self.char_map)
                    translations[sc_id] = processed_text

            if not translations:
                return "AVISO: Nenhum texto válido encontrado no TXT."

            # 2. Ler SC
            sc_lines = []
            try:
                with open(sc_path, 'r', encoding='cp932') as f:
                    sc_lines = f.readlines()
            except:
                with open(sc_path, 'r', encoding='utf-8') as f:
                    sc_lines = f.readlines()

            # 3. Substituir
            new_sc_lines = []
            count_modified = 0
            for line in sc_lines:
                match = re.match(r'^(\.message\s+\d+\s+)(.*)$', line)
                if match:
                    prefix = match.group(1)
                    id_search = re.search(r'\.message\s+(\d+)', prefix)
                    if id_search:
                        sc_id = id_search.group(1)
                        if sc_id in translations:
                            new_content = translations[sc_id]
                            new_line = f"{prefix}{new_content}\n"
                            new_sc_lines.append(new_line)
                            count_modified += 1
                            continue
                new_sc_lines.append(line)

            # 4. Salvar com MODO SEGURO (errors='replace')
            backup_path = sc_path + ".bak"
            if not os.path.exists(backup_path):
                 shutil.copy2(sc_path, backup_path)
            
            # CORREÇÃO AQUI: Adicionei errors='replace'
            # Isso impede que o script trave se achar um caractere inválido no Shift-JIS
            with open(sc_path, 'w', encoding='cp932', errors='replace', newline='') as f:
                f.writelines(new_sc_lines)

            return f"OK ({count_modified} linhas injetadas)"

        except Exception as e:
            return f"ERRO: {e}"

    def run_injection(self):
        if not hasattr(self, 'txt_files_list') or not self.txt_files_list:
            messagebox.showwarning("Aviso", "Selecione pelo menos um arquivo .txt.")
            return

        self.log(self.log_inject, "--- Iniciando Injeção em Lote ---")
        success_count = 0
        
        for txt_file in self.txt_files_list:
            name = os.path.basename(txt_file)
            self.log(self.log_inject, f"Processando: {name} ...")
            result = self.inject_single_file(txt_file)
            self.log(self.log_inject, f"  -> {result}")
            if "ERRO" not in result:
                success_count += 1
        
        self.log(self.log_inject, f"--- Concluído: {success_count}/{len(self.txt_files_list)} arquivos ---")

if __name__ == "__main__":
    root = tk.Tk()
    app = SCEditorBatchTool(root)
    root.mainloop()