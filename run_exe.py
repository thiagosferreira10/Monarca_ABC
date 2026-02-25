import os
import subprocess
import sys
from datetime import datetime

def log(msg):
    try:
        if getattr(sys, 'frozen', False):
            log_dir = os.path.dirname(sys.executable)
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(log_dir, "launcher_log.txt")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except:
        pass

def main():
    log("=== Launcher iniciado ===")

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    log(f"exe_dir: {exe_dir}")

    target_file = "HOME.py"
    script_path = os.path.join(exe_dir, target_file)
    work_dir = exe_dir

    if not os.path.exists(script_path):
        parent_dir = os.path.dirname(exe_dir)
        script_path_parent = os.path.join(parent_dir, target_file)
        if os.path.exists(script_path_parent):
            script_path = script_path_parent
            work_dir = parent_dir
        else:
            msg = f"Arquivo '{target_file}' nao encontrado em:\n  {exe_dir}"
            log(msg)
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, "Erro Fatal - Monarca ABC", 0x10)
            sys.exit(1)

    log(f"HOME.py: {script_path}")
    os.chdir(work_dir)

    python_exe = sys.executable if not getattr(sys, 'frozen', False) else "python"
    cmd = [python_exe, "-m", "streamlit", "run", "HOME.py", "--global.developmentMode=false"]
    log(f"cmd: {' '.join(cmd)}")

    err_log = os.path.join(exe_dir, "streamlit_err.txt")

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    try:
        with open(err_log, "w", encoding="utf-8") as err_file:
            subprocess.Popen(
                cmd,
                shell=True,
                cwd=work_dir,
                stdin=subprocess.DEVNULL,
                stdout=err_file,
                stderr=err_file,
                startupinfo=startupinfo,
            )
        log("Streamlit iniciado com sucesso")
    except Exception as e:
        log(f"EXCECAO: {e}")
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Falha ao iniciar:\n{e}", "Erro - Monarca ABC", 0x10)

if __name__ == '__main__':
    main()
