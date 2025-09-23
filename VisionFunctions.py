import cv2
import numpy as np
import math
from enum import Enum



class Region():
    Figures = Enum('Figures', ['RECTANGLE', 'CIRCLE', 'POLY'])
    def __init__(self, figure, coord1: tuple, coord2:tuple, radius, region_img, parent_img):
        self.fig_type = figure
        if self.fig_type == Region.Figures.RECTANGLE:
            self.pt1 = coord1

            self.pt2 = coord2
        elif self.fig_type == Region.Figures.CIRCLE:
            self.center_point = coord1
            self.radius = radius
        self.region_img = region_img
        self.parent_img = parent_img

class VisionSystem():
    
    def __init__(self, DeviceType: str, DeviceAddress: int, DeviceName: str):
        self.frameToShow = None
        self.RegionsAdded = []
        self.LastImage = None
        self.cir_shape = None
        if DeviceType is not None and DeviceAddress is not None:
            self.DeviceType = DeviceType
            self.deviceAddress = int(DeviceAddress)
            if not self._OpenDevice(self.deviceAddress):
                self.initOK =  False
                return
            self.setResolution()
        self.threshold_value = 180

        self.initOK = True
        self.savedImages = 0
        self.DeviceName = DeviceName
    
    def setResolution(self, width=3840, height=2160):
        width = 2592
        height = 1944
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def _OpenDevice(self, idx: int) -> bool:
        try:
            self.cap = cv2.VideoCapture(idx)
            if not self.cap.isOpened(): 
                return False
            else:
                return True
        except:
            print("Camera Not found or out of index")
            return False
    
    def trigger(self) -> cv2.typing.MatLike:
        if not self.initOK:
            return np.ones((2592,1944,3), dtype=np.uint8)*255
        while True:
            ret, frame = self.cap.read()
            if ret:
                break       
            else:
                continue
        # frame = frame[] 
        # img = cv2.resize(frame, (1200,900), interpolation=cv2.INTER_LINEAR)
        self.frameToShow = frame
        # cv2.imwrite(f"C:\\Users\\aoal148080\\Desktop\\iMAGES\\img_{self.savedImages}.jpg", img)
        self.savedImages += 1
        # rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame
    
    def Open_image(self, Filename: str) -> cv2.typing.MatLike:
        frame = cv2.imread(Filename, cv2.IMREAD_UNCHANGED)      
        # img = cv2.resize(frame, (1200,900), interpolation=cv2.INTER_LINEAR)
        self.frameToShow = frame.copy()
        # rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return frame
    
    def draw_circle(self, fill : bool = False) -> cv2.typing.MatLike:
        img  =  self.frameToShow.copy()
        coord_1 = [592, 427]
        radius = 239
        self.cir_shape = img[coord_1[1]-radius:coord_1[1]+radius, coord_1[0]-radius:coord_1[0]+radius]
        self.RegionsAdded.append(Region(Region.Figures.CIRCLE, coord1=coord_1, coord2=None, radius=radius, region_img=self.cir_shape.copy(), parent_img=img.copy()))
        self.LastImage = img.copy()                
        img = cv2.circle(img, (coord_1[0], coord_1[1]), int(radius), (0,255,0), 2)
        if fill:
            self.fill_circle(img, coord_1, radius, (0,0,0))
        return img

    def apply_thresh(self, img, debug: bool):
        shaped_region = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  
        _, shaped_region = cv2.threshold(shaped_region, self.threshold_value, 255, cv2.THRESH_BINARY)
        if debug:
            cv2.imshow("Thresholded", cv2.resize(shaped_region, (1200, 900), cv2.INTER_LINEAR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        pixel_count = cv2.countNonZero(shaped_region)
        shaped_region = cv2.cvtColor(shaped_region, cv2.COLOR_GRAY2BGR)
        return pixel_count, shaped_region
    
    def hsv_analysis(self, img: cv2.typing.MatLike, debug:bool = False) -> tuple[int, cv2.typing.MatLike]:
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # # define range of white color in HSV
        # # change it according to your need !
        lower_white = np.array([0,0,255-self.threshold_value])
        upper_white = np.array([179,self.threshold_value,255])

        # Get L channel From img
        # Schannel = hsv_img[:,1,:]
        # Create mask: change 250 to lower numbers to include more values as white 
        mask = cv2.inRange(hsv_img, lower_white, upper_white)
        pixel_count =  cv2.countNonZero(mask)
        # Threshold the HSL image to get only white colors
        # mask = cv2.inRange(hsv_img, lower_white, upper_white)
        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(img,img, mask= mask)
        if debug:
            cv2.imshow("HSL", cv2.resize(hsv_img, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("mask", cv2.resize(mask, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("res", cv2.resize(res, (1200, 900), cv2.INTER_LINEAR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return pixel_count, hsv_img 

    def HSL_analysis(self, img: cv2.typing.MatLike, debug: bool = False) -> tuple[int, cv2.typing.MatLike]:
        hsl_img = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)
        
        # Get L channel From img
        Lchannel = hsl_img[:,:,1]
        # Create mask: change 250 to lower numbers to include more values as white 
        mask = cv2.inRange(Lchannel, self.threshold_value, 255)
        pixel_count =  cv2.countNonZero(mask)
        # Threshold the HSL image to get only white colors
        # mask = cv2.inRange(hsv_img, lower_white, upper_white)
        # Bitwise-AND mask and original image
        res = cv2.bitwise_and(img,img, mask= mask)
        if debug:
            cv2.imshow("HSL", cv2.resize(hsl_img, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("mask", cv2.resize(mask, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("res", cv2.resize(res, (1200, 900), cv2.INTER_LINEAR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return pixel_count, hsl_img 
        
    def fill_circle(self, img: cv2.typing.MatLike, coord_1: tuple[int], radius: int, filling : tuple[int] = (0,0,0)) -> cv2.typing.MatLike:
        x = coord_1[0]
        y = coord_1[1]
        # pt2x = x + math.sqrt((radius*radius)-(i*i))
        for i in range(0, radius, 5):
            pt2x_1 = int(x + math.sqrt(pow(radius, 2) - pow(i, 2)))
            pt2x_2 = int(x - math.sqrt(pow(radius, 2) - pow(i, 2)))
            img=cv2.line(img, (pt2x_2-1, y+i), (pt2x_1+1, y+i), filling, 5)
            img=cv2.line(img, (pt2x_1+1, y-i), (pt2x_2-1, y-i), filling, 5)
        return img
    
    def HSL_Leak_Analysis(self, img: cv2.typing.MatLike, Lmin:int = 0, Lmax:int = 255, Smin:int = 0, Smax: int = 255, debug: bool = False) -> tuple[int, cv2.typing.MatLike]:
        hls_img = cv2.cvtColor(img, cv2.COLOR_BGR2HLS_FULL)
        
        white_min = np.array([0, Lmin, Smin], np.uint8)
        white_max = np.array([255, Lmax, Smax], np.uint8)
        maskwhite = cv2.inRange(hls_img, white_min, white_max)
        maskwhite = cv2.bitwise_not(maskwhite)
        res = cv2.bitwise_and(img,img, mask= maskwhite)
        pixel_count = cv2.countNonZero(maskwhite) 
        if pixel_count<=5:
            pixel_count = pixel_count*5
        elif pixel_count > 5 and pixel_count <= 10:
            pixel_count = pixel_count*4
        elif pixel_count > 10 and pixel_count <= 15:
            pixel_count = pixel_count*3
        elif pixel_count > 15 and pixel_count <= 30:
            pixel_count = pixel_count*2
        else:
            pixel_count = pixel_count*2

        contours, hierarchy = cv2.findContours(maskwhite.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(img, contours, -1, (0,255,0), 1, lineType=1, hierarchy=hierarchy)
        for contour in contours:
            x, y, xx, yy= cv2.boundingRect(contour)
            img = cv2.circle(img, (int(x), int(y)), 20, (0,255,0), 2)
            
        
        if debug:
            # img = cv2.circle(img, center, 10, (0,255,0), 1)
            cv2.imshow("contours", cv2.resize(img, (1200,900), cv2.INTER_LINEAR))
            cv2.imshow("HSL", cv2.resize(hls_img, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("mask", cv2.resize(maskwhite, (1200, 900), cv2.INTER_LINEAR))
            cv2.imshow("res", cv2.resize(res, (1200, 900), cv2.INTER_LINEAR))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        return pixel_count, img 

    def detect_leak_blue(self, img: cv2.typing.MatLike,Smin: int = 0, Smax: int = 140, Vmin: int = 120, Vmax: int = 255):
        Color_min = np.array([85,Smin,Vmin], np.uint8)
        Color_max = np.array([150,Smax,Vmax], np.uint8)

        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        maskblue = cv2.inRange(hsv_img, Color_min, Color_max)
        resultblue = cv2.bitwise_and(hsv_img, hsv_img, mask=maskblue)
        pixelsblue = cv2.countNonZero(maskblue)

        result = cv2.cvtColor(resultblue, cv2.COLOR_HSV2BGR)

        contours, hierarchy = cv2.findContours(maskblue.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(img, contours, -1, (0,255,0), 1, lineType=1, hierarchy=hierarchy)
        for contour in contours:
            x, y, _, _ = cv2.boundingRect(contour)
            img = cv2.circle(img, (int(x), int(y)), 20, (0,255,0), 2)
            
        
        pixels = pixelsblue
        # result = cv2.add(resultblue, resultwhite)
        return pixels, img


    def detect_leak_red(self, img: cv2.typing.MatLike, Smin:int = 0, Smax: int = 175, Vmin: int = 130, Vmax:int = 255):
        # Color_min = np.array([0,Smin,Vmin], np.uint8)
        # Color_max = np.array([15,Smax,Vmax], np.uint8)

        # hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # maskred = cv2.inRange(hsv_img, Color_min, Color_max)
        # resultred = cv2.bitwise_and(hsv_img, hsv_img, mask=maskred)
        # pixelsred = cv2.countNonZero(maskred)

        Red1_min = np.array([0,Smin,Vmin], np.uint8)
        Red1_max = np.array([15,Smax,Vmax], np.uint8)
        Red2_min = np.array([165,Smin,Vmin], np.uint8)
        Red2_max = np.array([179,Smax,Vmax], np.uint8)

        # Create HSV Image and threshold into a range.
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv_img, Red1_min, Red1_max)
        mask2 = cv2.inRange(hsv_img, Red2_min, Red2_max)
        maskred = cv2.bitwise_or(mask1, mask2)
        pixels = cv2.countNonZero(maskred)
        output = cv2.bitwise_and(img,img, mask= maskred)
        
        contours, hierarchy = cv2.findContours(maskred.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # cv2.drawContours(img, contours, -1, (0,255,0), 1, lineType=1, hierarchy=hierarchy)
        for contour in contours:
            x, y, _, _ = cv2.boundingRect(contour)
            img = cv2.circle(img, (int(x), int(y)), 20, (0,255,0), 2)
            

        output = cv2.cvtColor(output, cv2.COLOR_HSV2BGR)
        
        return pixels, img

    def extract_red_color(self, img: cv2.typing.MatLike, positive: bool = True) -> cv2.typing.MatLike:
        orange_min = np.array([0, 0, 0], np.uint8)
        orange_max = np.array([10, 255, 255], np.uint8)
        red_min = np.array([170, 0, 120], np.uint8)
        red_max = np.array([179, 255, 255], np.uint8)
        

        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        orange_mask = cv2.inRange(hsv_img, orange_min, orange_max)
        red_mask = cv2.inRange(hsv_img, red_min, red_max)
        res1 = cv2.bitwise_and(hsv_img, hsv_img, mask=orange_mask)
        res2 = cv2.bitwise_and(hsv_img, hsv_img, mask=red_mask)
        result = cv2.bitwise_or(res1, res2)
        if not positive:
            result = cv2.bitwise_not(result)

        # cv2.imshow('org mask', res1)
        # cv2.imshow('red mask', res2)
        # cv2.imshow('result', result)
        # cv2.waitKey()
        return result

    def extract_blue_color(self, img: cv2.typing.MatLike, positive: bool = True) -> cv2.typing.MatLike:
        blue_min = np.array([80, 50, 50], np.uint8)
        blue_max = np.array([140, 255, 255], np.uint8)

        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        blue_mask = cv2.inRange(hsv_img, blue_min, blue_max)
        
        result = cv2.bitwise_and(hsv_img, hsv_img, mask=blue_mask)
        
        if not positive:
            result = cv2.bitwise_not(result)

        # cv2.imshow('blue mask', blue_mask)
        # cv2.imshow('resultblue', result)

        # cv2.waitKey() 

        return result


    def extract_composite_circle(self,img: cv2.typing.MatLike, center_point: tuple[int], radius1: int, radius2: int) -> cv2.typing.MatLike:
        xc = center_point[1]
        yc = center_point[0]
        mask1 = np.ones_like(img)
        mask1 = cv2.circle(mask1, (yc,xc), radius1, (255,255,255), -1)
        mask2 = np.ones_like(img)
        mask2 = cv2.circle(mask2, (yc,xc), radius2, (255,255,255), -1)

        background = np.zeros_like(img)

        # subtract masks and make into single channel
        mask = cv2.subtract(mask2, mask1)

        # put mask into alpha channel of input
        result = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
        result[:, :, 3] = mask[:,:,0]
        i = 0
        j = 0
        for column in result :
            for pixel in column:
                if pixel[3] == 0 :
                    img[i,j] = background[i,j]
                j+=1
                if j == len(column):
                    j=0
            i+=1
        self.cir_shape = img[center_point[1]-radius2:center_point[1]+radius2, center_point[0]-radius2:center_point[0]+radius2]
        return img
    
    def extract_composite_circle_bitwise(self,img: cv2.typing.MatLike, center_point: tuple[int], radius1: int, radius2: int, debug: bool = False) -> cv2.typing.MatLike:
        # Definir le centro y radio de los circulos
        center = center_point

        #< Modificando estos valores se aumenta o disminute el grosor de la mascara en anillo > : Manipular exteriormente
        outer_radius = radius2 # Example: Radio exterior
        inner_radius = radius1# Example: Radio interior


        # Crear la mascara con las mismas dimenciones que la imagen, iniciarla en  0 (black)  - 
        mask = np.zeros(img.shape[:2], dtype=np.uint8)

        # Dibujar el circulo exterior (LLeno con color blanco)
        cv2.circle(mask, center, outer_radius, 255, thickness=-1)

        # Dibujar circulo interior  (lleno con color negro)
        cv2.circle(mask, center, inner_radius, 0, thickness=-1)

        # Aplicar la mascara a la imagen ingresada, 
        masked_img = cv2.bitwise_and(img, img, mask=mask)

        # Mostrar resultado
        if debug:
            cv2.imshow('Original img', img)
            cv2.imshow('Mask', mask)
            cv2.imshow('Ring Shaped ROI', masked_img)
            cv2.waitKey(1)
            cv2.destroyAllWindows()
        self.cir_shape = img[center_point[1]-radius2:center_point[1]+radius2, center_point[0]-radius2:center_point[0]+radius2]
        return masked_img
        
    def img_denoising_colored(self, img: cv2.typing.MatLike) -> cv2.typing.MatLike:
        dst = cv2.fastNlMeansDenoisingColored(img,None,10,10,7,21)
        return dst
    
    def ORB_feature_extractor(self, img: cv2.typing.MatLike) -> tuple:
        """
        Return the KeyPoints and a MatLike in tuple
        """
        orb = cv2.ORB_create()
        # find the keypoints with ORB
        kp = cv2.ORB.detect(orb,img,None)
        
        # compute the descriptors with ORB
        kp, des = cv2.ORB.compute(orb,img, kp)
        
        # draw only keypoints location,not size and orientation
        img2 = cv2.drawKeypoints(img, kp, None, color=(0,255,0), flags=0)
        return (kp, img2)
    
    def detectar_muescas(self, image: cv2.typing.MatLike,
                    umbral_binario: int = 10,
                    umbral_muesca: int = 20,
                    vecindad: int = 15) -> int:
        if vecindad < 2:
            vecindad = 2

        original = cv2.blur(image, (7, 7))
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, umbral_binario, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        total_notches = 0

        for cnt in contours:
            if len(cnt) < 20 or cv2.contourArea(cnt) < 300:
                continue

            pts = cnt[:, 0, :]
            deviations = np.zeros(len(pts))

            for i in range(vecindad, len(pts) - vecindad):
                pt1 = pts[i - vecindad]
                pt2 = pts[i + vecindad]
                line_vec = pt2 - pt1
                norm = np.linalg.norm(line_vec)
                if norm == 0:
                    continue
                line_unit = line_vec / norm
                p = pts[i]
                vec = p - pt1
                proj_len = np.dot(vec, line_unit)
                proj_point = pt1 + proj_len * line_unit
                deviation_vec = p - proj_point
                deviation = np.linalg.norm(deviation_vec)
                cross = line_unit[0] * deviation_vec[1] - line_unit[1] * deviation_vec[0]
                if cross < 0:
                    deviation = -deviation
                deviations[i] = deviation

            notch_indices = np.where(deviations < -umbral_muesca)[0]
            total_notches += len(notch_indices)

        return total_notches

    def detectar_manchas(
        img_good: np.ndarray, img_bad: np.ndarray,
        h1_low: int, h1_high: int, h2_low: int, h2_high: int,
        s_low: int, s_high: int, v_low: int, v_high: int,
        diff_thresh: int = 5
    ) -> tuple[np.ndarray, int]:
        # Validar que las im�genes existen
        if img_good is None or img_bad is None:
            raise ValueError("Una o ambas im�genes est�n vac�as (None).")

        # Convertir a HSV
        hsv_bad = cv2.cvtColor(img_bad, cv2.COLOR_BGR2HSV)

        # Crear m�scara roja combinando dos rangos de tonos
        mask_red1 = cv2.inRange(hsv_bad, (h1_low, s_low, v_low), (h1_high, s_high, v_high))
        mask_red2 = cv2.inRange(hsv_bad, (h2_low, s_low, v_low), (h2_high, s_high, v_high))
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Comparar canales rojos
        red_good = img_good[:, :, 2]
        red_bad = img_bad[:, :, 2]

        red_good_masked = cv2.bitwise_and(red_good, red_good, mask=mask_red)
        red_bad_masked = cv2.bitwise_and(red_bad, red_bad, mask=mask_red)

        # Calcular diferencia
        diff = red_good_masked.astype(np.int16) - red_bad_masked.astype(np.int16)
        diff[diff < diff_thresh] = 0
        diff[diff >= diff_thresh] = 255
        diff = diff.astype(np.uint8)

        # Quitar ruido
        kernel = np.ones((3, 3), np.uint8)
        clean_diff = cv2.morphologyEx(diff, cv2.MORPH_OPEN, kernel, iterations=1)

        # Buscar contornos
        contours, _ = cv2.findContours(clean_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = img_bad.copy()
        manchas_detectadas = 0

        # Dibujar las manchas
        for cnt in contours:
            if cv2.contourArea(cnt) > 1:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.circle(result, (cx, cy), 10, (0, 0, 255), 2)
                    cv2.putText(result, "< Mancha", (cx + 15, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    manchas_detectadas += 1

        return result, manchas_detectadas
    
    def contar_subcontornos_en_roi(img, cx, cy, r_in, r_out, umbral_bin, brillo_roi):
        h, w = img.shape[:2]
        centro = (cx, cy)

        # 🌀 Crear máscara tipo anillo
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(mask, centro, r_out, 255, -1)
        cv2.circle(mask, centro, r_in, 0, -1)

        # 🔆 Ajuste de brillo en HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_, s_, v_ = cv2.split(hsv)
        v_[mask == 255] = np.clip(v_[mask == 255] + brillo_roi, 0, 255)
        hsv_mod = cv2.merge((h_, s_, v_))
        img_brillo = cv2.cvtColor(hsv_mod, cv2.COLOR_HSV2BGR)

        # ⚫ Binarización dentro del ROI
        gray = cv2.cvtColor(img_brillo, cv2.COLOR_BGR2GRAY)
        zona_roi = cv2.bitwise_and(gray, gray, mask=mask)
        _, binaria_roi = cv2.threshold(zona_roi, umbral_bin, 255, cv2.THRESH_BINARY)

        # 🔍 Detectar contornos con jerarquía completa
        contornos, jerarquia = cv2.findContours(binaria_roi, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if jerarquia is None:
            return 0  # No se detectaron contornos

        # 🧮 Contar subcontornos (aquellos con un padre)
        subcontornos = sum(1 for i in range(len(contornos)) if jerarquia[0][i][3] != -1)

        return subcontornos
    
    def resize_to_square(image, size=800):
        h, w = image.shape[:2]
        max_side = max(h, w)
        
        # Crear lienzo cuadrado con fondo negro
        square = np.zeros((max_side, max_side, 3), dtype=np.uint8)
        
        # Centrar la imagen original
        x_offset = (max_side - w) // 2
        y_offset = (max_side - h) // 2
        square[y_offset:y_offset + h, x_offset:x_offset + w] = image

        # Redimensionar al tamaño deseado
        return cv2.resize(square, (size, size), interpolation=cv2.INTER_AREA)
    
    