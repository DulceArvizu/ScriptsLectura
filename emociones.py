import cv2
from fer import FER
import csv
from datetime import datetime
import base64
import numpy as np
import os
import time

detector = FER()

traduccion = {
    "angry": "enojado",
    "disgust": "disgusto",
    "fear": "miedo",
    "happy": "feliz",
    "sad": "triste",
    "surprise": "sorpresa",
    "neutral": "neutral"
}

frame_file = "frame_compartido.b64"

nombre_csv = f"emociones_{datetime.now().strftime('%d%m_%H%M')}.csv"
with open(nombre_csv, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["contador", "timestamp", "emocion_principal", "confianza", "segunda_emocion", "confianza_segunda"])

contador = 1
frame_prev = ""
ultimo_guardado = time.time()

print("[Emociones] Iniciado (modo archivo)...")

while True:
    try:
        if not os.path.exists(frame_file):
            time.sleep(0.01)
            continue
        
        with open(frame_file, "r") as f:
            frame_b64 = f.read().strip()
        
        if not frame_b64 or frame_b64 == frame_prev:
            time.sleep(0.01)
            continue
        
        frame_prev = frame_b64
        frame = cv2.imdecode(np.frombuffer(base64.b64decode(frame_b64), np.uint8), cv2.IMREAD_COLOR)
        
        if frame is None:
            print("[Emociones] Frame inválido")
            continue
        
        print(f"[{contador}] Detectando emociones...")
        emociones = detector.detect_emotions(frame)
        
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not emociones:
            emocion_guardada = "No detectado"
            confianza_guardada = 0
            emocion2_guardada = "No detectado"
            confianza2_guardada = 0
            print(f"[{contador}] No detectado")
        else:
            data = emociones[0]["emotions"]
            orden = sorted(data.items(), key=lambda x: x[1], reverse=True)
            (e1, c1), (e2, c2) = orden[:2]
            emocion_guardada = traduccion[e1]
            confianza_guardada = c1
            emocion2_guardada = traduccion[e2]
            confianza2_guardada = c2
            print(f"[{contador}] {traduccion[e1]} ({c1:.2f})")
        
        # Guardar datos cada 1 segundo
        tiempo_actual = time.time()
        if tiempo_actual - ultimo_guardado >= 1.0:
            with open(nombre_csv, "a", newline="", encoding="utf-8") as f:
                f.write(f"{contador},{ts},{emocion_guardada},{confianza_guardada:.2f},{emocion2_guardada},{confianza2_guardada:.2f}\n")
            contador += 1
            ultimo_guardado = tiempo_actual
        
    except Exception as e:
        print(f"[Error Emociones] {e}")
        time.sleep(0.01)