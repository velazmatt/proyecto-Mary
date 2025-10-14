import cv2
import numpy as np

def nothing(x): pass

def resize_to_square(image, size=800):
    h, w = image.shape[:2]
    max_side = max(h, w)
    square = np.zeros((max_side, max_side, 3), dtype=np.uint8)
    x_offset = (max_side - w) // 2
    y_offset = (max_side - h) // 2
    square[y_offset:y_offset + h, x_offset:x_offset + w] = image
    return cv2.resize(square, (size, size), interpolation=cv2.INTER_AREA)

# 📷 Cargar imagen y preparar 
img_path = r"C:\Users\AOAL129300\OneDrive - ALPSGROUP\Documents\test\shoot_163_r_tbd.jpg"  # ← Ajusta esta ruta
img = cv2.imread(img_path)
if img is None:
    print(f"ERROR: No se pudo cargar la imagen en {img_path}\nVerifica la ruta, el nombre de archivo y que el archivo existe.")
    exit()  # Finaliza el programa si la imagen no se carga

img = resize_to_square(img, 800)
h, w = img.shape[:2]

# 🎛️ Ventana de ajustes
cv2.namedWindow("Ajustes", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Ajustes", 400, 250)
cv2.createTrackbar("Centro X", "Ajustes", w // 2, w, nothing)
cv2.createTrackbar("Centro Y", "Ajustes", h // 2, h, nothing)
cv2.createTrackbar("Radio Interno", "Ajustes", 100, min(h, w) // 2, nothing)
cv2.createTrackbar("Radio Externo", "Ajustes", 200, min(h, w) // 2, nothing)
cv2.createTrackbar("Umbral binarización", "Ajustes", 127, 255, nothing)
cv2.createTrackbar("Brillo ROI", "Ajustes", 50, 100, nothing)  # 50 = neutro

while True:
    # ↔ Leer parámetros
    cx = cv2.getTrackbarPos("Centro X", "Ajustes")
    cy = cv2.getTrackbarPos("Centro Y", "Ajustes")
    r_in = cv2.getTrackbarPos("Radio Interno", "Ajustes")
    r_out = cv2.getTrackbarPos("Radio Externo", "Ajustes")
    umbral = cv2.getTrackbarPos("Umbral binarización", "Ajustes")
    brillo = cv2.getTrackbarPos("Brillo ROI", "Ajustes") - 50
    centro = (cx, cy)

    # 🌀 Crear máscara tipo anillo
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, centro, r_out, 255, -1)
    cv2.circle(mask, centro, r_in, 0, -1)

    # 🔆 Ajuste de brillo
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h_, s_, v_ = cv2.split(hsv)
    v_[mask == 255] = np.clip(v_[mask == 255] + brillo, 0, 255)
    hsv_mod = cv2.merge((h_, s_, v_))
    img_brillo = cv2.cvtColor(hsv_mod, cv2.COLOR_HSV2BGR)

    # ⚫ Binarizar dentro del ROI
    gray = cv2.cvtColor(img_brillo, cv2.COLOR_BGR2GRAY)
    zona_roi = cv2.bitwise_and(gray, gray, mask=mask)
    _, binaria_roi = cv2.threshold(zona_roi, umbral, 255, cv2.THRESH_BINARY)

    # 🔍 Detectar contornos y jerarquía
    contornos, jerarquia = cv2.findContours(binaria_roi, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # 🖼️ Imagen para visualizar resultados
    img_contornos = img.copy()

    subcontornos = 0  # contador total

    for i, cnt in enumerate(contornos):
        cv2.drawContours(img_contornos, [cnt], -1, (0, 255, 0), 2)  # verde

        hijo_idx = jerarquia[0][i][2]
        while hijo_idx != -1:
            cnt_hijo = contornos[hijo_idx]
            M = cv2.moments(cnt_hijo)
            if M["m00"] != 0:
                cx_h = int(M["m10"] / M["m00"])
                cy_h = int(M["m01"] / M["m00"])
                cv2.circle(img_contornos, (cx_h, cy_h), 4, (0, 255, 255), -1)  # amarillo
                cv2.putText(img_contornos, "Sub", (cx_h + 5, cy_h - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                subcontornos += 1
            hijo_idx = jerarquia[0][hijo_idx][0]  # siguiente hermano

    # 🧭 Dibujar ROI
    cv2.circle(img_contornos, centro, r_out, (0, 255, 0), 2)
    cv2.circle(img_contornos, centro, r_in, (0, 0, 255), 2)

    # 🧮 Mostrar conteo total de subcontornos
    cv2.putText(img_contornos, f"Subcontornos detectados: {subcontornos}", (30, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    # ▶ Mostrar imágenes
    cv2.imshow("Contornos y subcontornos", img_contornos)
    cv2.imshow("Binarización ROI", binaria_roi)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()                                                                                                                                                                                      