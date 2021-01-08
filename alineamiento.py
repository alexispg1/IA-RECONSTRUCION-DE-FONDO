import tkinter
import cv2
import numpy as np
import os.path
from tkinter import *
from tkinter import filedialog
from matplotlib import pyplot as plt
import glob

def select_video():
        vidcap = cv2.VideoCapture ("Evolucion.avi")
        currentframe = 0
        nombre = 0
        while(vidcap.isOpened()): 
            ret,frame = vidcap.read() 
            cv2.imshow('frame',frame)
            if cv2.waitKey(250) & 0xFF == ord("q"):
                break
        vidcap.release()


class SacarFondo():

    def __init__(self, alinear):
        if (alinear.get() == 1):
            imagenPromedio = self.promedioImagenes(0)
        else:
            imagenPromedio = self.promedioImagenes(1)
           
    
    def promedioImagenes(self, valor):
        arregloDeImagenes = [] #contendra n imagenes, n dado la cantidad de iteraciones
        imagenesParaVideo = [] #Imagenes resultantes que se usaran para la creacion del video

        framerate = 0.5
        path = tkinter.filedialog.askopenfilename(title="Selecciona el video deseado")
        alpha = float(alphaInto.get());
        frame_aux = None
        if len(path) > 0:
            vidcap = cv2.VideoCapture (path)
            currentframe = 0
            nombre = 0
            while(True): 
                vidcap.set(cv2.CAP_PROP_POS_MSEC,currentframe*1000)
                ret,frame = vidcap.read() 
                if ret: 
                    name = './imagenes/img' + str(nombre) + '.jpg'
                    arregloDeImagenes.append(frame)
                    nombre += 1
                    currentframe += framerate
                else: 
                    break

        #Permite seleccionar un segmento de la imagen inicial 
        fromCenter = False
        selectedZone = cv2.selectROI("Seleccione zona.", arregloDeImagenes[0], fromCenter)

        imagenesPasadas = 0 #cantidad de iteraciones hechas
       
        imagenPromedio = arregloDeImagenes[0] #Se selecciona la primer imagen del conjunto
        imagenesParaVideo.append(imagenPromedio) #Se añade el primer frame al video
        cv2.imwrite('iteracion' + str(0) + '.jpg', imagenPromedio) #Primera imagen de la evolucion
        #for de n interaciones, empieza en 1  int(iteraciones.get())
        if len(arregloDeImagenes) < 40:
            iteraciones = len(arregloDeImagenes)
        else:
            iteraciones = 40
        for t in range(1, iteraciones):
            
            frameSiguiente = arregloDeImagenes[t] #imagen que se operara con la imagen promedio
            #saber si se aplicara alineamiento
            if valor == 1:
                print(t)
                imagenPromedio = (alpha * imagenPromedio) + ( 1 - alpha) * frameSiguiente
            if valor == 0:
                imagenAlineada = self.alinearImagenes(imagenPromedio, frameSiguiente, selectedZone)
                imagenPromedio = (alpha * imagenPromedio) + ( 1 - alpha) * imagenAlineada
            imagenesParaVideo.append(imagenPromedio)
            cv2.imwrite('iteracion' + str(t) + '.jpg', imagenPromedio) #imagen de evolucion del proceso
            t += 1

        #Creacion del video
        img_array = []
        size = (1000, 1000)
        for filename in glob.glob('*.jpg'):
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width, height)
            img_array.append(img)
        out = cv2.VideoWriter('Evolucion.avi', cv2.VideoWriter_fourcc(*'DIVX'), 3, size)
        for i in range(len(img_array)):
            out.write(img_array[i])
        out.release()
        imagenPromedio = cv2.convertScaleAbs(imagenPromedio)

        cv2.imshow("Imagen Original", imagenPromedio)
        return imagenPromedio

    #Metodo para alinear imagenes
    def alinearImagenes(self, imagenPromedio, frameSiguiente, selectedZone):
        resultadoMenorDeComparacion = 999999999

        indicesDeMovimientoX = 0 #Que tanto se mueve la imagen en eje X
        indicesDeMovimientoY = 0 #Que tanto se mueve la imagen en eje Y

        tamano = imagenPromedio.shape #Tamaño de la imagen
        #Obtener la imagen de la seleccion
        segmentoDeImagenBuscado = imagenPromedio[selectedZone[1]:(selectedZone[1] + selectedZone[3]), selectedZone[0]:(selectedZone[0] + selectedZone[2])]
        #Se añade holgura a la seleccion, cuidando el tamaño maximo de la imagen
        holgura = 20
        seccionXE = int(selectedZone[0] - holgura)
        expansionMenorX = holgura
        while (seccionXE < 0):
            expansionMenorX = expansionMenorX - 1
            seccionXE = seccionXE + 1

        seccionXT = int((selectedZone[0] + selectedZone[2]) + holgura)
        if (seccionXT > tamano[1]):
            seccionXT = tamano[1]

        seccionYE = int(selectedZone[1] - holgura)
        expansionMenorY = holgura
        while (seccionYE < 0):
            expansionMenorY = expansionMenorY - 1
            seccionYE = seccionYE + 1

        seccionYT = int((selectedZone[1] + selectedZone[3]) + holgura)
        if (seccionYT > tamano[0]):
            seccionYT = tamano[0]

        sectorParaBuscarSegmento = frameSiguiente[seccionYE:seccionYT, seccionXE:seccionXT] #Secmento en el que se buscara el sector seleccionado de la imagen

        #segmentoDeImagenBuscado es el kernel actual 
        #sectorParaBuscarSegmento es el segmento que se buscara en la imagen siguiente
        for f in range(len(sectorParaBuscarSegmento) - len(segmentoDeImagenBuscado)):
            for c in range(len(sectorParaBuscarSegmento[0]) - len(segmentoDeImagenBuscado[0])):
                segmentoComparado = sectorParaBuscarSegmento[int(f):int(f + len(segmentoDeImagenBuscado)),
                                    int(c):int(c + len(segmentoDeImagenBuscado[0]))]

                # SSD  (imagenPromedio - frameActual)^2
                resultadoDeComparacion = (segmentoDeImagenBuscado - segmentoComparado) ** 2
                resultadoDeComparacion = np.sum(resultadoDeComparacion)
                #El resultado menor es el secmento que mas se aproxima a la imagen anterior
                if (resultadoMenorDeComparacion > resultadoDeComparacion):
                    resultadoMenorDeComparacion = resultadoDeComparacion
                    indicesDeMovimientoY = f #Actualizacion de movimiento en eje Y
                    indicesDeMovimientoX = c #Actualizacion de movimiento en eje X
        #movimiento verdadero
        desplazamientoX = indicesDeMovimientoX - (expansionMenorX)
        desplazamientoY = indicesDeMovimientoY - (expansionMenorY)
        #Actualizacion a movimineto real de la imagen entera
        if (desplazamientoX < 0):
            desplazamientoX = desplazamientoX * (-1)

        if (desplazamientoY < 0):
            desplazamientoY = desplazamientoY * (-1)

        desplazamientoX = int(desplazamientoX)
        desplazamientoY = int(desplazamientoY)

        imagenAlineada = np.zeros((len(frameSiguiente), len(frameSiguiente[0]), len(frameSiguiente[0][0])),np.uint8)
        #fusion de imagen nueva con anterior, localizando su convergencia 
        if (desplazamientoX >= 0):
            if (desplazamientoY >= 0):
                for g in range(0, len(frameSiguiente) - desplazamientoX):
                    for h in range(0, len(frameSiguiente[0]) - desplazamientoY):
                        imagenAlineada[g + desplazamientoX][h + desplazamientoY] = frameSiguiente[g][h]
            else:
                for g in range(0, len(frameSiguiente) - desplazamientoX):
                    for h in range(desplazamientoY, len(frameSiguiente[0])):
                        imagenAlineada[g + desplazamientoX][h - desplazamientoY] = frameSiguiente[g][h]
        else:
            if (desplazamientoY >= 0):
                for g in range(desplazamientoX, len(frameSiguiente)):
                    for h in range(0, len(frameSiguiente[0]) - desplazamientoY):
                        imagenAlineada[g - desplazamientoX][h + desplazamientoY] = frameSiguiente[g][h]
            else:
                for g in range(desplazamientoX, len(frameSiguiente)):
                    for h in range(desplazamientoY, len(frameSiguiente[0])):
                        imagenAlineada[g - desplazamientoX][h - desplazamientoY] = frameSiguiente[g][h]

        return imagenAlineada
   
def Start():
    s =SacarFondo(alinear)


w = tkinter.Tk()
w.geometry("500x300")
w.title("Sacar fondo")


alinear = IntVar()
ecualizar = IntVar()

C1 = Checkbutton(w, text="Alinear Imagenes", variable=alinear)
C1.pack()


label_titulo2 = tkinter.Label(w, text="Alpha", font='Helvetica 20 bold')
label_titulo2.pack()
alphaInto = tkinter.Entry(w)
alphaInto.insert(0, "0.12")
alphaInto.pack()


b3 = tkinter.Button(w, text="selecionar video", command=Start)
b3.pack()
b4 = tkinter.Button(w, text = "Reproducir video de evolucion", command = select_video)
b4.pack()

w.mainloop()