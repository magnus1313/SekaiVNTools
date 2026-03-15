# coding: utf-8
"""
ks_tool_gui_v3.py
Formato TXT: "dialogue | #Nome | Texto"
"""

import sys
import json
import re
import threading
from pathlib import Path
from typing import List, Dict
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ----------------------------------------------------
# Lógica Principal (Core)
# ----------------------------------------------------

GLINK_PATTERN = re.compile(r'\[glink\s+.*?text="([^"]+)".*?\]')
GLINK_REPLACE_PATTERN = re.compile(r'(text=")([^"]+)(")')
TAGS_REMOVAL_PATTERN = re.compile(r'\[.*?\]')

def extract_ks_data(file_path: Path) -> List[Dict]:
    """Lê o .ks e extrai textos, rastreando nomes de personagens (#Nome)."""
    try:
        with file_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise Exception(f"Erro ao ler {file_path.name}: {e}")

    extracted = []
    in_tyrano_code = False
    current_character = "" # Variável para guardar o nome da linha anterior

    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 1. Extrair de Glinks
        if stripped.startswith('[glink'):
            match = GLINK_PATTERN.search(stripped)
            if match:
                extracted.append({
                    "line_num": i,
                    "type": "glink",
                    "original": match.group(1),
                    "character": "", # Glinks geralmente não têm personagem associado no script
                    "translated": ""
                })
            continue
            
        # 2. Rastrear blocos de código
        if stripped == '[tb_start_tyrano_code]':
            in_tyrano_code = True
            continue
        elif stripped == '[_tb_end_tyrano_code]':
            in_tyrano_code = False
            continue
            
        # 3. Extrair Diálogos e Narrativa
        if in_tyrano_code:
            # Se for uma linha de nome (começa com #), atualiza a variável atual
            if stripped.startswith('#'):
                current_character = stripped
                continue

            # Ignora linhas vazias e comentários
            if not stripped or stripped.startswith(';'):
                continue
            
            # Remove tags para checar se há texto real
            text_without_tags = TAGS_REMOVAL_PATTERN.sub('', stripped)
            if not text_without_tags.strip():
                continue 
            
            # Adiciona o diálogo com o contexto do nome atual
            extracted.append({
                "line_num": i,
                "type": "dialogue",
                "original": stripped,
                "character": current_character, # Novo campo
                "translated": ""
            })
            
    return extracted

def inject_ks_data(original_ks_path: Path, entries: List[Dict]) -> List[str]:
    """Lê o .ks original e aplica as traduções."""
    try:
        with original_ks_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise Exception(f"Erro ao ler original {original_ks_path.name}: {e}")

    for item in entries:
        idx = item["line_num"]
        translated_text = item.get("translated", "").strip()
        
        # Se não houver tradução, mantém o original
        if not translated_text:
            translated_text = item["original"]
            
        if item["type"] == "dialogue":
            if idx < len(lines):
                leading_spaces = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
                lines[idx] = leading_spaces + translated_text + '\n'
        
        elif item["type"] == "glink":
            if idx < len(lines):
                lines[idx] = GLINK_REPLACE_PATTERN.sub(rf'\g<1>{translated_text}\g<3>', lines[idx])

    return lines

# ----------------------------------------------------
# Conversor TXT (Lógica atualizada para 3 partes)
# ----------------------------------------------------

def json_to_txt(json_path: Path, out_txt_path: Path):
    entries = []
    with json_path.open('r', encoding='utf-8') as f:
        entries = json.load(f)
    
    with out_txt_path.open('w', encoding='utf-8') as f:
        for item in entries:
            char = item.get('character', '')
            
            # Se tiver nome do personagem, formato com 3 partes
            if char:
                f.write(f"{item['type']} | {char} | {item['original']}\n")
            else:
                # Caso contrário (glink ou sem nome), formato padrão
                f.write(f"{item['type']} | {item['original']}\n")
                
    return len(entries)

