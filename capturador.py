import cv2
import base64
import time

frame_file = "frame_compartido.b64"
cap = cv2.VideoCapture(0)

print("[Capturador] Iniciado...")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[Capturador] ERROR en cámara")
        time.sleep(0.1)
        continue
    
    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    frame_b64 = base64.b64encode(buffer).decode()
    
    with open(frame_file, "w") as f:
        f.write(frame_b64)
    
    time.sleep(0.033)  # ~30 FPS