import subprocess
import time
import os

# Usa los Python de los ambientes virtuales
python_eye = r"C:\Users\dulce\LECTURA\env_eye\Scripts\python.exe"
python_emociones = r"C:\Users\dulce\LECTURA\env_emociones\Scripts\python.exe"

script_captura = r"C:\Users\dulce\LECTURA\capturador.py"
script_emociones = r"C:\Users\dulce\LECTURA\emociones.py"
script_eye = r"C:\Users\dulce\LECTURA\eyetracking.py"


print("[RunAll] Iniciando capturador…")
proc_cap = subprocess.Popen([python_eye, script_captura])
time.sleep(1)

print("[RunAll] Iniciando eye tracking…")
proc_eye = subprocess.Popen([python_eye, script_eye])

print("[RunAll] Iniciando emociones…")
proc_emo = subprocess.Popen([python_emociones, script_emociones])

print("[RunAll] Todo corriendo. Press Ctrl+C para detener.")

try:
    proc_emo.wait()
    proc_eye.wait()
    proc_cap.wait()
except KeyboardInterrupt:
    print("\n[RunAll] Deteniendo...")
    proc_cap.terminate()
    proc_eye.terminate()
    proc_emo.terminate()