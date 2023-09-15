##organizar libs e criar um novo ambiente virtual contendo apenas as bibliotecas necessarias
from PyQt5 import *
from PyQt5 import Qt
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QDate, QTime, QFile
from PyQt5.QtCore import QThread, QSocketNotifier, pyqtSignal, QObject
from PyQt5.QtNetwork import QTcpSocket
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtPrintSupport import *
#from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QStatusBar
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy

#uvboost bibliotecas
import numpy as np
import pandas as pd
from catboost.core import CatBoostRegressor
from catboost import CatBoost
#from pathlib import Path
#import timeit

import os #, sys
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
#from matplotlib.colors import ListedColormap, LinearSegmentedColormap
#from matplotlib import cm 
#import matplotlib.ticker as mticker
#import cartopy
import cartopy.crs as ccrs               
import cartopy.feature as cfeature        
#import cartopy.io.shapereader as shpreader 
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
#from matplotlib.figure import Figure
import geocoder #lib para obter localização por IP
import datetime #obter data e hora
import shutil
import math
import socket

#tela principal
from gui_uv_boost import Ui_MainWindow

#============================================================================================
def verificar_conexao_rede():
    try:
        # Tenta criar uma conexão com um host externo (neste caso, o google.com)
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

# Chamando a função para verificar a conexão
if verificar_conexao_rede():
    print("Conectado à rede.")
    # Obtém a localização atual do computador
    g = geocoder.ip('me')
    #Localização por IP
    latlon = g.latlng
else:
    print("Desconectado da rede.")
    latlon = [0, 0]

# Obtenha a data e hora atual
data_hora_atual = datetime.datetime.now()

dia = int(data_hora_atual.strftime('%d'))
mes = int(data_hora_atual.strftime('%m'))
ano = int(data_hora_atual.strftime('%Y'))
hor = int(data_hora_atual.strftime('%H'))
min = int(data_hora_atual.strftime('%M'))