def txt_to_json(txt_path: Path, original_json_path: Path, out_json_path: Path):
    with original_json_path.open('r', encoding='utf-8') as f:
        entries = json.load(f)
    
    with txt_path.open('r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f]

    if len(entries) != len(lines):
        raise ValueError(f"Erro de contagem: O JSON tem {len(entries)} linhas, mas o TXT tem {len(lines)} linhas.")

    for i, line in enumerate(lines):
        # Divide pelo separador |
        parts = [p.strip() for p in line.split('|')]
        
        translated_text = ""
        
        # Lógica para pegar o texto correto ignorando o nome do contexto
        if len(parts) >= 3:
            # Formato: Type | Char | Texto
            # Pegamos a 3ª parte (índice 2)
            translated_text = parts[2]
        elif len(parts) == 2:
            # Formato: Type | Texto (Fallback para glinks ou linhas sem nome)
            translated_text = parts[1]
        else:
            # Fallback extremo
            translated_text = line.strip()
            
        entries[i]['translated'] = translated_text

    with out_json_path.open('w', encoding='utf-8') as f:
        json.dump(entries, f, indent=4, ensure_ascii=False)
    return len(entries)

# ----------------------------------------------------
# Interface Gráfica (GUI) - Mantida Igual
# ----------------------------------------------------

class KSToolGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KS Tool Pro v3 (Menherafflesia)")
        self.root.geometry("900x650")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.tab_extract = ttk.Frame(self.notebook)
        self.tab_inject = ttk.Frame(self.notebook)
        self.tab_convert = ttk.Frame(self.notebook) 
        
        self.notebook.add(self.tab_extract, text='  Extrair  ')
        self.notebook.add(self.tab_inject, text='  Injetar  ')
        self.notebook.add(self.tab_convert, text='  Conversor TXT  ')
        
        self.setup_extract_tab()
        self.setup_inject_tab()
        self.setup_convert_tab()
        
        self.status_var = tk.StringVar(value="Pronto.")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log(self, message, widget):
        widget.config(state='normal')
        widget.insert(tk.END, message + "\n")
        widget.see(tk.END)
        widget.config(state='disabled')
        self.root.update_idletasks()

    def create_log(self, parent):
        lbl_log = ttk.Label(parent, text="Log de Progresso:")
        lbl_log.pack(anchor='w', padx=10)
        txt = scrolledtext.ScrolledText(parent, height=12, state='disabled')
        txt.pack(fill='both', expand=True, padx=10, pady=5)
        return txt

    def setup_extract_tab(self):
        frame = ttk.LabelFrame(self.tab_extract, text="Configurações", padding=10)
        frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(frame, text="Codificação do KS:").grid(row=0, column=0, sticky='w')
        self.combo_enc_ext = ttk.Combobox(frame, values=["utf-8", "shift_jis", "latin1"], width=15)
        self.combo_enc_ext.set("utf-8")
        self.combo_enc_ext.grid(row=0, column=1, sticky='w', padx=5)

        frame_files = ttk.LabelFrame(self.tab_extract, text="Arquivos .KS", padding=10)
        frame_files.pack(fill='x', padx=10, pady=5)
        
        self.list_files_extract = tk.Listbox(frame_files, height=6)
        scrollbar = ttk.Scrollbar(frame_files, orient="vertical", command=self.list_files_extract.yview)
        self.list_files_extract.configure(yscrollcommand=scrollbar.set)
        self.list_files_extract.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_box = ttk.Frame(frame_files)
        btn_box.pack(side="right", fill='y', padx=5)
        ttk.Button(btn_box, text="Adicionar Arquivos", command=self.add_files_extract).pack(fill='x', pady=2)
        ttk.Button(btn_box, text="Limpar Lista", command=self.clear_files_extract).pack(fill='x', pady=2)

        ttk.Button(self.tab_extract, text="▶ INICIAR EXTRAÇÃO", command=self.start_extraction).pack(fill='x', padx=20, pady=10)
        self.txt_extract_log = self.create_log(self.tab_extract)

    def setup_inject_tab(self):
        frame = ttk.LabelFrame(self.tab_inject, text="Configurações", padding=10)
        frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(frame, text="Codificação de Saída:").grid(row=0, column=0, sticky='w')
        self.combo_enc_inj = ttk.Combobox(frame, values=["utf-8", "shift_jis", "latin1"], width=15)
        self.combo_enc_inj.set("utf-8")
        self.combo_enc_inj.grid(row=0, column=1, sticky='w', padx=5)

        frame_files = ttk.LabelFrame(self.tab_inject, text="Arquivos .KS", padding=10)
        frame_files.pack(fill='x', padx=10, pady=5)
        
        self.list_files_inject = tk.Listbox(frame_files, height=6)
        scrollbar2 = ttk.Scrollbar(frame_files, orient="vertical", command=self.list_files_inject.yview)
        self.list_files_inject.configure(yscrollcommand=scrollbar2.set)
        self.list_files_inject.pack(side="left", fill="both", expand=True)
        scrollbar2.pack(side="right", fill="y")
        
        btn_box = ttk.Frame(frame_files)
        btn_box.pack(side="right", fill='y', padx=5)
        ttk.Button(btn_box, text="Adicionar .KSs", command=self.add_files_inject).pack(fill='x', pady=2)
        ttk.Button(btn_box, text="Limpar Lista", command=self.clear_files_inject).pack(fill='x', pady=2)
        
        ttk.Button(self.tab_inject, text="▶ INICIAR INJEÇÃO", command=self.start_injection).pack(fill='x', padx=20, pady=10)
        self.txt_inject_log = self.create_log(self.tab_inject)

    def setup_convert_tab(self):
        info_frame = ttk.LabelFrame(self.tab_convert, text="Fluxo de Tradução", padding=10)
        info_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(info_frame, text="1. O TXT agora mostra 'Tipo | #Nome | Texto'.", foreground="blue").pack(anchor='w')
        ttk.Label(info_frame, text="2. Traduza apenas o texto final. O nome #Ayume é apenas contexto.", foreground="green").pack(anchor='w')
        
        frame_files = ttk.LabelFrame(self.tab_convert, text="Arquivos", padding=10)
        frame_files.pack(fill='x', padx=10, pady=5)
        
        self.list_files_convert = tk.Listbox(frame_files, height=6)
        scrollbar3 = ttk.Scrollbar(frame_files, orient="vertical", command=self.list_files_convert.yview)
        self.list_files_convert.configure(yscrollcommand=scrollbar3.set)
        self.list_files_convert.pack(side="left", fill="both", expand=True)
        scrollbar3.pack(side="right", fill="y")
        
        btn_box = ttk.Frame(frame_files)
        btn_box.pack(side="right", fill='y', padx=5)
        ttk.Button(btn_box, text="Adicionar .JSONs", command=self.add_files_convert).pack(fill='x', pady=2)
        ttk.Button(btn_box, text="Limpar Lista", command=self.clear_files_convert).pack(fill='x', pady=2)
        
        action_frame = ttk.Frame(self.tab_convert)
        action_frame.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(action_frame, text="📄 JSON -> TXT (Extrair Texto)", command=self.start_json_to_txt).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(action_frame, text="💾 TXT -> JSON (Aplicar Tradução)", command=self.start_txt_to_json).pack(side='right', expand=True, fill='x', padx=5)
        self.txt_convert_log = self.create_log(self.tab_convert)

    def add_files_generic(self, listbox, title, ext):
        files = filedialog.askopenfilenames(title=title, filetypes=[(f"{ext} Files", f"*.{ext}"), ("All Files", "*.*")])
        for f in files:
            listbox.insert(tk.END, f)

    def add_files_extract(self): self.add_files_generic(self.list_files_extract, "Selecionar KSs", "ks")
    def add_files_inject(self): self.add_files_generic(self.list_files_inject, "Selecionar KSs", "ks")
    def add_files_convert(self): self.add_files_generic(self.list_files_convert, "Selecionar JSONs", "json")

    def clear_files_generic(self, listbox, txt_widget):
        listbox.delete(0, tk.END)
        txt_widget.config(state='normal')
        txt_widget.delete(1.0, tk.END)
        txt_widget.config(state='disabled')
        
    def clear_files_extract(self): self.clear_files_generic(self.list_files_extract, self.txt_extract_log)
    def clear_files_inject(self): self.clear_files_generic(self.list_files_inject, self.txt_inject_log)
    def clear_files_convert(self): self.clear_files_generic(self.list_files_convert, self.txt_convert_log)

    def start_extraction(self):
        files = [self.list_files_extract.get(i) for i in range(self.list_files_extract.size())]
        if not files: return
        self.txt_extract_log.config(state='normal')
        self.txt_extract_log.delete(1.0, tk.END)
        self.txt_extract_log.config(state='disabled')
        t = threading.Thread(target=self.run_extraction, args=(files,))
        t.start()

    def run_extraction(self, files):
        self.log(f"Processando {len(files)} arquivo(s)...", self.txt_extract_log)
        for f_str in files:
            ks_path = Path(f_str)
            self.log(f"Lendo: {ks_path.name}", self.txt_extract_log)
            try:
                entries = extract_ks_data(ks_path)
                out_json = ks_path.with_name(ks_path.stem + ".strings.json")
                with out_json.open('w', encoding='utf-8') as f:
                    json.dump(entries, f, indent=4, ensure_ascii=False)
                self.log(f"  -> {len(entries)} textos. Salvo em {out_json.name}", self.txt_extract_log)
            except Exception as e:
                self.log(f"  ❌ ERRO: {e}", self.txt_extract_log)
        self.log("✅ Extração concluída.", self.txt_extract_log)

    def start_injection(self):
        files = [self.list_files_inject.get(i) for i in range(self.list_files_inject.size())]
        if not files: return
        self.txt_inject_log.config(state='normal')
        self.txt_inject_log.delete(1.0, tk.END)
        self.txt_inject_log.config(state='disabled')
        t = threading.Thread(target=self.run_injection, args=(files,))
        t.start()

    def run_injection(self, files):
        enc = self.combo_enc_inj.get()
        self.log(f"Iniciando injeção...", self.txt_inject_log)
        for f_str in files:
            ks_path = Path(f_str)
            json_paths = [
                ks_path.with_name(ks_path.stem + ".translated.json"),
                ks_path.with_name(ks_path.stem + ".strings.json")
            ]
            json_path = next((jp for jp in json_paths if jp.exists()), None)
            
            if not json_path:
                self.log(f"  ❌ JSON não encontrado para {ks_path.name}.", self.txt_inject_log)
                continue
            
            try:
                with json_path.open('r', encoding='utf-8') as f:
                    entries = json.load(f)
                new_lines = inject_ks_data(ks_path, entries)
                out_ks = ks_path.with_name(ks_path.stem + "_translated.ks")
                with out_ks.open('w', encoding=enc) as f:
                    f.writelines(new_lines)
                self.log(f"  ✅ Salvo: {out_ks.name}", self.txt_inject_log)
            except Exception as e:
                self.log(f"  ❌ ERRO: {e}", self.txt_inject_log)
        self.log("✅ Injeção finalizada.", self.txt_inject_log)

    def start_json_to_txt(self):
        files = [self.list_files_convert.get(i) for i in range(self.list_files_convert.size())]
        if not files: return
        self.txt_convert_log.config(state='normal')
        self.txt_convert_log.delete(1.0, tk.END)
        self.txt_convert_log.config(state='disabled')
        t = threading.Thread(target=self.run_json_to_txt, args=(files,))
        t.start()

    def run_json_to_txt(self, files):
        self.log("Convertendo JSON -> TXT...", self.txt_convert_log)
        for f_str in files:
            p = Path(f_str)
            try:
                count = json_to_txt(p, p.with_suffix('.txt'))
                self.log(f"  ✅ {p.name} -> .txt ({count} linhas)", self.txt_convert_log)
            except Exception as e:
                self.log(f"  ❌ ERRO: {e}", self.txt_convert_log)
        self.log("Conversão finalizada.", self.txt_convert_log)

    def start_txt_to_json(self):
        files = [self.list_files_convert.get(i) for i in range(self.list_files_convert.size())]
        if not files: return
        self.txt_convert_log.config(state='normal')
        self.txt_convert_log.delete(1.0, tk.END)
        self.txt_convert_log.config(state='disabled')
        t = threading.Thread(target=self.run_txt_to_json, args=(files,))
        t.start()

    def run_txt_to_json(self, files):
        self.log("Aplicando TXT no JSON...", self.txt_convert_log)
        for f_str in files:
            json_path = Path(f_str)
            txt_path = json_path.with_suffix('.txt')
            if not txt_path.exists():
                self.log(f"  ⚠️ TXT não encontrado: {txt_path.name}", self.txt_convert_log)
                continue
            try:
                count = txt_to_json(txt_path, json_path, json_path.with_name(json_path.stem + ".translated.json"))
                self.log(f"  ✅ Aplicado ({count} itens)", self.txt_convert_log)
            except Exception as e:
                self.log(f"  ❌ ERRO: {e}", self.txt_convert_log)
        self.log("Aplicação finalizada.", self.txt_convert_log)

if __name__ == '__main__':
    root = tk.Tk()
    app = KSToolGUI(root)
    root.mainloop()