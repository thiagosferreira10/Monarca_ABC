import os
import subprocess
import sys

def main():
    # Silent Mode Launcher
    
    # Determine Execution Path
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Locate app_ui.py
    # 1. Check current folder
    target_file = "app_ui.py"
    script_path = os.path.join(exe_dir, target_file)
    work_dir = exe_dir
    
    if not os.path.exists(script_path):
        # 2. Check parent folder (Project Root)
        parent_dir = os.path.dirname(exe_dir)
        script_path_parent = os.path.join(parent_dir, target_file)
        
        if os.path.exists(script_path_parent):
            script_path = script_path_parent
            work_dir = parent_dir
        else:
            # Fatal Error: Cannot find app
            # Show a message box since we have no console
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"Arquivo '{target_file}' nao encontrado!\nCertifique-se de que o executavel esta na pasta do projeto.", "Erro Fatal - Monarca ABC", 0x10)
            sys.exit(1)
            
    # Change to project dir
    os.chdir(work_dir)
    
    # Prepare Command
    cmd = ["streamlit", "run", "app_ui.py", "--global.developmentMode=false"]
    
    # Execution Flags to hide window
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    try:
        # Popen ensures it runs independent of the launcher
        subprocess.Popen(
            cmd, 
            shell=True,
            cwd=work_dir,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
            # creationflags can be added if shell=False, but shell=True usually handles path implementation better for 'streamlit' command alias
        )
    except Exception as e:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Falha ao iniciar aplicacao:\n{e}", "Erro - Monarca ABC", 0x10)

if __name__ == '__main__':
    main()
