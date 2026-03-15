import io
import os
import struct
import zipfile
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

EOCD_SIG = b"PK\x05\x06"

# ==========================================
# LÓGICA DE EXTRAÇÃO E RECONSTRUÇÃO
# ==========================================

def find_embedded_zip_candidates(data: bytes):
    """Busca os arquivos ZIP embutidos no EXE, lógica do extrair_package.py original."""
    i = 0
    while True:
        i = data.find(EOCD_SIG, i)
        if i == -1:
            break

        if i + 22 > len(data):
            i += 1
            continue

        try:
            disk_no, cd_disk, disk_entries, total_entries, cd_size, cd_offset, comment_len = struct.unpack_from(
                "<HHHHIIH", data, i + 4
            )
        except struct.error:
            i += 1
            continue

        end = i + 22 + comment_len
        if end > len(data):
            i += 1
            continue

        zip_start = i - cd_offset - cd_size
        if zip_start < 0:
            i += 1
            continue

        blob = data[zip_start:end]

        try:
            with zipfile.ZipFile(io.BytesIO(blob), "r") as zf:
                names = zf.namelist()
                if "package.json" in names or "index.html" in names:
                    yield {
                        "zip_start": zip_start,
                        "zip_end": end,
                        "size": len(blob),
                        "names": names,
                        "blob": blob,
                    }
        except zipfile.BadZipFile:
            pass

        i += 1

def process_patch(exe_path, patch_path, output_path, log_callback, finish_callback):
    """Executa o processo completo de patching em background."""
    try:
        log_callback("Lendo o executável original...")
        with open(exe_path, "rb") as f:
            data = f.read()

        log_callback("Procurando o pacote embutido (Offset)...")
        candidates = list(find_embedded_zip_candidates(data))
        if not candidates:
            raise Exception("Nenhum pacote zip embutido com package.json/index.html foi encontrado no EXE.")

        best = max(candidates, key=lambda c: c["size"])
        zip_start = best["zip_start"]
        base_zip_blob = best["blob"]
        
        log_callback(f"Pacote encontrado! Offset inicial: {zip_start}")

        # Usamos uma pasta temporária para fazer o merge dos arquivos
        with tempfile.TemporaryDirectory() as tmpdir:
            log_callback("Extraindo arquivos originais na memória...")
            with zipfile.ZipFile(io.BytesIO(base_zip_blob)) as zf_base:
                zf_base.extractall(tmpdir)

            log_callback("Aplicando o patch de tradução...")
            with zipfile.ZipFile(patch_path) as zf_patch:
                zf_patch.extractall(tmpdir)

            log_callback("Reconstruindo o pacote com os novos arquivos...")
            patched_zip_io = io.BytesIO()
            with zipfile.ZipFile(patched_zip_io, "w", zipfile.ZIP_DEFLATED) as zf_new:
                for root, _, files in os.walk(tmpdir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, tmpdir)
                        zf_new.write(file_path, arcname)
            
            patched_pkg_bytes = patched_zip_io.getvalue()

        log_callback("Gerando o novo executável...")
        stub = data[:zip_start]
        with open(output_path, "wb") as f:
            f.write(stub)
            f.write(patched_pkg_bytes)

        log_callback("\nSUCESSO! O jogo foi traduzido.")
        log_callback(f"Salvo em: {output_path}")
        finish_callback(True)

    except Exception as e:
        log_callback(f"\nERRO: {str(e)}")
        finish_callback(False)

# ==========================================
# INTERFACE GRÁFICA (GUI)
# ==========================================

class PatcherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Patcher Menherafflesia")
        self.geometry("550x450")
        self.resizable(False, False)

        # Variáveis dos caminhos
        self.exe_path_var = tk.StringVar()
        self.patch_path_var = tk.StringVar()
        self.output_path_var = tk.StringVar(value=os.path.join(os.getcwd(), "menherafflesia_br.exe"))

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # 1. Executável Original
        tk.Label(frame, text="Executável Original do Jogo (.exe):", anchor="w").pack(fill=tk.X)
        frame_exe = tk.Frame(frame)
        frame_exe.pack(fill=tk.X, pady=(0, 10))
        tk.Entry(frame_exe, textvariable=self.exe_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(frame_exe, text="Procurar...", command=self.browse_exe).pack(side=tk.RIGHT)

        # 2. Patch de Tradução
        tk.Label(frame, text="Arquivo de Tradução (Patch.zip):", anchor="w").pack(fill=tk.X)
        frame_patch = tk.Frame(frame)
        frame_patch.pack(fill=tk.X, pady=(0, 10))
        tk.Entry(frame_patch, textvariable=self.patch_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(frame_patch, text="Procurar...", command=self.browse_patch).pack(side=tk.RIGHT)

        # 3. Arquivo de Saída
        tk.Label(frame, text="Onde salvar o jogo traduzido:", anchor="w").pack(fill=tk.X)
        frame_out = tk.Frame(frame)
        frame_out.pack(fill=tk.X, pady=(0, 15))
        tk.Entry(frame_out, textvariable=self.output_path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(frame_out, text="Procurar...", command=self.browse_output).pack(side=tk.RIGHT)

        # Botão Iniciar
        self.btn_start = tk.Button(frame, text="Aplicar Tradução", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), command=self.start_patching)
        self.btn_start.pack(fill=tk.X, pady=(0, 15))

        # Log
        tk.Label(frame, text="Progresso:", anchor="w").pack(fill=tk.X)
        self.txt_log = tk.Text(frame, height=8, state=tk.DISABLED, bg="#f0f0f0")
        self.txt_log.pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        """Adiciona mensagens à caixa de texto de progresso."""
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def browse_exe(self):
        path = filedialog.askopenfilename(title="Selecione o executável original", filetypes=[("Executáveis", "*.exe")])
        if path:
            self.exe_path_var.set(path)

    def browse_patch(self):
        path = filedialog.askopenfilename(title="Selecione o arquivo de Patch", filetypes=[("Arquivos ZIP", "*.zip")])
        if path:
            self.patch_path_var.set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(title="Salvar jogo traduzido como", defaultextension=".exe", filetypes=[("Executáveis", "*.exe")], initialfile="menherafflesia_traduzido.exe")
        if path:
            self.output_path_var.set(path)

    def start_patching(self):
        exe_path = self.exe_path_var.get()
        patch_path = self.patch_path_var.get()
        output_path = self.output_path_var.get()

        if not exe_path or not os.path.exists(exe_path):
            messagebox.showerror("Erro", "Por favor, selecione um executável original válido.")
            return
        if not patch_path or not os.path.exists(patch_path):
            messagebox.showerror("Erro", "Por favor, selecione o arquivo de Patch (ZIP) válido.")
            return

        # Desabilita o botão para não clicar duas vezes
        self.btn_start.config(state=tk.DISABLED, text="Processando...")
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete(1.0, tk.END) # Limpa o log
        self.txt_log.config(state=tk.DISABLED)

        # Roda o processamento em uma Thread separada para não travar a GUI
        threading.Thread(
            target=process_patch, 
            args=(exe_path, patch_path, output_path, self.log, self.on_finish),
            daemon=True
        ).start()

    def on_finish(self, success):
        """Reabilita a interface quando terminar."""
        self.btn_start.config(state=tk.NORMAL, text="Aplicar Tradução")
        if success:
            messagebox.showinfo("Concluído", "A tradução foi aplicada com sucesso!\nDivirta-se jogando.")

if __name__ == "__main__":
    app = PatcherApp()
    app.mainloop()