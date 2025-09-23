import sys
import os
import cv2
import asyncio
import datetime
from time import sleep
import numpy as np
import socket

from Phidget22.Phidget import *
from Phidget22.Devices.DigitalInput import *
from Phidget22.Devices.DigitalOutput import *

from GlobalFunctions import GlobalFunctions
from VisionFunctions import VisionSystem
import Models

from ui_mainwindow_D_2 import Ui_MainWindow
from ui_ScanUser import Ui_DialogScanUser
from ui_LogoutDialog import Ui_LogOutDialog
from ui_SaturationEdit_800x480 import Ui_ParameterEdit
from ui_PasswordDialog import Ui_DialogPassword
from ui_maskedit_800x480 import Ui_MaskEdit

from PySide6.QtCore import (Qt, QTimer )
from PySide6.QtGui import (QImage, QPixmap, QColor, QScreen)
from PySide6.QtWidgets import (QMainWindow, QApplication, QDialog, QWidget, QListWidgetItem,
                            QMessageBox, QLabel, QTableWidgetItem, QListWidget )


class ColorCode():
    def __init__(self):
        self.GRAY = 1
        self.BLUE = 2
        self.GREEN = 3
        self.RED = 4

class FrmPassword(QDialog):
    def __init__(self, password):
        super().__init__()
        self.ui = Ui_DialogPassword()
        self.ui.setupUi(self)
        self.Password = password
        self.ui.buttonBox.accepted.connect(self.button_accept)
        self.ui.buttonBox.rejected.connect(self.button_reject)
        self.ui.tb_password.returnPressed.connect(self.button_accept)
        self.PasswordOK = False

    def button_accept(self):
        tbPassword = self.ui.tb_password.text()
        if tbPassword == self.Password:
            self.PasswordOK = True
            self.close()
        else:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setText("Contraseña incorrecta")
            msg.exec()
            
            


    def button_reject(self):
        self.PasswordOK = False
        self.close()
        

class FrmMaskEdit(QDialog):
    def __init__(self, parent = ..., f = ...):
        super().__init__()
        self.ui = Ui_MaskEdit()
        self.ui.setupUi(self)
        self._appLoaded = False
        self.ui.btn_accept.clicked.connect(self.button_save)
        self.ui.btn_reject.clicked.connect(self.button_cancel)
        self.ui.slider_innerRadius.valueChanged.connect(self.onSliderChanged)
        self.ui.slider_outerRadius.valueChanged.connect(self.onSliderChanged)
        self.ui.tb_xCoord.textChanged.connect(self.tb_returnKeyXcoord)
        self.ui.tb_yCoord.textChanged.connect(self.tb_returnKeyYcoord)
        self.vision = VisionSystem(None, None, None)
        self.img: cv2.typing.MatLike = None

        # self.ui.buttonBox.setMouseTracking(False)

        self.InnerRadius = 0
        self.OuterRadius = 0
        self.xCoord = 0
        self.yCoord = 0
        self._appLoaded = True

    def tb_returnKeyXcoord(self):
        if self._internalCall: 
            return
        self.xCoord = int(self.ui.tb_xCoord.text())
        self.apply_mask(self.img.copy())

    def tb_returnKeyYcoord(self):
        if self._internalCall: 
            return
        self.yCoord = int(self.ui.tb_yCoord.text())
        self.apply_mask(self.img.copy())

    def set_image(self, img: cv2.typing.MatLike, label: QLabel):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_img.shape

        qt_img = QImage(rgb_img.data, w, h, ch *w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_img))
        label.update()

    def apply_mask(self, img: cv2.typing.MatLike):
        # Set minimum and max HSV values to display
        output  = self.vision.extract_composite_circle_bitwise(img, (self.xCoord, self.yCoord), self.InnerRadius, self.OuterRadius)

        self._internalCall = True
        self.ui.tb_xCoord.setText(str(self.xCoord))
        self.ui.tb_yCoord.setText(str(self.yCoord))
        self.ui.slider_innerRadius.setValue(self.InnerRadius)
        self.ui.slider_outerRadius.setValue(self.OuterRadius)
        self._internalCall = False

        self.set_image(output, self.ui.label_img)
        
    def onSliderChanged(self):
        if not self._appLoaded: return    
        if self._internalCall: 
            return
        self.InnerRadius = self.ui.slider_innerRadius.value()
        self.OuterRadius = self.ui.slider_outerRadius.value()

        self.xCoord = int(self.ui.tb_xCoord.text())
        self.yCoord = int(self.ui.tb_yCoord.text())
        
        self.apply_mask(self.img.copy())

    def button_save(self):
        if not self._appLoaded: return
        self.save = True
        self.close()

    def button_cancel(self):
        if not self._appLoaded: return
        self.save = False
        self.close()

######################################################################################################################

class FrmAdjustParameters(QDialog):
    def __init__(self, MaxSat: int = 140, MinValue: int = 120):
        super().__init__()
        self.ui = Ui_ParameterEdit()
        self.ui.setupUi(self)
        self._appLoaded = False
        self.ui.buttonBox.accepted.connect(self.button_save)
        self.ui.buttonBox.rejected.connect(self.button_cancel)
        self.ui.sliderMaxSaturation.valueChanged.connect(self.onSliderChanged)
        self.ui.sliderMinValue.valueChanged.connect(self.onSliderChanged)
        self.ui.sliderMinSaturation.valueChanged.connect(self.onSliderChanged)
        self.ui.sliderMaxValue.valueChanged.connect(self.onSliderChanged)
        self.ui.rbBlueFeatures.toggled.connect(self.OnRadioButtonCheck)
        self.ui.rbRedFeatures.toggled.connect(self.OnRadioButtonCheck)
        self.ui.rbWhiteFeatures.toggled.connect(self.OnRadioButtonCheck)
        self.ui.rbBlueFeatures.setChecked(True)
        self.vision = VisionSystem(None, None,None)
        self.blue_MaxSat = MaxSat
        self.blue_MinValue = MinValue
        self.red_MaxSat = 0
        self.red_MinValue = 0
        self.blue_MinSat = 0
        self.blue_MaxValue = 255
        self.red_MinSat = 0
        self.red_MaxValue = 255
        self.HlsSatMin = 0
        self.HlsSatMax = 255
        self.HlsLightMin = 0
        self.HlsLightMax = 255
        self.ui.sliderMaxSaturation.setValue(MaxSat)
        self.ui.sliderMinValue.setValue(MinValue)
        self.ui.sliderMinSaturation.setValue(0)
        self.ui.sliderMaxValue.setValue(255)
        self.img: cv2.typing.MatLike = None
        self.save = False
        self.rbToggled = False
        self._appLoaded = True



    def set_image(self, img: cv2.typing.MatLike, label: QLabel):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_img.shape

        qt_img = QImage(rgb_img.data, w, h, ch *w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_img))
        label.update()

    def extract_features(self, img: cv2.typing.MatLike):
        # Set minimum and max HSV values to display
        if self.ui.rbBlueFeatures.isChecked():
            Vmin = self.blue_MinValue
            Vmax = self.blue_MaxValue
            Smin = self.blue_MinSat
            Smax = self.blue_MaxSat

            # Color_min = np.array([85,Smin,Vmin], np.uint8)
            # Color_max = np.array([150,Smax,Vmax], np.uint8)
            # # Create HSV Image and threshold into a range.
            # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # mask = cv2.inRange(hsv, Color_min, Color_max)
            # pixels = cv2.countNonZero(mask)
            # output = cv2.bitwise_and(img,img, mask= mask)
            pixels, output = self.vision.detect_leak_blue(img.copy(), Smin, Smax, Vmin, Vmax)

            self.set_image(output, self.ui.label_img)
            self.ui.label_BluePixels.setText(f"Blue Pixels: {pixels}")

        elif self.ui.rbRedFeatures.isChecked():
            Vmin = self.red_MinValue
            Vmax = self.red_MaxValue
            Smin = self.red_MinSat
            Smax = self.red_MaxSat

            # Color1_min = np.array([0,Smin,Vmin], np.uint8)
            # Color1_max = np.array([15,Smax,Vmax], np.uint8)
            # Color2_min = np.array([165,Smin,Vmin], np.uint8)
            # Color2_max = np.array([179,Smax,Vmax], np.uint8)

            # # Create HSV Image and threshold into a range.
            # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            # mask1 = cv2.inRange(hsv, Color1_min, Color1_max)
            # mask2 = cv2.inRange(hsv, Color2_min, Color2_max)
            # mask = cv2.bitwise_or(mask1, mask2)
            # pixels1 = cv2.countNonZero(mask1)
            # pixels2 = cv2.countNonZero(mask2)
            # output = cv2.bitwise_and(img,img, mask= mask)
            pixels, output = self.vision.detect_leak_red(img.copy(), Smin, Smax, Vmin, Vmax)

            self.set_image(output, self.ui.label_img)
            self.ui.label_RedPixels.setText(f"Red Pixels: {pixels}")

        elif self.ui.rbWhiteFeatures.isChecked():
            Lmin = self.HlsLightMin
            Lmax = self.HlsLightMax
            Smin = self.HlsSatMin
            Smax = self.HlsSatMax

            pixels, output = self.vision.HSL_Leak_Analysis(img.copy(), Lmin, Lmax, Smin, Smax)

            self.set_image(output, self.ui.label_img)
            self.ui.label_WhitePixels.setText(f"White Pixels: {pixels}")


    def OnRadioButtonCheck(self):
        if not self._appLoaded: return
        self.rbToggled = True
        if self.ui.rbBlueFeatures.isChecked():
            self.ui.sliderMaxSaturation.setValue(self.blue_MaxSat)
            self.ui.sliderMinValue.setValue(self.blue_MinValue)
            self.ui.sliderMinSaturation.setValue(self.blue_MinSat)
            self.ui.sliderMaxValue.setValue(self.blue_MaxValue)
            self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.blue_MaxSat}")
            self.ui.label_MinValue.setText(f"Min Value: {self.blue_MinValue}")
            self.ui.label_MinSaturation.setText(f"Min Saturation: {self.blue_MinSat}")
            self.ui.label_MaxValue.setText(f"Max Value: {self.blue_MaxValue}")
        elif self.ui.rbRedFeatures.isChecked():
            self.ui.sliderMaxSaturation.setValue(self.red_MaxSat)
            self.ui.sliderMinValue.setValue(self.red_MinValue)
            self.ui.sliderMinSaturation.setValue(self.red_MinSat)
            self.ui.sliderMaxValue.setValue(self.red_MaxValue)
            self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.red_MaxSat}")
            self.ui.label_MinValue.setText(f"Min Value: {self.red_MinValue}")
            self.ui.label_MinSaturation.setText(f"Min Saturation: {self.red_MinSat}")
            self.ui.label_MaxValue.setText(f"Max Value: {self.red_MaxValue}")
        elif self.ui.rbWhiteFeatures.isChecked():
            self.ui.sliderMaxSaturation.setValue(self.HlsSatMax)
            self.ui.sliderMinValue.setValue(self.HlsLightMin)
            self.ui.sliderMinSaturation.setValue(self.HlsSatMin)
            self.ui.sliderMaxValue.setValue(self.HlsLightMax)
            self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.HlsSatMax}")
            self.ui.label_MinValue.setText(f"Min Light: {self.HlsLightMin}")
            self.ui.label_MinSaturation.setText(f"Min Saturation: {self.HlsSatMin}")
            self.ui.label_MaxValue.setText(f"Max Light: {self.HlsLightMax}")

        self.extract_features(self.img.copy())
        self.rbToggled = False



    def onSliderChanged(self):
        if not self._appLoaded: return
        if self.ui.rbBlueFeatures.isChecked():
            if not self.rbToggled:
                self.blue_MaxSat = self.ui.sliderMaxSaturation.value()
                self.blue_MinValue = self.ui.sliderMinValue.value()
                self.blue_MinSat = self.ui.sliderMinSaturation.value()
                self.blue_MaxValue = self.ui.sliderMaxValue.value()
                self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.blue_MaxSat}")
                self.ui.label_MinValue.setText(f"Min Value: {self.blue_MinValue}")
                self.ui.label_MinSaturation.setText(f"Min Saturation: {self.blue_MinSat}")
                self.ui.label_MaxValue.setText(f"Max Value: {self.blue_MaxValue}")
        elif self.ui.rbRedFeatures.isChecked():
            if not self.rbToggled:
                self.red_MaxSat = self.ui.sliderMaxSaturation.value()
                self.red_MinValue = self.ui.sliderMinValue.value()
                self.red_MinSat = self.ui.sliderMinSaturation.value()
                self.red_MaxValue = self.ui.sliderMaxValue.value()
                self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.red_MaxSat}")
                self.ui.label_MinValue.setText(f"Min Value: {self.red_MinValue}")
                self.ui.label_MinSaturation.setText(f"Min Saturation: {self.red_MinSat}")
                self.ui.label_MaxValue.setText(f"Max Value: {self.red_MaxValue}")
        elif self.ui.rbWhiteFeatures.isChecked():
            if not self.rbToggled:
                self.HlsSatMax = self.ui.sliderMaxSaturation.value()
                self.HlsLightMin = self.ui.sliderMinValue.value()
                self.HlsSatMin = self.ui.sliderMinSaturation.value()
                self.HlsLightMax = self.ui.sliderMaxValue.value()
                self.ui.label_MaxSaturation.setText(f"Max Saturation: {self.HlsSatMax}")
                self.ui.label_MinValue.setText(f"Min Light: {self.HlsLightMin}")
                self.ui.label_MinSaturation.setText(f"Min Saturation: {self.HlsSatMin}")
                self.ui.label_MaxValue.setText(f"Max Light: {self.HlsLightMax}")
        if not self.rbToggled:
            self.extract_features(self.img.copy())


    def button_save(self):
        if not self._appLoaded: return
        self.save = True
        self.close()


    def button_cancel(self):
        if not self._appLoaded: return
        self.save = False
        self.close()