csv_input = 0 #modo csv desligado
#============================================================================================
class MapWidget(QWidget):
    sinal = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        global latlon

        # Crie a figura para o mapa
        self.fig = plt.figure(figsize=(6,10), facecolor='#EFEFEF')
        self.canvas = FigureCanvas(self.fig)
        self.fig.patch.set_alpha(1)

        # Adicione a figura ao layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Adicione o mapa à figura
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())

        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        
        img = plt.imread('doc/img/map.png')
        img_extent = (-180, 180, -90, 90)
        self.ax.imshow(img, origin='upper', extent=img_extent, transform=ccrs.PlateCarree())

        #self.ax.stock_img()
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.5, color='black')
        self.ax.coastlines(color='black', linestyle='-', alpha=1, linewidth=0.5)
        self.ax.set_frame_on(False)
        self.ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.7, linestyle='--')
       
        # Crie uma variável para armazenar o ponto anterior
        self.previous_point_1 = None
        self.previous_point_2 = None
        self.previous_point_3 = None

        # Plote um ponto no mapa nas coordenadas clicadas
        lat = latlon[0]
        lon = latlon[1]

        self.previous_point_1 = self.ax.plot(lon, lat+4, marker='v', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
        self.previous_point_2 = self.ax.plot(lon, lat+9, marker='o', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
        self.previous_point_3 = self.ax.plot(lon, lat+8.7, marker='o', color='white', markersize=5, transform=ccrs.PlateCarree())[0]

        # Conecte o evento de clique do mouse
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        global latlon

        if event.inaxes == self.ax:
            # Obtenha as coordenadas do clique
            lon, lat = self.ax.projection.transform_point(event.xdata, event.ydata, ccrs.PlateCarree())
            latlon = [lat, lon]

            # Remova o ponto anterior, se houver
            if self.previous_point_1 is not None:
                self.previous_point_1.remove()

            if self.previous_point_2 is not None:
                self.previous_point_2.remove()
            
            if self.previous_point_3 is not None:
                self.previous_point_3.remove()

            # Plote um ponto no mapa nas coordenadas clicadas
            self.previous_point_1 = self.ax.plot(lon, lat+4, marker='v', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
            self.previous_point_2 = self.ax.plot(lon, lat+9, marker='o', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
            self.previous_point_3 = self.ax.plot(lon, lat+8.7, marker='o', color='white', markersize=5, transform=ccrs.PlateCarree())[0]

            # Atualize o canvas
            self.canvas.draw()
            sinal_end = True
            self.sinal.emit(sinal_end)

class MainWindow(QMainWindow, Ui_MainWindow, QThread, MapWidget):    
    def __init__(self):
        super(MainWindow, self).__init__()

        global latlon, dia, mes, ano, hor, min
    
        self.setupUi(self)

        self.setWindowTitle('UV Boost')
        self.setMaximumSize(650, 650)
        self.setMinimumSize(650, 650)

        # Carrega o arquivo de estilo externo
        style_file = QFile("doc/style/qss_uvboost.qss")
        style_file.open(QFile.ReadOnly | QFile.Text)
        style_sheet = style_file.readAll().data().decode()

        self.setStyleSheet(style_sheet)
#==================================================================//BODY SIZE
        self.label.setMaximumSize(632,50)
        self.label.setMinimumSize(632,50) 
        self.label_2.setMaximumSize(300,30)
        self.label_2.setMinimumSize(300,30)
        self.label_3.setMaximumSize(300,30)
        self.label_3.setMinimumSize(300,30) 
        self.lineEdit.setMaximumSize(200,30)
        self.lineEdit.setMinimumSize(200,30)  
        self.lineEdit_2.setMaximumSize(200,30)
        self.lineEdit_2.setMinimumSize(200,30) 
        self.label_4.setMaximumSize(256,40)
        self.label_4.setMinimumSize(256,40)
        self.label_13.setMaximumSize(240,40)
        self.label_13.setMinimumSize(240,40)

        self.pushButton_3.setText('')
        img_off = QPixmap('doc/img/off.png')
        self.pushButton_3.setIconSize(img_off.size())
        self.pushButton_3.setIcon(QIcon(img_off))

        self.label_7.setMaximumSize(150,30)
        self.label_7.setMinimumSize(150,30)   
        self.dateEdit.setMaximumSize(100,30)
        self.dateEdit.setMinimumSize(100,30)
        self.label_9.setMaximumSize(150,30)
        self.label_9.setMinimumSize(150,30)
        self.lineEdit_5.setMaximumSize(100,30)
        self.lineEdit_5.setMinimumSize(100,30)
        self.label_5.setMaximumSize(150,30)
        self.label_5.setMinimumSize(150,30)
        self.lineEdit_3.setMaximumSize(100,30)
        self.lineEdit_3.setMinimumSize(100,30)
        self.label_8.setMaximumSize(240,30)
        self.label_8.setMinimumSize(240,30)
        self.timeEdit.setMaximumSize(100,30)
        self.timeEdit.setMinimumSize(100,30)
        self.label_10.setMaximumSize(240,30)
        self.label_10.setMinimumSize(240,30)
        self.lineEdit_6.setMaximumSize(100,30)
        self.lineEdit_6.setMinimumSize(100,30)
        self.label_6.setMaximumSize(240,30)
        self.label_6.setMinimumSize(240,30)
        self.lineEdit_4.setMaximumSize(100,30)
        self.lineEdit_4.setMinimumSize(100,30)
        self.label_12.setMaximumSize(300,30)
        self.label_12.setMinimumSize(300,30)
        self.lineEdit_7.setMaximumSize(300,30)
        self.lineEdit_7.setMinimumSize(300,30)
        self.pushButton_2.setMaximumSize(30,30)
        self.pushButton_2.setMinimumSize(30,30)
        self.pushButton.setMaximumSize(632,30)
        self.pushButton.setMinimumSize(632,30)
#======================================================================//
        #plota o mapa interativo
        self.label_11.setText('')
        vbox = QVBoxLayout()
        self.label_11.setLayout(vbox)
        map_canvas = MapWidget()
        vbox.addWidget(map_canvas)
      
        #atualiza as label de lat e lon
        map_canvas.sinal.connect(self.latlon_func)

        Lat = format(latlon[0], '.2f')
        Lon = format(latlon[1], '.2f')
        self.lineEdit_3.setText(str(Lat))
        self.lineEdit_4.setText(str(Lon))

        self.lineEdit_3.textEdited.connect(self.latlon_line)  
        self.lineEdit_4.textEdited.connect(self.latlon_line)

        #===================================
        #data
        data = QDate(ano, mes, dia)
        self.dateEdit.setDate(data)
        self.dateEdit.dateChanged.connect(self.data_atualizada)
        #hora
        hora = QTime(hor, min)
        self.timeEdit.setTime(hora)
        self.timeEdit.timeChanged.connect(self.hora_atualizada)

        self.pushButton.clicked.connect(self.Run)

        self.pushButton_3.clicked.connect(self.modo)

        self.pushButton_2.clicked.connect(self.caminho_csv)

    def caminho_csv(self):
        caminho_csv = QtWidgets.QFileDialog().getOpenFileName()
        caminho_csv = caminho_csv[0]

        extenção = os.path.splitext(caminho_csv)
        extenção = extenção[1]

        self.lineEdit_7.setText(caminho_csv)

        csv_file = caminho_csv.split('/')
        csv_file = csv_file[-1]

        diretorio_atual = os.getcwd()

        # Verificar se o arquivo está no diretório atual
        caminho_arquivo = os.path.join(diretorio_atual, csv_file)
        if extenção != '.csv':
            self.lineEdit_7.setText('arquivo incompativel')
        else:
            if os.path.isfile(caminho_arquivo):
                print(csv_file, 'ok')
            else:
                print(csv_file)
                shutil.copy(caminho_csv, './')        

    def modo(self):
        global csv_input

        if csv_input == 1:
            csv_input = 0
            
            self.pushButton_3.setText('')
            img_off = QPixmap('doc/img/off.png')
            self.pushButton_3.setIconSize(img_off.size())
            self.pushButton_3.setIcon(QIcon(img_off))
        else:
            csv_input = 1

            self.pushButton_3.setText('')
            img_off = QPixmap('doc/img/on.png')
            self.pushButton_3.setIconSize(img_off.size())
            self.pushButton_3.setIcon(QIcon(img_off))

    def Run(self):
        global csv_input, dia, mes, ano, hor, min

        dia, mes, ano, hor, min = int(dia), int(mes), int(ano), int(hor), int(min)

        #variaveis
        lat = self.lineEdit_3.text()
        if lat == '':
            lat = float(0)
            self.lineEdit_3.setText('0')
        else:
            try:
                lat = float(lat)
            except ValueError:
                lat = float(0)
                self.lineEdit_3.setText('0')

        lon = self.lineEdit_4.text()
        if lon == '':
            lon = float(0)
            self.lineEdit_4.setText('0')
        else:
            try:
                lon = float(lon)
            except ValueError:
                lon = float(0)
                self.lineEdit_4.setText('0')
            
        ozone = self.lineEdit_5.text()
        try:
            ozone = float(ozone)
        except ValueError:
            ozone = float(0)
            self.lineEdit_5.setText('0')
        
        aod = self.lineEdit_6.text()
        try:
            aod = float(aod)
        except ValueError:
            aod = float(0)
            self.lineEdit_6.setText('0')
    
        #calcular o sza
        data_hora = datetime.datetime(ano, mes, dia, hor, min, 0)
        
        # Converter a latitude e longitude de graus para radianos
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        # Obter o dia do ano
        dia_ano = data_hora.timetuple().tm_yday

        # Calcular a declinação solar
        declinacao_solar = 23.45 * math.sin(math.radians(360.0 / 365.0 * (284 + dia_ano)))

        # Calcular a diferença entre a hora local e o tempo solar médio em horas
        diferenca_tempo = data_hora.hour - 12 + data_hora.minute / 60 + data_hora.second / 3600

        # Calcular o ângulo do zênite solar
        angulo_zenite = math.degrees(math.acos(math.sin(lat_rad) * math.sin(math.radians(declinacao_solar)) +
                                                math.cos(lat_rad) * math.cos(math.radians(declinacao_solar)) *
                                                math.cos(math.radians(15 * diferenca_tempo))))

        #load_model
        UVBoost = CatBoost()
        UVBoost_D = CatBoost()
        UVBoost.load_model("UVBoost.model")
        UVBoost_D.load_model("UVBoost_D.model")
    
        #caminho CSV
        csv_file = self.lineEdit_7.text()
        csv_file = csv_file.split('/')
        csv_file = csv_file[-1]
#=============================================================================/UV_Boost
        if csv_input == 1:
            namefile = csv_file
            df = pd.read_csv(namefile,sep=';',header=0)
            df_inp = df.iloc[:, [0,1,2]].values
        else:
            sza = angulo_zenite
            df_inp = np.array([sza,ozone,aod])
    
        UV_fct = UVBoost.predict(df_inp)
        UV_fct_D = UVBoost_D.predict(df_inp)

        # Saving the information
        if csv_input == 1:
            data1 = np.array([UV_fct]).T
            data2 = np.array([UV_fct_D]).T

            data1 = data1*40
            
            df_UIV = pd.DataFrame(data1, columns=['UVI'])
            df_VitD = pd.DataFrame(data2, columns=['VitD'])
        
            df_inp = pd.DataFrame(df_inp, columns=['SZA','CTO','AOD'])
            df = pd.concat([df_inp, df_UIV, df_VitD],axis=1)

            outputfile = 'OUT_'+ namefile

            df.to_csv(outputfile)

        else:
            if UV_fct < 0:
                UV_fct = 0

            if UV_fct_D < 0:
                UV_fct_D = 0
            
            Ultraviolet_Index = UV_fct*40
            Ultraviolet_Index = "{:.{}f}".format(Ultraviolet_Index, 1)
            Ultraviolet_Index = str(Ultraviolet_Index)
            Vitamin_D_weighted_irradiances  = UV_fct_D
            Vitamin_D_weighted_irradiances = "{:.{}f}".format(Vitamin_D_weighted_irradiances, 3)
            Vitamin_D_weighted_irradiances  = str(Vitamin_D_weighted_irradiances)

            self.lineEdit.setText(Ultraviolet_Index)
            self.lineEdit_2.setText(Vitamin_D_weighted_irradiances + ' (W/m2)')
        
    def hora_atualizada(self):
        global hor, min
        
        hora = self.timeEdit.text()
        hora = hora.split(':')
        hor = hora[0]
        min = hora[1]
        print(hor, min)

    def data_atualizada(self):
        global dia, mes, ano
        
        data = self.dateEdit.text()
        data = data.split('/')
        dia = data[0]
        mes = data[1]
        ano = data[2]

    def latlon_line(self):
        global latlon

        lat = self.lineEdit_3.text()
        lon = self.lineEdit_4.text()
        
        try:
            if lat == '':
                lat = '0'
                lat = float(lat)
            else:
                if lat[0] == '-' and len(lat) >= 2:
                    lat = float(lat.replace("-", "")) * -1
                elif lat == '-':
                    lat = '0'
                    lat = float(lat)                
                else:
                    lat = float(lat)
        except ValueError:
            lat = '0'
            lat = float(lat)
        
        try:
            if lon == '':
                lon = '0'
                lon = float(lon)
            else:
                if lon[0] == '-' and len(lon) >= 2:
                    l0n = float(lon.replace("-", "")) * -1
                elif lon == '-':
                    lon = '0'
                    lon = float(lon)                
                else:
                    lon = float(lon)
        except ValueError:
            lon = '0'
            lon = float(lon)

        lon_ = float(lon) - 360
        # Acesse o widget do mapa
        map_widget = self.label_11.layout().itemAt(0).widget()

        # Remova o ponto anterior, se houver
        if map_widget.previous_point_1 is not None:
            map_widget.previous_point_1.remove()

        if map_widget.previous_point_2 is not None:
            map_widget.previous_point_2.remove()

        if map_widget.previous_point_3 is not None:
            map_widget.previous_point_3.remove()

        # Plote o ponto no mapa nas coordenadas desejadas
        map_widget.previous_point_1 = map_widget.ax.plot(lon_, lat+4, marker='v', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
        map_widget.previous_point_2 = map_widget.ax.plot(lon_, lat+9, marker='o', color='red', markersize=10, transform=ccrs.PlateCarree())[0]
        map_widget.previous_point_3 = map_widget.ax.plot(lon_, lat+8.7, marker='o', color='white', markersize=5, transform=ccrs.PlateCarree())[0]
      
        # Atualize o canvas
        map_widget.canvas.draw()

    def latlon_func(self, concluida):
        global latlon
    
        Lat = format(latlon[0], '.2f')
        Lon = format(latlon[1], '.2f')
        self.lineEdit_3.setText(str(Lat))
        self.lineEdit_4.setText(str(Lon))

if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()
