import cv2
import mediapipe as mp
import csv
from datetime import datetime
import base64
import numpy as np
import os
import time

# Usar archivo temporal en lugar de ZMQ
frame_file = "frame_compartido.b64"

mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True)

nombre_csv = f"eyetracking_{datetime.now().strftime('%d%m_%H%M')}.csv"
with open(nombre_csv, "w", newline="", encoding="utf-8") as f:
    csv.writer(f).writerow(["contador", "timestamp", "direccion", "centro_acum", "izquierda_acum", "derecha_acum", "arriba_acum", "abajo_acum"])

contador = 1
calibrado = False
samples = 0
CALIB_MAX = 25
base_x = 0.0
base_y = 0.0
ultimo_guardado = time.time()
centro_acum = 0
izquierda_acum = 0
derecha_acum = 0
arriba_acum = 0
abajo_acum = 0

print("[EyeTracking] Iniciado (modo archivo)...")

def obtener_direccion(face):
    global calibrado, samples, base_x, base_y
    lm = face.landmark
    iris_x = (lm[468].x + lm[473].x) / 2
    iris_y = (lm[468].y + lm[473].y) / 2
    eye_left = lm[33].x
    eye_right = lm[263].x
    eye_top = lm[159].y
    eye_bottom = lm[145].y
    w = eye_right - eye_left
    h = eye_bottom - eye_top
    
    if w == 0 or h == 0:
        return "desconocido"
    
    rx = (iris_x - eye_left) / w
    ry = (iris_y - eye_top) / h
    
    if not calibrado:
        base_x += rx
        base_y += ry
        samples += 1
        print(f"[Calibración] {samples}/{CALIB_MAX}")
        if samples >= CALIB_MAX:
            base_x /= samples
            base_y /= samples
            calibrado = True
            print(f"[✓] CALIBRACIÓN COMPLETA - Base: ({base_x:.3f}, {base_y:.3f})")
        return "centro"
    
    dx = rx - base_x
    dy = ry - base_y
    
    print(f"[Ojo] rx={rx:.3f}, ry={ry:.3f} | dx={dx:.3f}, dy={dy:.3f}")
    
    threshold_simple = 0.05      # Para direcciones simples (arriba, abajo, etc)
    threshold_diagonal = 0.03    # Para diagonales (más sensibles)
    
    # Primero intentar detectar diagonales
    if dx < -threshold_diagonal and dy < -threshold_diagonal:
        return "arriba_izquierda"
    elif dx > threshold_diagonal and dy < -threshold_diagonal:
        return "arriba_derecha"
    elif dx < -threshold_diagonal and dy > threshold_diagonal:
        return "abajo_izquierda"
    elif dx > threshold_diagonal and dy > threshold_diagonal:
        return "abajo_derecha"
    # Luego direcciones simples
    elif abs(dx) < threshold_simple and abs(dy) < threshold_simple:
        return "centro"
    elif dx < -threshold_simple:
        return "izquierda"
    elif dx > threshold_simple:
        return "derecha"
    elif dy < -threshold_simple:
        return "arriba"
    elif dy > threshold_simple:
        return "abajo"
    
    return "centro"

frame_prev = ""
while True:
    try:
        if not os.path.exists(frame_file):
            time.sleep(0.01)
            continue
        
        with open(frame_file, "r") as f:
            frame_b64 = f.read().strip()
        
        if not frame_b64 or frame_b64 == frame_prev:
            time.sleep(0.005)
            continue
        
        frame_prev = frame_b64
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(frame_b64), np.uint8), cv2.IMREAD_COLOR)
        
        if frame is None:
            continue
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)
        
        direccion = "desconocido"
        if res.multi_face_landmarks:
            direccion = obtener_direccion(res.multi_face_landmarks[0])
        
        # Actualizar contadores acumulativos según la dirección
        if direccion == "centro":
            centro_acum += 1
        elif direccion == "izquierda":
            izquierda_acum += 1
        elif direccion == "derecha":
            derecha_acum += 1
        elif direccion == "arriba":
            arriba_acum += 1
        elif direccion == "abajo":
            abajo_acum += 1
        elif direccion == "arriba_izquierda":
            arriba_acum += 1
            izquierda_acum += 1
        elif direccion == "arriba_derecha":
            arriba_acum += 1
            derecha_acum += 1
        elif direccion == "abajo_izquierda":
            abajo_acum += 1
            izquierda_acum += 1
        elif direccion == "abajo_derecha":
            abajo_acum += 1
            derecha_acum += 1
        
        # Guardar datos cada 1 segundo
        tiempo_actual = time.time()
        if tiempo_actual - ultimo_guardado >= 1.0:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(nombre_csv, "a", newline="", encoding="utf-8") as f:
                f.write(f"{contador},{ts},{direccion},{centro_acum},{izquierda_acum},{derecha_acum},{arriba_acum},{abajo_acum}\n")
            
            contador += 1
            print(f"[{contador}] {direccion} | Centro:{centro_acum} Izq:{izquierda_acum} Der:{derecha_acum} Arr:{arriba_acum} Aba:{abajo_acum}")
            
            # Resetear contadores acumulativos para el siguiente segundo
            centro_acum = 0
            izquierda_acum = 0
            derecha_acum = 0
            arriba_acum = 0
            abajo_acum = 0
            
            ultimo_guardado = tiempo_actual
        
    except Exception as e:
        print(f"[Error] {e}")
        time.sleep(0.01)