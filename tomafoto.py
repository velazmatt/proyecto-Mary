import cv2
import os

CAMERA_LEFT_INDEX=0
CAMERA_RIGHT_INDEX=2
OUTPUT_DIR = r'data'
os.makedirs(OUTPUT_DIR,exist_ok=True)

RES_WIDTH=2592
RES_HEIGHT=1944

def get_next_index():
    archivos = os.listdir(OUTPUT_DIR)
    indices=[]
    for archivo in archivos:
        if archivo.endswith(".jpg"):
            partes=archivo.split("_")
            if len(partes)>=2:
                try:
                    indices.append(int(partes[1]))
                except:
                    continue
    return max(indices,default=0)+1

cap_izq = cv2.VideoCapture(CAMERA_LEFT_INDEX,cv2.CAP_V4L2)
cap_der = cv2.VideoCapture(CAMERA_RIGHT_INDEX,cv2.CAP_V4L2)

if not cap_izq.isOpened() or not cap_der.isOpened():
    print("No se pudo abrir una o ambas camaras.")
    cap_izq.release()
    cap_der.release()
    exit()

cap_izq.set(cv2.CAP_PROP_FRAME_WIDTH,RES_WIDTH)
cap_izq.set(cv2.CAP_PROP_FRAME_HEIGHT,RES_HEIGHT)


cap_der.set(cv2.CAP_PROP_FRAME_WIDTH,RES_WIDTH)
cap_der.set(cv2.CAP_PROP_FRAME_HEIGHT,RES_HEIGHT)

print("Presiona 'c' para capturar, 'q' para salir")

while True:
    ret_izq,frame_izq=cap_izq.read()
    ret_der,frame_der=cap_der.read()
    
    if not ret_izq or not ret_der:
        print("Error al capturar imagen")
        break
    
    cv2.imshow("Camara izquierda",frame_izq)
    cv2.imshow("Camara derecha",frame_der)
    
    key=cv2.waitKey(1) & 0xFF
    
    if key==ord('c'):
        index=get_next_index()
        filename_izq=os.path.join(OUTPUT_DIR,f"shoot_{index:03d}_l_tbd.jpg")
        filename_der=os.path.join(OUTPUT_DIR,f"shoot_{index:03d}_r_tbd.jpg")
        cv2.imwrite(filename_izq,frame_izq)
        cv2.imwrite(filename_der,frame_der)
        print(f"Captura guardada:{filename_izq},{filename_der}")
    elif key==ord('q'):
        break

cap_izq.release()
cap_der.release()
cv2.destroyAllWindows()