class FrmUser(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_DialogScanUser()
        self.ui.setupUi(self)
        self.ui.btnCancel.clicked.connect(self.fn_close)
        self.ui.txtUserID.textChanged.connect(self.text_changed)
        self.FormDone = False
        self.closed = False

    def fn_close(self):
        print("closeDialog")
        self.closed = True
        self.close()

    def text_changed(self) -> bool:
        # AOAL48080
        if len(self.ui.txtUserID.text()) >= 6:
            self.UserID = self.ui.txtUserID.text()
            self.FormDone = True
            print(self.UserID)
            self.close()
        self.FormDone = False

class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.Model = 'L'

        self.host_name = socket.gethostname()
        self.ui.listWidget_L.clear()
        self.ui.listWidget_R.clear()
        self.listWidgetItemsL = []
        self.listWidgetItemsR = []
        self.addToMsgList("App Initializing", self.ui.listWidget_L, self.listWidgetItemsL)
        self.addToMsgList("App Initializing", self.ui.listWidget_R, self.listWidgetItemsR)
        self.ui.tabCtl.setCurrentIndex(0)
        self.frmUser = FrmUser()
        self.colors = ColorCode()
        self.frmAdjustParams = FrmAdjustParameters()
        self.frmMaskEdit = FrmMaskEdit()
        self.ModelosList = []
        self.ModelInProcess = ""
        self.innerRadiusL = 0
        self.outterRadiusL = 0
        self.CircleCenterPointL = [0,0]
        self.RedSatMaxL = 0
        self.RedValueMinL = 0
        self.RedSatMinL = 0
        self.RedValueMaxL = 0
        self.BlueSatMaxL = 0
        self.BlueValueMinL = 0
        self.BlueSatMinL = 0
        self.BlueValueMaxL = 0
        self.PixelLimitL = 0

        self.innerRadiusR = 0
        self.outterRadiusR = 0
        self.CircleCenterPointR = [0,0]
        self.RedSatMaxR = 0
        self.RedValueMinR = 0
        self.RedSatMinR = 0
        self.RedValueMaxR = 0
        self.BlueSatMaxR = 0
        self.BlueValueMinR = 0
        self.BlueSatMinR = 0
        self.BlueValueMaxR = 0
        self.PixelLimitR = 0

        self.Password = ''

        self.cameraType_1 = None
        self.cameraAddress_1 = None
        self.cameraType_2 = None
        self.cameraAddress_2 = None

        self.LED_ON = 'background-color: rgb(0,207,80);\ncolor: rgb(230,230,230);'
        self.LED_OFF = 'background-color: rgb(0,107,40);\ncolor: rgb(230,230,230);'

        self.OUT_ON = 'background-color: rgb(247,40,10);'
        self.OUT_OFF = 'background-color: rgb(147,80,40);'

        # Tracking init
        self.addToMsgList("Loading traceablity Data", self.ui.listWidget_L, self.listWidgetItemsL)
        self.addToMsgList("Loading traceablity Data", self.ui.listWidget_R, self.listWidgetItemsR)
        self.logDataL = Models.LogFugaDeLuz()
        self.logDataR = Models.LogFugaDeLuz()
        self.logDataL.Modelo = 'Ring L'
        self.logDataR.Modelo = 'Ring R'
        self.glblMgr = GlobalFunctions()
        self.Equip = self.glblMgr.GetEquipByHostMOPTrack()
        self.glblMgr.GetEquipModelsMOPTrack()
        self.logDataL.Equip = self.Equip
        self.logDataR.Equip = self.Equip
        self.load_EquipConfig()
        self.load_controls()
        self.load_params()
        self.ui.txtDoor.setText("Opened")
        self.setCtlColor(self.ui.txtDoor, ColorCode().GRAY)

        # Control vars
        self.userLoggedIn = False
        self.InTest = False
        self.timerMain_inUse = False
        self.readyToTest = False
        self.test_fail = False
        self.DoorClosed = False
        self.test_step = 0
        self.img = None
        self.cir_shape = None
        self.tries = 0
        self.white_pixelsL = 0
        self.pixel_countL = 0
        self.red_pixelsL = 0
        self.blue_pixelsL = 0
        self.key_points_foundL = 0
        self.white_pixelsR = 0
        self.pixel_countR = 0
        self.red_pixelsR = 0
        self.blue_pixelsR = 0
        self.key_points_foundR = 0
        

        # button Connections
        self.addToMsgList("Setting up UI", self.ui.listWidget_L, self.listWidgetItemsL)
        self.addToMsgList("Setting up UI", self.ui.listWidget_R, self.listWidgetItemsR)
        # self.ui.rbHsvAnalysis.setChecked(True)
        self.ui.btnManualInspection.clicked.connect(self.manual_inspection)
        self.ui.btnLogEmployee.clicked.connect(self.user_login)
        self.ui.btnLogout.clicked.connect(self.user_logout)
        self.ui.btnTrigger.clicked.connect(self.trigger)
        self.ui.comboBox.currentIndexChanged.connect(self.cbx_model_change)
        # self.ui.SliderThreshold.setEnabled(False)
        self.ui.txtCenterPointX.setEnabled(False)
        self.ui.txtCenterPointY.setEnabled(False)
        # self.ui.SliderInnerRadius.setEnabled(False)
        # self.ui.SliderOutterRadius.setEnabled(False)
        self.ui.btnSaveThreshold.setEnabled(False)
        self.ui.btnManualInspection.setEnabled(False)
        self.ui.btnAdjustInpsection.setEnabled(False)
        self.ui.btnLogout.setEnabled(False)
        self.ui.btnIniciar.setEnabled(False)

        self.ui.btn_DoorClamp.setEnabled(False)
        self.ui.btn_MarkerL.setEnabled(False)
        self.ui.btn_MarkerR.setEnabled(False)
        self.ui.btn_Spare0.setEnabled(False)
        self.ui.btn_Spare1.setEnabled(False)
        self.ui.btn_Spare2.setEnabled(False)
        self.ui.btn_Spare3.setEnabled(False)
        self.ui.btn_Spare4.setEnabled(False)

        # self.ui.SliderThreshold.valueChanged.connect(self.SliderValueChanged)
        # self.ui.SliderInnerRadius.valueChanged.connect(self.SliderValueChanged)
        # self.ui.SliderOutterRadius.valueChanged.connect(self.SliderValueChanged)
        self.ui.btnSaveThreshold.clicked.connect(self.edit_mask)
        self.ui.btnAdjustInpsection.clicked.connect(self.adjust_parameters)
        self.ui.btnUnlockParameters.clicked.connect(self.unlock_parameters)
        self.ui.btnUnlockParameters.setEnabled(False)

        self.ui.btnIniciar.clicked.connect(self.testInit)

        self.ui.btnSaveThreshold.setText("Edit Mask")

        # Devices Init
        self.addToMsgList("Connecting devices", self.ui.listWidget_L, self.listWidgetItemsL)
        self.addToMsgList("Connecting devices", self.ui.listWidget_R, self.listWidgetItemsR)
        self.visionL = VisionSystem(self.cameraType_1, self.cameraAddress_1, 'L')
        if not self.visionL.initOK:
            self.show_messagebox("Error", "Connection to vision system L not established")
        else:
            self.ui.txtCameraStatusL.setText("Connected Camera L")
            self.setCtlColor(self.ui.txtCameraStatusL, self.colors.GREEN)
            self.SliderValueChanged()


        
        self.visionR = VisionSystem(self.cameraType_2, self.CameraAddress_R, 'R')
        if not self.visionR.initOK:
            self.show_messagebox("Error", "Connection to vision system R not established")
        else:
            self.ui.txtCameraStatusR.setText("Connected Camera R")
            self.setCtlColor(self.ui.txtCameraStatusR, self.colors.GREEN)
            self.SliderValueChanged()
    
        
        # Phidget
        self.InputsArray = [False,False,False,False,False,False,False,False]
        self.OutputsArray = [False,False,False,False,False,False,False,False]

        self.ui.btn_DoorClamp.setChecked(False)
        self.ui.btn_MarkerL.setChecked(False)
        self.ui.btn_MarkerR.setChecked(False)
        self.ui.btn_Spare0.setChecked(False)
        self.ui.btn_Spare1.setChecked(False)
        self.ui.btn_Spare2.setChecked(False)
        self.ui.btn_Spare3.setChecked(False)
        self.ui.btn_Spare4.setChecked(False)

        self.ui.btn_DoorClamp.setStyleSheet(self.OUT_OFF)
        self.ui.btn_MarkerL.setStyleSheet(self.OUT_OFF)
        self.ui.btn_MarkerR.setStyleSheet(self.OUT_OFF)
        self.ui.btn_Spare0.setStyleSheet(self.OUT_OFF)
        self.ui.btn_Spare1.setStyleSheet(self.OUT_OFF)
        self.ui.btn_Spare2.setStyleSheet(self.OUT_OFF)
        self.ui.btn_Spare3.setStyleSheet(self.OUT_OFF)
        self.ui.btn_Spare4.setStyleSheet(self.OUT_OFF)

        

        self.DoorInput = DigitalInput()
        self.DoorInput.setChannel(8)
        self.SpareIn1 = DigitalInput()
        self.SpareIn1.setChannel(0)
        self.SpareIn2 = DigitalInput()
        self.SpareIn2.setChannel(1)
        self.SpareIn3 = DigitalInput()
        self.SpareIn3.setChannel(2)
        self.SpareIn4 = DigitalInput()
        self.SpareIn4.setChannel(3)
        self.SpareIn5 = DigitalInput()
        self.SpareIn5.setChannel(4)
        self.SpareIn6 = DigitalInput()
        self.SpareIn6.setChannel(5)
        self.SpareIn7 = DigitalInput()
        self.SpareIn7.setChannel(6)
        self.DoorClamp = DigitalOutput()
        self.DoorClamp.setChannel(1)
        self.MarkerL = DigitalOutput()
        self.MarkerL.setChannel(2)
        self.MarkerR = DigitalOutput()
        self.MarkerR.setChannel(3)
        self.SpareOut1 = DigitalOutput()
        self.SpareOut1.setChannel(0)
        self.ReleaseClamp = DigitalOutput()
        self.ReleaseClamp.setChannel(4)
        self.SpareOut3 = DigitalOutput()
        self.SpareOut3.setChannel(5)
        self.SpareOut4 = DigitalOutput()
        self.SpareOut4.setChannel(6)
        self.SpareOut5 = DigitalOutput()
        self.SpareOut5.setChannel(7)
        try:
            self.DoorInput.openWaitForAttachment(1000)
            self.SpareIn1.openWaitForAttachment(1000)
            self.SpareIn2.openWaitForAttachment(1000)
            self.SpareIn3.openWaitForAttachment(1000)
            self.SpareIn4.openWaitForAttachment(1000)
            self.SpareIn5.openWaitForAttachment(1000)
            self.SpareIn6.openWaitForAttachment(1000)
            self.SpareIn7.openWaitForAttachment(1000)
            self.DoorClamp.openWaitForAttachment(1000)
            self.MarkerL.openWaitForAttachment(1000)
            self.MarkerR.openWaitForAttachment(1000)
            self.SpareOut1.openWaitForAttachment(1000)
            self.ReleaseClamp.openWaitForAttachment(1000)
            self.SpareOut3.openWaitForAttachment(1000)
            self.SpareOut4.openWaitForAttachment(1000)
            self.SpareOut5.openWaitForAttachment(1000)
        except PhidgetException as e:
            self.show_messagebox("Error", str(e))

        # Test Timer
        self.timer_test = QTimer()
        self.timer_test.setInterval(100)
        self.timer_test.timeout.connect(self.Inspect)

        # Timer main
        self.timer_main = QTimer()
        self.timer_main.setInterval(100)
        self.timer_main.timeout.connect(self.timer_main_timeout)
        self.timer_main.start()
        self.addToMsgList("Loading Complete!", self.ui.listWidget_L, self.listWidgetItemsL)
        self.addToMsgList("Loading Complete!", self.ui.listWidget_R, self.listWidgetItemsR)
        self.readyToTest = True
        self.ui.comboBox.setCurrentIndex(-1)

    def SliderValueChanged(self):
        vision = self.visionL if self.Model=='L' else self.visionR
        if not vision.initOK:
                return
        # vision.threshold_value = self.ui.SliderThreshold.value()
        # self.ui.label_thresh_level.setText(f"Threshold Level: {vision.threshold_value}")
        if vision.DeviceName == 'L':
            # self.innerRadiusL = self.ui.SliderInnerRadius.value()
            # self.ui.label_InnerRadius.setText(f"Inner Radius: {self.innerRadiusL}")
            # self.outterRadiusL = self.ui.SliderOutterRadius.value()
            # self.ui.label_OuterRadius.setText(f"Outter Radius: {self.outterRadiusL}")
            self.CircleCenterPointL[0] =int(self.ui.txtCenterPointX.text())
            self.CircleCenterPointL[1] =int(self.ui.txtCenterPointY.text())
        if vision.DeviceName == 'R':
            # self.innerRadiusR = self.ui.SliderInnerRadius.value()
            # self.ui.label_InnerRadius.setText(f"Inner Radius: {self.innerRadiusR}")
            # self.outterRadiusR = self.ui.SliderOutterRadius.value()
            # self.ui.label_OuterRadius.setText(f"Outter Radius: {self.outterRadiusR}")
            self.CircleCenterPointR[0] =int(self.ui.txtCenterPointX.text())
            self.CircleCenterPointR[1] =int(self.ui.txtCenterPointY.text())

    

    def FillGrid(self, lastTen: list[str]):
        i = 0
        self.ui.tableTestData.clear()
        self.ui.tableTestData.setRowCount(len(lastTen))
        self.ui.tableTestData.setColumnCount(8)
        self.ui.tableTestData.setHorizontalHeaderLabels(["Empleado", "Modelo", "White Px", "Red Px", "Blue Px", "Px Count", "Result", "Fecha"])
        self.ui.tableTestData.verticalHeader().hide()
        for row in lastTen:
            color = QColor.fromRgb(20,230,20,255) if row['TestResult'] == True else QColor.fromRgb(250,20,20,255)
            result = "PASS" if row['TestResult'] else "FAIL"
            if row['NumEmpleado'] is None:
                item_Empleado = QTableWidgetItem('None')    
            else:
                item_Empleado = QTableWidgetItem(row['NumEmpleado'])
            if row['Model'] is None:
                item_Model = QTableWidgetItem('None')
            else:
                if ',' in row['Model']: 
                    item_Model = QTableWidgetItem(f"{row['Model'].split(',')[1]} {row['Model'].split(',')[2]}")
                else:
                    item_Model = QTableWidgetItem(row['Model'])
            item_WhitePixel = QTableWidgetItem(str(row['WhitePixelCount']))
            item_RedPixel = QTableWidgetItem(str(row['RedPixelCount']))
            item_BluePixel = QTableWidgetItem(str(row['BluePixelCount']))
            item_TotalPixel = QTableWidgetItem(str(row['TotalPixelCount']))
            item_TestResult = QTableWidgetItem(result)
            item_TestResult.setBackground(color)
            item_Date = QTableWidgetItem(row['CreateDate'].strftime("%d-%m-%y %H:%M:%S"))

            self.ui.tableTestData.setItem(i, 0, item_Empleado)
            self.ui.tableTestData.setItem(i, 1, item_Model)
            self.ui.tableTestData.setItem(i, 2, item_WhitePixel)
            self.ui.tableTestData.setItem(i, 3, item_RedPixel)
            self.ui.tableTestData.setItem(i, 4, item_BluePixel)
            self.ui.tableTestData.setItem(i, 5, item_TotalPixel)
            self.ui.tableTestData.setItem(i, 6, item_TestResult)
            self.ui.tableTestData.setItem(i, 7, item_Date)
            self.ui.tableTestData.setColumnWidth(0, 60)
            self.ui.tableTestData.setColumnWidth(1, 90)
            self.ui.tableTestData.setColumnWidth(2, 60)
            self.ui.tableTestData.setColumnWidth(3, 60)
            self.ui.tableTestData.setColumnWidth(4, 60)
            self.ui.tableTestData.setColumnWidth(5, 60)
            self.ui.tableTestData.setColumnWidth(6, 70)
            self.ui.tableTestData.setColumnWidth(7, 130)

            i+=1
        self.ui.tableTestData.show()

    def save_VisionParameters(self):
        # value_thresh = self.ui.SliderThreshold.value()
        param_thresh = 'Threshold'
        # value_Inner = self.ui.SliderInnerRadius.value()
        param_Inner = 'InnerRadius'
        # value_Outter = self.ui.SliderOutterRadius.value()
        param_Outter = 'OutterRadius'
        value_cx = self.ui.txtCenterPointX.text()
        param_cx = 'CenterX'
        value_cy = self.ui.txtCenterPointY.text()
        param_cy = 'CenterY'
        ModelParam = 0
        modelo = 'DL' if self.ModelInProcess.endswith("L") else 'DR'
        if modelo == 'DL':
            ModelParam = 1
        elif modelo == 'DR':
            ModelParam = 2

        redVmin = self.glblMgr.saveParam(self.Equip, 'RedValueMin', self.RedValueMinL, 1)
        redSmax = self.glblMgr.saveParam(self.Equip, 'RedSatMax', self.RedSatMaxL, 1)
        redVmax = self.glblMgr.saveParam(self.Equip, 'RedValueMax', self.RedValueMaxL, 1)
        redSmin = self.glblMgr.saveParam(self.Equip, 'RedSatMin', self.RedSatMinL, 1)

        blueVmax = self.glblMgr.saveParam(self.Equip, 'BlueValueMax', self.BlueValueMaxL, 1)
        blueSmin = self.glblMgr.saveParam(self.Equip, 'BlueSatMin', self.BlueSatMinL, 1)
        blueVmin = self.glblMgr.saveParam(self.Equip, 'BlueValueMin', self.BlueValueMinL, 1)
        blueSmax = self.glblMgr.saveParam(self.Equip, 'BlueSatMax', self.BlueSatMaxL, 1)

        hlsLmin = self.glblMgr.saveParam(self.Equip, 'HlsLightMin', self.HlsLightMinL, 1)
        hlsLmax = self.glblMgr.saveParam(self.Equip, 'HlsLightMax', self.HlsLightMaxL, 1)
        hlsSmin = self.glblMgr.saveParam(self.Equip, 'HlsSatMin', self.HlsSatMinL, 1)
        hlsSmax = self.glblMgr.saveParam(self.Equip, "HlsSatMax", self.HlsSatMaxL, 1)

        redVmin = self.glblMgr.saveParam(self.Equip, 'RedValueMin', self.RedValueMinR, 2)
        redSmax = self.glblMgr.saveParam(self.Equip, 'RedSatMax', self.RedSatMaxR, 2)
        redVmax = self.glblMgr.saveParam(self.Equip, 'RedValueMax', self.RedValueMaxR, 2)
        redSmin = self.glblMgr.saveParam(self.Equip, 'RedSatMin', self.RedSatMinR, 2)

        blueVmax = self.glblMgr.saveParam(self.Equip, 'BlueValueMax', self.BlueValueMaxR, 2)
        blueSmin = self.glblMgr.saveParam(self.Equip, 'BlueSatMin', self.BlueSatMinR, 2)
        blueVmin = self.glblMgr.saveParam(self.Equip, 'BlueValueMin', self.BlueValueMinR, 2)
        blueSmax = self.glblMgr.saveParam(self.Equip, 'BlueSatMax', self.BlueSatMaxR, 2)

        hlsLmin = self.glblMgr.saveParam(self.Equip, 'HlsLightMin', self.HlsLightMinR, 2)
        hlsLmax = self.glblMgr.saveParam(self.Equip, 'HlsLightMax', self.HlsLightMaxR, 2)
        hlsSmin = self.glblMgr.saveParam(self.Equip, 'HlsSatMin', self.HlsSatMinR, 2)
        hlsSmax = self.glblMgr.saveParam(self.Equip, "HlsSatMax", self.HlsSatMaxR, 2)


        # thresk_ok = self.glblMgr.saveParam(self.Equip, param_thresh, value_thresh, ModelParam)
        # Inner_ok = self.glblMgr.saveParam(self.Equip, param_Inner, value_Inner, ModelParam)
        # Outter_ok = self.glblMgr.saveParam(self.Equip, param_Outter, value_Outter, ModelParam)
        # CX_ok = self.glblMgr.saveParam(self.Equip, param_cx, value_cx, ModelParam)
        # CY_ok = self.glblMgr.saveParam(self.Equip, param_cy, value_cy, ModelParam)
        if blueSmax and blueVmin and redSmax and redVmin:
            self.show_messagebox('Succes!', "Configuration Succesfully saved")
        else:
            self.show_messagebox('Error', "Could not Save the configuration")

    def live_video(self):
        vision = self.visionL if self.Model=='L' else self.visionR
        if not vision.initOK:
                return
        if vision.DeviceName == 'L':
            self.addToMsgList("Trigger!", self.ui.listWidget_L, self.listWidgetItemsL)
        else:
            self.addToMsgList("Trigger!", self.ui.listWidget_R, self.listWidgetItemsR)
        img = vision.trigger()
        # img = self.vision.Open_image("LightLeakCut.bmp")

        if self.Model == 'L':
            self.img = vision.extract_composite_circle_bitwise(img, self.CircleCenterPointL, self.innerRadiusL, self.outterRadiusL, debug=False)
            # if self.ui.rbGrayscaleThreshold.isChecked():
            #     pixels, img_mask = vision.apply_thresh(self.img, False)
            #     self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
            # elif self.ui.rbHslAnalysis.isChecked():
            #     pixels, img_mask = vision.HSL_analysis(self.img, False)
            #     self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
            # elif self.ui.rbHsvAnalysis.isChecked():
            red_pixels, red_img = vision.detect_leak_red(self.img.copy(), self.RedSatMaxL, self.RedValueMinL)
            blue_pixels, blue_img = vision.detect_leak_blue(self.img.copy(), self.BlueSatMaxL, self.BlueValueMinL)
            white_pixels, white_img = self.visionL.HSL_Leak_Analysis(self.img.copy(), self.HlsLightMinL, self.HlsLightMaxL, self.HlsSatMinL, self.HlsSatMaxL)
            pixels = red_pixels + blue_pixels + white_pixels
            # self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
                # self.cir_shape = cv2.bitwise_or(red_img, blue_img)
        elif self.Model == 'R':
            self.img = vision.extract_composite_circle_bitwise(img, self.CircleCenterPointR, self.innerRadiusR, self.outterRadiusR, debug=False)
            # if self.ui.rbGrayscaleThreshold.isChecked():
            #     pixels, img_mask = vision.apply_thresh(self.img, False)
            #     self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
            # elif self.ui.rbHslAnalysis.isChecked():
            #     pixels, img_mask = vision.HSL_analysis(self.img, False)
            #     self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
            # elif self.ui.rbHsvAnalysis.isChecked():
            red_pixels, red_img = vision.detect_leak_red(self.img.copy(), self.RedSatMaxR, self.RedValueMinR)
            blue_pixels, blue_img = vision.detect_leak_blue(self.img.copy(), self.BlueSatMaxR, self.BlueValueMinR)
            white_pixels, white_img = self.visionL.HSL_Leak_Analysis(self.img.copy(), self.HlsLightMinR, self.HlsLightMaxR, self.HlsSatMinR, self.HlsSatMaxR)
            pixels = red_pixels + blue_pixels + white_pixels
                # self.ui.label_PixelCountManual.setText(f"Pixel count: {pixels}")
                # self.cir_shape = cv2.bitwise_or(red_img, blue_img)


        # self.set_image(self.img, self.ui.label_img_L)
        self.cir_shape = cv2.bitwise_or(red_img, blue_img)
        self.cir_shape = cv2.bitwise_or(self.cir_shape, white_img)
        self.set_image(self.cir_shape, self.ui.label_img_manual)

    def trigger(self, vision: VisionSystem):
        if not self.ui.btnLiveVideo.isChecked():
            vision = self.visionL if self.Model == 'L' else self.visionR
            if not vision.initOK:
                return
            if vision.DeviceName == 'L':
                self.addToMsgList("Trigger!", self.ui.listWidget_L, self.listWidgetItemsL)
            else:
                self.addToMsgList("Trigger!", self.ui.listWidget_R, self.listWidgetItemsR)
            # img = self.vision.Open_image("LightLeakCut.bmp")
            img = vision.trigger()

            self.set_image(img, self.ui.label_img_L if vision.DeviceName == 'L' else self.ui.label_img_R)
            self.set_image(img, self.ui.label_img_manual)

    def set_image(self, img, label: QLabel):
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h,w,ch = rgb_img.shape

        qt_img = QImage(rgb_img.data, w, h, ch *w, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_img))
        label.update()


    def addToMsgList(self, item: str, listWidget: QListWidget, listItem: QListWidgetItem):
        if len(item) <= 16:
            msg = item + '\t'
        elif len(item) <= 9:
            msg = item + '\t\t'
        else:
            msg = item
        listItem.insert(0, f"{msg}\t{datetime.datetime.now()}")
        item_count = len(listItem)
        if item_count > 20:
            listItem.pop(-1)
        listWidget.clear()
        listWidget.addItems(listItem)

    def user_login(self):
        self.frmUser.exec()
        if self.frmUser.FormDone or self.frmUser.UserID is not None:
            self.userData = self.glblMgr.GetMOPTrackUserData(self.frmUser.UserID)
            if self.userData is None:
                self.show_messagebox("Error",
                                     "User ID not found in database")
            elif not self.userData[3]:
                self.show_messagebox("Error",
                                     "User not active")
            else:
                lastTen = self.glblMgr.GetLastTenRecords()
                self.FillGrid(lastTen)
                if self.userData[0] >= 2:
                    self.ui.btnManualInspection.setEnabled(True)
                    self.ui.btnLogout.setEnabled(True)
                    self.ui.btnLogEmployee.setEnabled(False)
                    self.ui.btnUnlockParameters.setEnabled(True)

                self.userLoggedIn = True
                self.UserID = self.frmUser.UserID
                self.UserName = f"{self.UserID}-{self.userData[1]} {self.userData[2]}"
                self.frmUser.UserID = None
                self.frmUser.ui.txtUserID.clear()
                self.ui.txtEmployeeNum.setText(self.UserName)
                self.ui.txtLoggedEmployee.setText(self.UserID)
                self.logDataL.NumEmpleado = self.UserID
                self.logDataR.NumEmpleado = self.UserID
                self.show_messagebox("Log in", "User logged in successfully!")
                self.addToMsgList("User Logged In", self.ui.listWidget_L, self.listWidgetItemsL)
                self.addToMsgList("User Logged In", self.ui.listWidget_R, self.listWidgetItemsR)
                self.ui.comboBox.setCurrentIndex(0 )

        else :
            self.show_messagebox("Error",
                                "User Id not provided!")

    def user_logout(self):
        dialog = Ui_LogOutDialog()
        if dialog.exec():
            self.userLoggedIn = False
            self.userData = None
            self.ui.txtEmployeeNum.clear()
            self.ui.txtLoggedEmployee.clear()
            # self.ui.SliderThreshold.setEnabled(False)
            self.ui.txtCenterPointX.setEnabled(False)
            self.ui.txtCenterPointY.setEnabled(False)
            # self.ui.SliderInnerRadius.setEnabled(False)
            # self.ui.SliderOutterRadius.setEnabled(False)
            self.ui.btnSaveThreshold.setEnabled(False)
            self.ui.btnManualInspection.setEnabled(False)
            self.ui.btnLogout.setEnabled(False)
            self.ui.btnAdjustInpsection.setEnabled(False)
            self.ui.btnLogEmployee.setEnabled(True)
            self.ui.btnUnlockParameters.setEnabled(False)
        else:
            return

    def testInit(self):
        if self.ui.btnIniciar.isChecked():
            self.ReleaseClamp = False
            self.DoorClosed = True
            self.ui.txtDoor.setText("Closed")
            self.setCtlColor(self.ui.txtDoor, ColorCode().GREEN)
            sleep(0.1)
        elif not self.ui.btnIniciar.isChecked():
            self.DoorClosed = False
            self.ui.txtDoor.setText("Opened")
            self.setCtlColor(self.ui.txtDoor, ColorCode().GRAY)

    def timer_main_timeout(self):
        if not self.timerMain_inUse:
            self.timerMain_inUse = True
            if self.userLoggedIn:
                if not self.InTest and self.readyToTest:
                    self.ui.lineEdit_status_L.setText("Ready to Test")
                    self.setCtlColor(self.ui.lineEdit_status_L, self.colors.BLUE)
                    self.ui.lineEdit_status_R.setText("Ready to Test")
                    self.setCtlColor(self.ui.lineEdit_status_R, self.colors.BLUE)
                elif self.InTest and not self.test_failL and not self.test_failR and not self.test_passL and not self.test_passR:
                    self.ui.lineEdit_status_L.setText("Testing")
                    self.setCtlColor(self.ui.lineEdit_status_L, self.colors.BLUE)
                    self.ui.lineEdit_status_R.setText("Testing")
                    self.setCtlColor(self.ui.lineEdit_status_R, self.colors.BLUE)
                    self.ui.txtTestStatus.setText("In test")



            else:
                self.ui.lineEdit_status_L.setText("Waiting Log in")
                self.setCtlColor(self.ui.lineEdit_status_L, self.colors.GRAY)
                self.ui.lineEdit_status_R.setText("Waiting Log in")
                self.setCtlColor(self.ui.lineEdit_status_R, self.colors.GRAY)
                self.ui.txtTestStatus.setText("Disabled")
                self.timerMain_inUse = False
                return

            if self.ui.btnLiveVideo.isChecked():
                self.live_video()

            if not self.InTest and self.ui.tabCtl.currentIndex() == 2:
                self.InputsArray[0] = self.DoorInput.getState()
                self.InputsArray[1] = self.SpareIn1.getState()
                self.InputsArray[2] = self.SpareIn2.getState()
                self.InputsArray[3] = self.SpareIn3.getState()
                self.InputsArray[4] = self.SpareIn4.getState()
                self.InputsArray[5] = self.SpareIn5.getState()
                self.InputsArray[6] = self.SpareIn6.getState()
                self.InputsArray[7] = self.SpareIn7.getState()
                
                self.ui.LED_DoorClosed.setStyleSheet(self.LED_ON if self.InputsArray[0] else self.LED_OFF)
                self.ui.LED_SpareIn0.setStyleSheet(self.LED_ON if self.InputsArray[1] else self.LED_OFF)
                self.ui.LED_SpareIn1.setStyleSheet(self.LED_ON if self.InputsArray[2] else self.LED_OFF)
                self.ui.LED_SpareIn2.setStyleSheet(self.LED_ON if self.InputsArray[3] else self.LED_OFF)
                self.ui.LED_SpareIn3.setStyleSheet(self.LED_ON if self.InputsArray[4] else self.LED_OFF)
                self.ui.LED_SpareIn4.setStyleSheet(self.LED_ON if self.InputsArray[5] else self.LED_OFF)
                self.ui.LED_SpareIn5.setStyleSheet(self.LED_ON if self.InputsArray[6] else self.LED_OFF)
                self.ui.LED_SpareIn6.setStyleSheet(self.LED_ON if self.InputsArray[7] else self.LED_OFF)
                
                self.OutputsArray[0] = self.ui.btn_DoorClamp.isChecked()
                self.OutputsArray[1] = self.ui.btn_MarkerL.isChecked()
                self.OutputsArray[2] = self.ui.btn_MarkerR.isChecked()
                self.OutputsArray[3] = self.ui.btn_Spare0.isChecked()
                self.OutputsArray[4] = self.ui.btn_Spare1.isChecked()
                self.OutputsArray[5] = self.ui.btn_Spare2.isChecked()
                self.OutputsArray[6] = self.ui.btn_Spare3.isChecked()
                self.OutputsArray[7] = self.ui.btn_Spare4.isChecked()

                self.ui.btn_DoorClamp.setStyleSheet(self.OUT_ON if self.OutputsArray[0] else self.OUT_OFF)
                self.ui.btn_MarkerL.setStyleSheet(self.OUT_ON if self.OutputsArray[1] else self.OUT_OFF)
                self.ui.btn_MarkerR.setStyleSheet(self.OUT_ON if self.OutputsArray[2] else self.OUT_OFF)
                self.ui.btn_Spare0.setStyleSheet(self.OUT_ON if self.OutputsArray[3] else self.OUT_OFF)
                self.ui.btn_Spare1.setStyleSheet(self.OUT_ON if self.OutputsArray[4] else self.OUT_OFF)
                self.ui.btn_Spare2.setStyleSheet(self.OUT_ON if self.OutputsArray[5] else self.OUT_OFF)
                self.ui.btn_Spare3.setStyleSheet(self.OUT_ON if self.OutputsArray[6] else self.OUT_OFF)
                self.ui.btn_Spare4.setStyleSheet(self.OUT_ON if self.OutputsArray[7] else self.OUT_OFF)

                self.DoorClamp.setState(self.OutputsArray[0])
                self.MarkerL.setState(self.OutputsArray[1])
                self.MarkerR.setState(self.OutputsArray[2])
                self.SpareOut1.setState(self.OutputsArray[3])
                self.ReleaseClamp.setState(self.OutputsArray[4])
                self.SpareOut3.setState(self.OutputsArray[5])
                self.SpareOut4.setState(self.OutputsArray[6])
                self.SpareOut5.setState(self.OutputsArray[7])


            if self.DoorInput.getState():
                self.DoorClosed = True
                self.ui.txtDoor.setText("Closed")
                self.setCtlColor(self.ui.txtDoor, ColorCode().GREEN)
                sleep(0.1)
            elif not self.DoorInput.getState():
                self.DoorClosed = False
                self.ui.txtDoor.setText("Opened")
                self.setCtlColor(self.ui.txtDoor, ColorCode().GRAY)

            if not self.DoorClosed and not self.InTest and self.ui.tabCtl.currentIndex() == 0:
                self.readyToTest = True
                
            if self.DoorClosed == True and not self.InTest and self.readyToTest and self.ui.tabCtl.currentIndex() == 0:
                if self.ui.btnLiveVideo.isChecked():
                    self.timerMain_inUse = False
                    return
                # self.trigger(self.visionL)
                # self.trigger(self.visionR)
                self.set_image(self.visionL.trigger(), self.ui.label_img_L)
                self.set_image(self.visionR.trigger(), self.ui.label_img_R)
                self.test_fail = False
                self.test_failL = False
                self.test_failR = False
                self.test_pass = False
                self.test_passL = False
                self.test_passR = False
                self.InTest = True
                self.readyToTest = False
                self.test_step = 0
                sleep(1)
                self.timer_test.start()
                self.timerMain_inUse = False

            self.timerMain_inUse = False



    def setCtlColor(self, obj: QWidget, color: ColorCode):
        if color == self.colors.BLUE:
            obj.setStyleSheet(u"background-color: rgb(0 ,87, 127);\n"
                              "color: rgb(255,255,255)")
        elif color == self.colors.GRAY:
            obj.setStyleSheet(u"background-color: rgb(70 ,70, 70);\n"
                              "color: rgb(220,220,220)")
        elif color == self.colors.GREEN:
            obj.setStyleSheet(u"background-color: rgb(0 ,170, 60);\n"
                              "color: rgb(0,0,0)")
        elif color == self.colors.RED:
            obj.setStyleSheet(u"background-color: rgb(180 ,20, 20);\n"
                              "color: rgb(0,0,0)")
        obj.update()

    def load_controls(self):
        self.ui.txtCameraType.setText(self.cameraType_1)
        self.ui.txtCameraAddress.setText(self.cameraAddress_1)
        self.ui.txtCameraStatusL.setText('Not Connected')
        self.ui.txtCameraStatusR.setText('Not Connected')
        self.ui.txtEquip.setText(str(self.Equip))
        self.setCtlColor(self.ui.txtCameraStatusL, self.colors.RED)
        self.setCtlColor(self.ui.txtCameraStatusR, self.colors.RED)
        for partNum in self.glblMgr.PartNumbersList:
            model = partNum.PartNumber + ", " + str(partNum.Description).split(' ')[0] +" "+ str(partNum.Description).split(' ')[1]
            self.ModelosList.append(model)

        self.ui.comboBox.clear()
        self.ui.comboBox.addItems(self.ModelosList)
        self.ui.comboBox.setCurrentIndex(0)

    def load_EquipConfig(self):
        self.glblMgr.GetParamsMOPTrack(self.Equip)
        self.ModelInProcess = self.ui.comboBox.currentText()
        for modelParam in self.glblMgr.RecordListParams:
            if modelParam.param == "CameraType":
                self.cameraType_1 = modelParam.value
                if modelParam.value_2 is not None:
                    self.cameraType_2 = modelParam.value_2
            elif modelParam.param == "CameraUSBId":
                self.cameraAddress_1 = modelParam.value
                if modelParam.value_2 is not None:
                    self.CameraAddress_R = modelParam.value_2
            elif modelParam.param == "Password":
                self.Password = modelParam.value
                

    def load_params(self):
        self.glblMgr.GetParamsMOPTrack(self.Equip)
        self.ModelInProcess = self.ui.comboBox.currentText()
        # modelo = 'DL' if self.ModelInProcess.endswith("L") else 'DR'
        for modelParam in self.glblMgr.RecordListParams:
            if modelParam.param == "Threshold":
                self.ThresholdL = int(modelParam.value) 
                self.ThresholdR = int(modelParam.value_2)
                # self.ui.SliderThreshold.setValue(int(self.ThresholdL))
            if modelParam.param == "InnerRadius":
                self.innerRadiusL = int(modelParam.value)
                self.innerRadiusR = int(modelParam.value_2)
                # self.ui.SliderInnerRadius.setValue(int(self.innerRadiusL))
            if modelParam.param == "OutterRadius":
                self.outterRadiusL = int(modelParam.value)
                self.outterRadiusR = int(modelParam.value_2)
                # self.ui.SliderOutterRadius.setValue(int(self.outterRadiusL))
            if modelParam.param == "CenterX":
                self.CircleCenterPointL[0] = int(modelParam.value)
                self.CircleCenterPointR[0] = int(modelParam.value_2)
                self.ui.txtCenterPointX.setText(str(self.CircleCenterPointL[0]))
            if modelParam.param == "CenterY":
                self.CircleCenterPointL[1] = int(modelParam.value)
                self.CircleCenterPointR[1] = int(modelParam.value_2)
                self.ui.txtCenterPointY.setText(str(self.CircleCenterPointL[1]))
            if modelParam.param == "BlueValueMin":
                self.BlueValueMinL = int(modelParam.value)
                self.BlueValueMinR = int(modelParam.value_2)
            if modelParam.param == "BlueValueMax":
                self.BlueValueMaxL = int(modelParam.value)
                self.BlueValueMaxR = int(modelParam.value_2)
            if modelParam.param == "BlueSatMin":
                self.BlueSatMinL = int(modelParam.value)
                self.BlueSatMinR = int(modelParam.value_2)
            if modelParam.param == "BlueSatMax":
                self.BlueSatMaxL = int(modelParam.value)
                self.BlueSatMaxR = int(modelParam.value_2)
            if modelParam.param == "RedValueMin":
                self.RedValueMinL = int(modelParam.value)
                self.RedValueMinR = int(modelParam.value_2)
            if modelParam.param == "RedValueMax":
                self.RedValueMaxL = int(modelParam.value)
                self.RedValueMaxR = int(modelParam.value_2)
            if modelParam.param == "RedSatMax":
                self.RedSatMaxL = int(modelParam.value)
                self.RedSatMaxR = int(modelParam.value_2)
            if modelParam.param == "RedSatMin":
                self.RedSatMinL = int(modelParam.value)
                self.RedSatMinR = int(modelParam.value_2)
            if modelParam.param == "HlsLightMin":
                self.HlsLightMinL = int(modelParam.value)
                self.HlsLightMinR = int(modelParam.value_2)
            if modelParam.param == "HlsLightMax":
                self.HlsLightMaxL = int(modelParam.value)
                self.HlsLightMaxR = int(modelParam.value_2)
            if modelParam.param == "HlsSatMin":
                self.HlsSatMinL = int(modelParam.value)
                self.HlsSatMinR = int(modelParam.value_2)
            if modelParam.param == "HlsSatMax":
                self.HlsSatMaxL = int(modelParam.value)
                self.HlsSatMaxR = int(modelParam.value_2)
            if modelParam.param == "PixelLimit":
                self.PixelLimitL = int(modelParam.value)
                self.PixelLimitR = int(modelParam.value)


    def show_messagebox(self, Title: str, Msg: str):
        msg = QMessageBox()
        msg.setWindowTitle(Title)
        msg.setText(Msg)
        msg.exec()


    def manual_inspection(self):
        print("Manual inspection")
        finish_test = False
        self.test_fail = False
        self.test_pass = False
        testStep = 0

        vision = self.visionL if self.Model=='L' else self.visionR
        RedSatMin = self.RedSatMinL if self.Model=='L' else self.RedSatMinR
        RedSatMax = self.RedSatMaxL if self.Model=='L' else self.RedSatMaxR
        RedValueMin = self.RedValueMinL if self.Model=='L' else self.RedValueMinR
        RedValueMax = self.RedValueMaxL if self.Model=='L' else self.RedValueMaxR
        BlueSatMin = self.BlueSatMinL if self.Model=='L' else self.BlueSatMinR
        BlueSatMax = self.BlueSatMaxL if self.Model=='L' else self.BlueSatMaxR
        BlueValueMin = self.BlueValueMinL if self.Model=='L' else self.BlueValueMinR
        BlueValueMax = self.BlueValueMaxL if self.Model=='L' else self.BlueValueMaxR
        HlsLightMin = self.HlsLightMinL if self.Model=='L' else self.HlsLightMinR
        HlsLightMax = self.HlsLightMaxL if self.Model=='L' else self.HlsLightMaxR
        HlsSatMin = self.HlsSatMinL if self.Model=='L' else self.HlsSatMinR
        HlsSatMax = self.HlsSatMaxL if self.Model=='L' else self.HlsSatMaxR
        logData = self.logDataL if self.Model=='L' else self.logDataR
        if not vision.initOK:
                return

        while not finish_test:
            self.InTest = True
            self.readyToTest = False
            if testStep == 0:          # Get the image
                self.StartTime = datetime.datetime.now()

                # self.img = self.vision.Open_image('LightLeakCut.bmp') 
                self.img = vision.trigger() 
                self.set_image(self.img, self.ui.label_img_manual)
                testStep = 10
            elif testStep == 10:       # Draw the circle
                # self.img = self.vision.draw_circle(True)
                self.coord_1 = [616, 458]
                self.radius = 380
                self.radius2 = 416
                self.img = vision.extract_composite_circle_bitwise(self.img, self.CircleCenterPointL, self.innerRadiusL, self.outterRadiusL, debug=False)
                if self.img is None:
                    msg = QMessageBox()
                    msg.setWindowTitle("Warning")
                    msg.setText("No image to Inspect")
                    msg.exec()
                testStep = 20
            elif testStep == 20:       # Get the pixel count and evaluate
                red_pixels = 0
                blue_pixels = 0
                white_pixels = 0
                # if self.ui.rbGrayscaleThreshold.isChecked():
                #     pixel_count, self.cir_shape = vision.apply_thresh(self.img, True)
                # elif self.ui.rbHslAnalysis.isChecked():
                #     pixel_count, self.cir_shape = vision.HSL_analysis(self.img, True)
                # elif self.ui.rbHsvAnalysis.isChecked():
                    # pixel_count, self.cir_shape = vision.hsv_analysis(self.img, True)
                red_pixels, red_img = vision.detect_leak_red(self.img.copy(), RedSatMin, RedSatMax, RedValueMin, RedValueMax)
                blue_pixels, blue_img = vision.detect_leak_blue(self.img.copy(), BlueSatMin, BlueSatMax, BlueValueMin, BlueValueMax)
                white_pixels, white_img = vision.HSL_Leak_Analysis(self.img.copy(), HlsLightMin, HlsLightMax, HlsSatMin, HlsSatMax)
                pixel_count = red_pixels + blue_pixels + white_pixels
                self.cir_shape = cv2.bitwise_or(red_img, blue_img)
                self.cir_shape = cv2.bitwise_or(self.cir_shape, white_img)

                if self.tries < 3 and pixel_count == 0:
                    testStep = 0
                    self.tries += 1
                    continue

                if pixel_count != 0:
                    self.test_fail = True
                    self.test_pass = not self.test_fail
                else:
                    self.test_pass = True
                    self.test_fail = not self.test_pass

                logData.WhitePixelCount = white_pixels
                logData.RedPixelCount = red_pixels
                logData.BluePixelCount = blue_pixels
                logData.TotalPixelCount = pixel_count
                logData.TestResult = self.test_pass


                print(f"Pixel Count: {pixel_count}")
                # self.ui.label_PixelCountManual.setText(f"Pixel count: {pixel_count}")
                testStep = 30
            elif testStep == 30:       # Show The image
                # self.img[self.coord_1[1]-self.radius2:self.coord_1[1]+self.radius2, self.coord_1[0]-self.radius2:self.coord_1[0]+self.radius2] = self.cir_shape
                vision.frameToShow = self.img.copy()
                # rgb_img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
                cv2.imshow("Thresholded img", cv2.resize(self.cir_shape, (1200,900), interpolation=cv2.INTER_LINEAR))
                cv2.waitKey()
                cv2.destroyAllWindows()
                self.set_image(self.img, self.ui.label_img_manual)
                testStep = 40
            elif testStep == 40:       # Save Data Output
                print("Saving to Database")
                # with pymssql.connect(CS['server'], CS['uid'], CS['pwd'], CS['database']) as conn:
                #     with conn.cursor(as_dict=True) as cursor:
                #         cursor.callproc('proc_Insert_FugaDeLuz', (NumDeEmpleado, Model, pixel_count, not test_fail))
                #         conn.commit()

                testStep = 50
            elif testStep == 50:       # paint good or bad color

                if self.Model == 'L':
                    if self.test_pass:
                        self.ui.lineEdit_status_L.setText("Pass")
                        self.setCtlColor(self.ui.lineEdit_status_L, self.colors.GREEN)
                    elif self.test_fail:
                        self.ui.lineEdit_status_L.setText("Fail")
                        self.setCtlColor(self.ui.lineEdit_status_L, self.colors.RED)
                elif self.Model == 'R':
                    if self.test_pass:
                        self.ui.lineEdit_status_L.setText("Pass")
                        self.setCtlColor(self.ui.lineEdit_status_L, self.colors.GREEN)
                    elif self.test_fail:
                        self.ui.lineEdit_status_L.setText("Fail")
                        self.setCtlColor(self.ui.lineEdit_status_L, self.colors.RED)

                self.tries = 0
                self.InTest = False
                finish_test = True
                self.timer_test.stop()
                self.endTime = datetime.datetime.now()
                testTime = self.endTime - self.StartTime
                self.ui.txtCycleTime.setText(str(testTime.total_seconds()))

        pass

    def cbx_model_change(self):
        model = self.ui.comboBox.currentText()
        self.ui.txtPartNumber.setText(model)
        self.Model = 'L' if model.endswith('L') else 'R'
        # self.logData.Modelo = model
        self.load_params()

        centerX = self.CircleCenterPointL[0] if self.Model == 'L' else self.CircleCenterPointR[0]
        centerY = self.CircleCenterPointL[1] if self.Model == 'L' else self.CircleCenterPointR[1]
        self.ui.txtCenterPointX.setText(str(centerX))
        self.ui.txtCenterPointY.setText(str(centerY))

        pass

    def Inspect(self):

        # finish_test = False
        # self.test_fail = False
        # self.test_pass = False

        # # while not finish_test:
        # self.InTest = True
        # self.readyToTest = False
            if self.test_step == 0:          # Get the image
                self.StartTime = datetime.datetime.now()
                self.addToMsgList("Take Snapshot", self.ui.listWidget_L, self.listWidgetItemsL)
                self.addToMsgList("Take Snapshot", self.ui.listWidget_R, self.listWidgetItemsR)
                self.imgL = self.visionL.trigger()
                self.imgR = self.visionR.trigger()

                self.set_image(self.imgL, self.ui.label_img_L)
                self.set_image(self.imgR, self.ui.label_img_R)
                
                self.test_step = 5
            elif self.test_step == 5:       # clamp door to lock
                self.DoorClamp.setState(True)
                self.addToMsgList("Door Locked", self.ui.listWidget_L, self.listWidgetItemsL)
                self.test_step = 10
            elif self.test_step == 10:       # Draw the circle
                self.coord_1 = [616, 458]
                self.radius = 380
                self.radius2 = 416
                self.imgL = self.visionL.extract_composite_circle_bitwise(self.imgL, self.CircleCenterPointL, self.innerRadiusL, self.outterRadiusL, debug=False)
                self.imgR = self.visionR.extract_composite_circle_bitwise(self.imgR, self.CircleCenterPointR, self.innerRadiusR, self.outterRadiusR, debug=False)
                
                self.test_step = 20
            elif self.test_step == 20:       # Get the pixel count and evaluate
                
                # if self.ui.rbGrayscaleThreshold.isChecked():
                #     self.pixel_countL, self.cir_shapeL = self.visionL.apply_thresh(self.imgL, True)
                #     self.pixel_countR, self.cir_shapeR = self.visionR.apply_thresh(self.imgR, True)
                # elif self.ui.rbHslAnalysis.isChecked():
                #     self.pixel_countL, self.cir_shapeL = self.visionL.HSL_analysis(self.imgL, True)
                #     self.pixel_countR, self.cir_shapeR = self.visionR.HSL_analysis(self.imgR, True)
                # elif self.ui.rbHsvAnalysis.isChecked():
                red_pixelsL, red_imgL = self.visionL.detect_leak_red(self.imgL.copy(), self.RedSatMinL, self.RedSatMaxL, self.RedValueMinL, self.RedValueMaxL)
                blue_pixelsL, blue_imgL = self.visionL.detect_leak_blue(self.imgL.copy(), self.BlueSatMinL, self.BlueSatMaxL, self.BlueValueMinL, self.BlueValueMaxL)
                white_pixelsL, white_imgL = self.visionL.HSL_Leak_Analysis(self.imgL.copy(), self.HlsLightMinL, self.HlsLightMaxL, self.HlsSatMinL, self.HlsSatMaxL)
                    
                pixel_countL = red_pixelsL + blue_pixelsL + white_pixelsL
                self.cir_shapeL = cv2.bitwise_or(red_imgL, blue_imgL)
                self.cir_shapeL = cv2.bitwise_or(self.cir_shapeL, white_imgL)

                red_pixelsR, red_imgR = self.visionR.detect_leak_red(self.imgR.copy(), self.RedSatMinR, self.RedSatMaxR, self.RedValueMinR, self.RedValueMaxR)
                blue_pixelsR, blue_imgR = self.visionR.detect_leak_blue(self.imgR.copy(), self.BlueSatMinR, self.BlueSatMaxR, self.BlueValueMinR, self.BlueValueMaxR)
                white_pixelsR, white_imgR = self.visionR.HSL_Leak_Analysis(self.imgR.copy(), self.HlsLightMinR, self.HlsLightMaxR, self.HlsSatMinR, self.HlsSatMaxR)
                    
                pixel_countR = red_pixelsR + blue_pixelsR + white_pixelsR
                self.cir_shapeR = cv2.bitwise_or(red_imgR, blue_imgR)
                self.cir_shapeR = cv2.bitwise_or(self.cir_shapeR, white_imgR)

                if self.tries < 3:
                    self.test_step = 0
                    self.tries += 1
                    self.white_pixelsL += white_pixelsL
                    self.red_pixelsL += red_pixelsL
                    self.blue_pixelsL += blue_pixelsL
                    self.pixel_countL += pixel_countL

                    self.white_pixelsR += white_pixelsR
                    self.red_pixelsR += red_pixelsR
                    self.blue_pixelsR += blue_pixelsR
                    self.pixel_countR += pixel_countR
                    # self.key_points_found += len(kp)
                    return

                self.tries = 0

                self.white_pixelsL = int(self.white_pixelsL / 3)
                self.red_pixelsL = int(self.red_pixelsL / 3)
                self.blue_pixelsL = int(self.blue_pixelsL / 3)
                self.pixel_countL = int(self.pixel_countL / 3)

                self.white_pixelsR = int(self.white_pixelsR / 3)
                self.red_pixelsR = int(self.red_pixelsR / 3)
                self.blue_pixelsR = int(self.blue_pixelsR / 3)
                self.pixel_countR = int(self.pixel_countR / 3)
                    # self.key_points_found = int(self.key_points_found/3)
                    
                    #
                    #Change | HVG | Jul/8/2025
                    #Se agrega el limite de pixeles estaticamente para ejecutar las pruebas a 30 Pixeles, este dato debe venir desde la DB
                    #se mantendra asi hasta crear la ventana de configuracion
                    #
                if self.pixel_countL > 50:# self.PixelLimitL:
                    self.test_failL_luz = True
                    self.test_passL_luz = not self.test_failL_luz
                    print("prueba luz L - NG")
                else:
                    print("prueba luz L - OK")
                    self.test_passL_luz = True
                    self.test_failL_luz = not self.test_passL_luz
                    
                if self.pixel_countR > 50:# self.PixelLimitR:
                    self.test_failR_luz = True
                    self.test_passR_luz = not self.test_failR_luz
                    print("prueba luz R - NG")
                else:
                    print("prueba luz R - OK")
                    self.test_passR_luz = True
                    self.test_failR_luz = not self.test_passR_luz

                self.logDataL.WhitePixelCount = self.white_pixelsL
                self.logDataL.RedPixelCount = self.red_pixelsL
                self.logDataL.BluePixelCount = self.blue_pixelsL
                self.logDataL.TotalPixelCount = self.pixel_countL
                self.logDataL.TestResult = self.test_passL

                self.logDataR.WhitePixelCount = self.white_pixelsR
                self.logDataR.RedPixelCount = self.red_pixelsR
                self.logDataR.BluePixelCount = self.blue_pixelsR
                self.logDataR.TotalPixelCount = self.pixel_countR
                self.logDataR.TestResult = self.test_passR
                # print(f"KeyPoints: {self.key_points_found}")

                self.white_pixelsL = 0
                self.red_pixelsL = 0
                self.blue_pixelsL = 0
                self.pixel_countL = 0
                self.key_points_foundL = 0

                self.white_pixelsR = 0
                self.red_pixelsR = 0
                self.blue_pixelsR = 0
                self.pixel_countR = 0
                self.key_points_foundR = 0

                print(f"Pixel Count L: {self.logDataL.TotalPixelCount}")
                print(f"Pixel Count R: {self.logDataR.TotalPixelCount}")
                self.ui.label_PixelCount_L.setText(f"Pixel count: {self.logDataL.TotalPixelCount}")
                self.ui.label_PixelCount_R.setText(f"Pixel count: {self.logDataR.TotalPixelCount}")
                self.test_step = 25
            elif self.test_step == 25:       # Detecta muescas lado L
                self.addToMsgList("Running test 25",self.ui.listWidget_L,self.listWidgetItemsL)
                self.totalmuescasl = self.visionL.detectar_muescas(self.imgL.copy())
                self.addToMsgList(f"Muescas totales: {self.totalmuescasl}",self.ui.listWidget_L,self.listWidgetItemsL)
                
                if self.totalmuescasl > 0:
                    self.test_failL_muescas_L = True
                    self.test_passL_muescas_L = not self.test_failL_muescas_L
                    self.ui.lineEdit_status_L.setText("Muescas")
                    print("Muescas L - NG")
                else:
                    self.test_passL_muescas_L = True
                    self.test_failL_muescas_L = not self.test_passL_muescas_L
                    print("Muescas L - OK")

                
                self.test_step = 26
            
            elif self.test_step == 26:      # Detecta muescas lado R
                self.addToMsgList("Running test 26",self.ui.listWidget_R,self.listWidgetItemsR)
                self.totalmuescasr = self.visionR.detectar_muescas(self.imgR.copy())
                self.addToMsgList(f"Muescas totales: {self.totalmuescasr}",self.ui.listWidget_R,self.listWidgetItemsR)
                
                if self.totalmuescasr > 0:
                    self.test_failR_muescasR = True
                    self.test_passR_muescas_R = not self.test_failR_muescasR
                    self.ui.lineEdit_status_R.setText("Muescas")
                    print("Muescas R - NG")
                else:
                    self.test_passR_muescas_R = True
                    self.test_failR_muescasR = not self.test_passR_muescas_R
                    print("Muescas R - OK")
                    
                self.test_step = 27
            
            
            #====================================================
            #====================================================
            #===== DETECTA MANCHAS LADO L =======================
            #====================================================
            elif self.test_step == 27:     # Detecta manchas Lado L           
                print("running test 27")              
                self.imgslave = self.imgL
                imgz = VisionSystem.resize_to_square(self.imgslave, 800)
                self.total_manchas_L = VisionSystem.contar_subcontornos_en_roi(imgz,431,400,258,281,20,0)
                self.addToMsgList(f"Manchas totales: {self.total_manchas_L}",self.ui.listWidget_L,self.listWidgetItemsL)#print(f"manchas totales {self.manchas}")
                
                if self.total_manchas_L > 0:
                    self.test_failL = True
                    self.test_passL = not self.test_failL
                    self.ui.lineEdit_status_L.setText("Manchas")
                else:
                    self.test_passL = True
                    self.test_failL = not self.test_passL
                    
                self.test_step = 28
            #=====================================================
            #=====================================================
            #====== DETECTA MANCHAS LADO R =======================
            #=====================================================    
            elif self.test_step == 28:    # Detecta manchas lado R
                print("running test 28")
                self.imgslave2 = self.imgR
                imgy = VisionSystem.resize_to_square(self.imgslave2, 800)
                self.total_manchas_R = VisionSystem.contar_subcontornos_en_roi(imgy,458,408,253,291,10,0)
                self.addToMsgList(f"Manchas totales: {self.total_manchas_R}",self.ui.listWidget_R,self.listWidgetItemsR)#print(f"manchas totales {self.manchas}")

                if self.total_manchas_R > 0:
                    self.test_failR = True
                    self.test_passR = not self.test_failR
                    self.ui.lineEdit_status_R.setText("Manchas")
                else:
                    self.test_passR = True
                    self.test_failR = not self.test_passR
                self.test_step = 30#Move to the next step
                
            #====================================================
            #====================================================
            #====== MUESTRA LAS IMAGENES EN LOS LADOS L Y R =====
            #====================================================
            elif self.test_step == 30:       # Show The image                   
                self.visionL.frameToShow = self.imgslave.copy()
                self.set_image(self.imgslave, self.ui.label_img_L)
                self.visionR.frameToShow = self.imgslave2.copy()
                self.set_image(self.imgslave2, self.ui.label_img_R)
                self.test_step = 40 #Move to the next step
                
                
            elif self.test_step == 40:       # Save Data Output
                print("Saving to Database")
                self.addToMsgList("Save to DB", self.ui.listWidget_L, self.listWidgetItemsL)
                self.addToMsgList("Save to DB", self.ui.listWidget_R, self.listWidgetItemsR)
                logOKL = self.glblMgr.InsertFugaDeLuzLogRecord(Log = self.logDataL)
                logOKR = self.glblMgr.InsertFugaDeLuzLogRecord(Log = self.logDataR)
                if logOKL:
                    self.addToMsgList("Save DB OK", self.ui.listWidget_L, self.listWidgetItemsL)
                else:
                    self.addToMsgList("Save DB NG", self.ui.listWidget_L, self.listWidgetItemsL)

                if logOKR:
                    self.addToMsgList("Save DB OK", self.ui.listWidget_R, self.listWidgetItemsR)
                else:
                    self.addToMsgList("Save DB NG", self.ui.listWidget_R, self.listWidgetItemsR)

                listLastTen = self.glblMgr.GetLastTenRecords()
                self.FillGrid(listLastTen)
                self.test_step = 50
                
                
            elif self.test_step == 50:       # paint good or bad color
                #Control de reusltado de prueba LADO L
                if self.test_passL and self.test_passL_luz and self.test_passL_muescas_L:
                    self.ui.lineEdit_status_L.setText("Pass")
                    self.addToMsgList("Test Good", self.ui.listWidget_L, self.listWidgetItemsL)
                    self.setCtlColor(self.ui.lineEdit_status_L, self.colors.GREEN)
                    self.ui.lineEdit_status_L.update()
                    self.MarkerL.setState(True)
                    sleep(.5)
                    self.MarkerL.setState(False)
                elif self.test_failL or self.test_failL_luz or self.test_failL_muescas_L :
                    self.ui.lineEdit_status_L.setText("Fail")
                    self.addToMsgList("Test Bad", self.ui.listWidget_L, self.listWidgetItemsL)
                    self.setCtlColor(self.ui.lineEdit_status_L, self.colors.RED)
                    self.ui.lineEdit_status_L.update()

                #Control de resultado de prueba LADO R
                if  self.test_passR and self.test_passR_luz and self.test_passR_muescas_R:
                    self.ui.lineEdit_status_R.setText("Pass")
                    self.addToMsgList("Test Good", self.ui.listWidget_R, self.listWidgetItemsR)
                    self.setCtlColor(self.ui.lineEdit_status_R, self.colors.GREEN)
                    self.ui.lineEdit_status_R.update()
                    self.MarkerR.setState(True)
                    sleep(.5)
                    self.MarkerR.setState(False)
                elif self.test_failR or self.test_failR_luz or  self.test_failR_muescasR:
                    self.ui.lineEdit_status_R.setText("Fail")
                    self.addToMsgList("Test Bad", self.ui.listWidget_R, self.listWidgetItemsR)
                    self.setCtlColor(self.ui.lineEdit_status_R, self.colors.RED)
                    self.ui.lineEdit_status_R.update()

                if self.test_failL or self.test_failR or self.test_failL_luz or self.test_failR_luz or self.test_failR_muescasR or self.test_failL_muescas_L:
                    Pass_ok = False
                    while not Pass_ok:
                        lock = FrmPassword(self.Password)
                        lock.exec()
                        Pass_ok = lock.PasswordOK

                if self.host_name == "piPaint01":
                    self.DoorClamp.setState(False)
                else:
                    self.ReleaseClamp.setState(True)
                    self.DoorClamp.setState(False)
                #self.DoorClamp.setState(False)

                self.InTest = False
                finish_test = True
                self.timer_test.stop()
                self.endTime = datetime.datetime.now()
                testTime = self.endTime - self.StartTime
                self.ui.txtCycleTime.setText(str(testTime.total_seconds()))
                self.addToMsgList("Waiting initial position", self.ui.listWidget_L, self.listWidgetItemsL)
                self.addToMsgList("Waiting initial position", self.ui.listWidget_R, self.listWidgetItemsR)
                self.timerMain_inUse = False

    def edit_mask(self):
        vision = self.visionL if self.Model == 'L' else self.visionR
        # take fresh image to pass without mask
        self.img = vision.trigger()
        self.frmMaskEdit.img = self.img

        self.frmMaskEdit.InnerRadius = self.innerRadiusL if self.Model == 'L' else self.innerRadiusR
        self.frmMaskEdit.OuterRadius = self.outterRadiusL if self.Model == 'L' else self.outterRadiusR
        self.frmMaskEdit.xCoord = self.CircleCenterPointL[0] if self.Model == 'L' else self.CircleCenterPointR[0]
        self.frmMaskEdit.yCoord = self.CircleCenterPointL[1] if self.Model == 'L' else self.CircleCenterPointR[1]
        self.frmMaskEdit.apply_mask(self.frmMaskEdit.img)
        self.frmMaskEdit.exec()
        if self.frmMaskEdit.save == True:
            if self.Model == 'L':
                self.innerRadiusL = self.frmMaskEdit.InnerRadius
                self.outterRadiusL = self.frmMaskEdit.OuterRadius
                self.CircleCenterPointL[0] = self.frmMaskEdit.xCoord
                self.CircleCenterPointL[1] = self.frmMaskEdit.yCoord
                
            elif self.Model == 'R':
                self.innerRadiusR = self.frmMaskEdit.InnerRadius
                self.outterRadiusR = self.frmMaskEdit.OuterRadius
                self.CircleCenterPointR[0] = self.frmMaskEdit.xCoord
                self.CircleCenterPointR[1] = self.frmMaskEdit.yCoord

            self.save_maskParameters()

    def save_maskParameters(self):
        value_Inner = self.innerRadiusL if self.Model == 'L' else self.innerRadiusR
        param_Inner = 'InnerRadius'
        value_Outter = self.outterRadiusL if self.Model == 'L' else self.outterRadiusR
        param_Outter = 'OutterRadius'
        value_cx = self.CircleCenterPointL[0] if self.Model == 'L' else self.CircleCenterPointR[0]
        param_cx = 'CenterX'
        value_cy = self.CircleCenterPointL[1] if self.Model == 'L' else self.CircleCenterPointR[1]
        param_cy = 'CenterY'
        ModelParam = 0
        modelo = 'DL' if self.ModelInProcess.endswith("L") else 'DR'
        if modelo == 'DL':
            ModelParam = 1
        elif modelo == 'DR':
            ModelParam = 2

        Inner_ok = self.glblMgr.saveParam(self.Equip, param_Inner, value_Inner, ModelParam)
        Outter_ok = self.glblMgr.saveParam(self.Equip, param_Outter, value_Outter, ModelParam)
        CX_ok = self.glblMgr.saveParam(self.Equip, param_cx, value_cx, ModelParam)
        CY_ok = self.glblMgr.saveParam(self.Equip, param_cy, value_cy, ModelParam)

        if Inner_ok and Outter_ok and CX_ok and CY_ok:
            self.show_messagebox('Succes!', "Configuration Succesfully saved")
        else:
            self.show_messagebox('Error', "Could not Save the configuration")

    def adjust_parameters(self):
        vision = self.visionL if self.Model == 'L' else self.visionR
        # Take Fresh image to adjutst Parameters
        self.img = vision.trigger()
        # self.img = self.vision.Open_image(u'LightLeakCut.bmp')
        if self.Model == 'L':
            self.img = vision.extract_composite_circle_bitwise(self.img, self.CircleCenterPointL, self.innerRadiusL, self.outterRadiusL, debug=False)
            self.frmAdjustParams.img = self.img
            self.frmAdjustParams.blue_MaxSat = self.BlueSatMaxL
            self.frmAdjustParams.blue_MinValue = self.BlueValueMinL
            self.frmAdjustParams.red_MaxSat = self.RedSatMaxL
            self.frmAdjustParams.red_MinValue = self.RedValueMinL

            self.frmAdjustParams.blue_MinSat = self.BlueSatMinL
            self.frmAdjustParams.blue_MaxValue = self.BlueValueMaxL
            self.frmAdjustParams.red_MinSat = self.RedSatMinL
            self.frmAdjustParams.red_MaxValue = self.RedValueMaxL

            self.frmAdjustParams.HlsSatMin = self.HlsSatMinL
            self.frmAdjustParams.HlsSatMax = self.HlsSatMaxL
            self.frmAdjustParams.HlsLightMin = self.HlsLightMinL
            self.frmAdjustParams.HlsLightMax = self.HlsLightMaxL
        else:
            self.img = vision.extract_composite_circle_bitwise(self.img, self.CircleCenterPointR, self.innerRadiusR, self.outterRadiusR, debug=False)
            self.frmAdjustParams.img = self.img
            self.frmAdjustParams.blue_MaxSat = self.BlueSatMaxR
            self.frmAdjustParams.blue_MinValue = self.BlueValueMinR
            self.frmAdjustParams.red_MaxSat = self.RedSatMaxR
            self.frmAdjustParams.red_MinValue = self.RedValueMinR

            self.frmAdjustParams.blue_MinSat = self.BlueSatMinR
            self.frmAdjustParams.blue_MaxValue = self.BlueValueMaxR
            self.frmAdjustParams.red_MinSat = self.RedSatMinR
            self.frmAdjustParams.red_MaxValue = self.RedValueMaxR

            self.frmAdjustParams.HlsSatMin = self.HlsSatMinR
            self.frmAdjustParams.HlsSatMax = self.HlsSatMaxR
            self.frmAdjustParams.HlsLightMin = self.HlsLightMinR
            self.frmAdjustParams.HlsLightMax = self.HlsLightMaxR

        self.frmAdjustParams.vision = vision
        self.frmAdjustParams.ui.rbRedFeatures.setChecked(True)
        self.frmAdjustParams.extract_features(self.frmAdjustParams.img)
        self.frmAdjustParams.exec()

        if self.frmAdjustParams.save == True:
            if self.Model == 'L':
                self.BlueSatMaxL = self.frmAdjustParams.blue_MaxSat
                self.BlueSatMinL = self.frmAdjustParams.blue_MinSat
                self.BlueValueMinL = self.frmAdjustParams.blue_MinValue
                self.BlueValueMaxL = self.frmAdjustParams.blue_MaxValue
                self.RedSatMaxL = self.frmAdjustParams.red_MaxSat
                self.RedSatMinL = self.frmAdjustParams.red_MinSat
                self.RedValueMinL = self.frmAdjustParams.red_MinValue
                self.RedValueMaxL = self.frmAdjustParams.red_MaxValue
                self.HlsSatMinL = self.frmAdjustParams.HlsSatMin
                self.HlsSatMaxL = self.frmAdjustParams.HlsSatMax
                self.HlsLightMinL = self.frmAdjustParams.HlsLightMin
                self.HlsLightMaxL = self.frmAdjustParams.HlsLightMax
            elif self.Model == 'R':
                self.BlueSatMaxR = self.frmAdjustParams.blue_MaxSat
                self.BlueSatMinR = self.frmAdjustParams.blue_MinSat
                self.BlueValueMinR = self.frmAdjustParams.blue_MinValue
                self.BlueValueMaxR = self.frmAdjustParams.blue_MaxValue
                self.RedSatMaxR = self.frmAdjustParams.red_MaxSat
                self.RedSatMinR = self.frmAdjustParams.red_MinSat
                self.RedValueMinR = self.frmAdjustParams.red_MinValue
                self.RedValueMaxR = self.frmAdjustParams.red_MaxValue
                self.HlsSatMinR = self.frmAdjustParams.HlsSatMin
                self.HlsSatMaxR = self.frmAdjustParams.HlsSatMax
                self.HlsLightMinR = self.frmAdjustParams.HlsLightMin
                self.HlsLightMaxR = self.frmAdjustParams.HlsLightMax
            self.save_VisionParameters()
            self.frmAdjustParams.save = False
        self.load_params()

    def adjust_mask(self):
        vision = self.visionL if self.Model == 'L' else self.visionR
        if self.img is not None:
            self.frmAdjustParams.img = self.img
        else:
            self.img = vision.trigger()
            # self.img = self.vision.Open_image(u'LightLeakCut.bmp')
            self.img = vision.extract_composite_circle_bitwise(self.img, self.CircleCenterPointL, self.innerRadiusL, self.outterRadiusL, debug=False)
            self.frmAdjustParams.img = self.img
        self.frmAdjustParams.blue_MaxSat = self.BlueSatMaxL
        self.frmAdjustParams.blue_MinValue = self.BlueValueMinL
        self.frmAdjustParams.red_MaxSat = self.RedSatMaxL
        self.frmAdjustParams.red_MinValue = self.RedValueMinL

        self.frmAdjustParams.blue_MinSat = self.BlueSatMinL
        self.frmAdjustParams.blue_MaxValue = self.BlueValueMaxL
        self.frmAdjustParams.red_MinSat = self.RedSatMinL
        self.frmAdjustParams.red_MaxValue = self.RedValueMaxL

        self.frmAdjustParams.HlsSatMin = self.HlsSatMinL
        self.frmAdjustParams.HlsSatMax = self.HlsSatMaxL
        self.frmAdjustParams.HlsLightMin = self.HlsLightMinL
        self.frmAdjustParams.HlsLightMax = self.HlsLightMaxL

        self.frmAdjustParams.vision = vision
        self.frmAdjustParams.ui.rbRedFeatures.setChecked(True)
        self.frmAdjustParams.extract_features(self.frmAdjustParams.img)
        self.frmAdjustParams.exec()

        if self.frmAdjustParams.save == True:
            if self.Model == 'L':
                self.BlueSatMaxL = self.frmAdjustParams.blue_MaxSat
                self.BlueSatMinL = self.frmAdjustParams.blue_MinSat
                self.BlueValueMinL = self.frmAdjustParams.blue_MinValue
                self.BlueValueMaxL = self.frmAdjustParams.blue_MaxValue
                self.RedSatMaxL = self.frmAdjustParams.red_MaxSat
                self.RedSatMinL = self.frmAdjustParams.red_MinSat
                self.RedValueMinL = self.frmAdjustParams.red_MinValue
                self.RedValueMaxL = self.frmAdjustParams.red_MaxValue
                self.HlsSatMinL = self.frmAdjustParams.HlsSatMin
                self.HlsSatMaxL = self.frmAdjustParams.HlsSatMax
                self.HlsLightMinL = self.frmAdjustParams.HlsLightMin
                self.HlsLightMaxL = self.frmAdjustParams.HlsLightMax
            elif self.Model == 'R':
                self.BlueSatMaxR = self.frmAdjustParams.blue_MaxSat
                self.BlueSatMinR = self.frmAdjustParams.blue_MinSat
                self.BlueValueMinR = self.frmAdjustParams.blue_MinValue
                self.BlueValueMaxR = self.frmAdjustParams.blue_MaxValue
                self.RedSatMaxR = self.frmAdjustParams.red_MaxSat
                self.RedSatMinR = self.frmAdjustParams.red_MinSat
                self.RedValueMinR = self.frmAdjustParams.red_MinValue
                self.RedValueMaxR = self.frmAdjustParams.red_MaxValue
                self.HlsSatMinR = self.frmAdjustParams.HlsSatMin
                self.HlsSatMaxR = self.frmAdjustParams.HlsSatMax
                self.HlsLightMinR = self.frmAdjustParams.HlsLightMin
                self.HlsLightMaxR = self.frmAdjustParams.HlsLightMax
            self.save_VisionParameters()
            self.frmAdjustParams.save = False
        self.load_params()

    def unlock_parameters(self):
        if self.ui.btnUnlockParameters.isChecked():
            frmPassword = FrmPassword(self.Password)
            frmPassword.exec()

            if frmPassword.PasswordOK:
                # self.ui.SliderThreshold.setEnabled(True)
                self.ui.txtCenterPointX.setEnabled(True)
                self.ui.txtCenterPointY.setEnabled(True)
                # self.ui.SliderInnerRadius.setEnabled(True)
                # self.ui.SliderOutterRadius.setEnabled(True)
                self.ui.btnSaveThreshold.setEnabled(True)
                self.ui.btnManualInspection.setEnabled(True)
                self.ui.btnAdjustInpsection.setEnabled(True)
                self.ui.btnIniciar.setEnabled(True)
                self.ui.btnUnlockParameters.setText("    Lock Parameters")

                self.ui.btn_DoorClamp.setEnabled(True)
                self.ui.btn_MarkerL.setEnabled(True)
                self.ui.btn_MarkerR.setEnabled(True)
                self.ui.btn_Spare0.setEnabled(True)
                self.ui.btn_Spare1.setEnabled(True)
                self.ui.btn_Spare2.setEnabled(True)
                self.ui.btn_Spare3.setEnabled(True)
                self.ui.btn_Spare4.setEnabled(True)
                
        else:
            # self.ui.SliderThreshold.setEnabled(False)
            self.ui.txtCenterPointX.setEnabled(False)
            self.ui.txtCenterPointY.setEnabled(False)
            # self.ui.SliderInnerRadius.setEnabled(False)
            # self.ui.SliderOutterRadius.setEnabled(False)
            self.ui.btnSaveThreshold.setEnabled(False)
            self.ui.btnManualInspection.setEnabled(False)
            self.ui.btnAdjustInpsection.setEnabled(False)
            self.ui.btnIniciar.setEnabled(False)
            self.ui.btnUnlockParameters.setText("    Unlock Parameters")

            self.ui.btn_DoorClamp.setEnabled(False)
            self.ui.btn_MarkerL.setEnabled(False)
            self.ui.btn_MarkerR.setEnabled(False)
            self.ui.btn_Spare0.setEnabled(False)
            self.ui.btn_Spare1.setEnabled(False)
            self.ui.btn_Spare2.setEnabled(False)
            self.ui.btn_Spare3.setEnabled(False)
            self.ui.btn_Spare4.setEnabled(False)
                

        pass


if __name__=="__main__":
    app = QApplication(sys.argv)
    win = UI()
    win.show()
    center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
    geo = win.frameGeometry()
    geo.moveCenter(center)
    win.move(geo.topLeft())
    app.exec()
