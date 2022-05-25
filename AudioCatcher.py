import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import struct 
import librosa
import pyaudio as pa 
from scipy.fft import fft, ifft

class Audio:
    FRAMES = 1024*8                                   # Tamaño del paquete a procesar
    FORMAT = pa.paInt16                               # Formato de lectura INT 16 bits
    CHANNELS = 1
    Fs = 44100   
    
    def __init__(self) :
                                       # Frecuencia de muestreo típica para audi
        p = pa.PyAudio()
        stream = p.open(                                  # Abrimos el canal de audio con los parámeteros de configuración
                        format = FORMAT,
                        channels = CHANNELS,
                        rate = Fs,
                        input=True,
                        output=True,
                        frames_per_buffer=FRAMES
                    )
                                                ## Creamos una gráfica con 2 subplots y configuramos los ejes

        fig, (ax,ax1) = plt.subplots(2)
        x_audio = np.arange(0,FRAMES,1)
        x_fft = np.linspace(0, Fs, FRAMES)
        line, = ax.plot(x_audio, np.random.rand(FRAMES),'r')
        line_fft, = ax1.semilogx(x_fft, np.random.rand(FRAMES), 'b')
        ax.set_ylim(-32500,32500)
        ax.ser_xlim = (0,FRAMES)
        Fmin = 1
        Fmax = 5000
        ax1.set_xlim(Fmin,Fmax)
        fig.show()


    def startListen():
        F = (Fs/FRAMES)*np.arange(0,FRAMES//2)                 # Creamos el vector de frecuencia para encontrar la frecuencia dominante
i = 0
ant = 0
F_fund = 0.0
while True:
    
    data = stream.read(FRAMES)                         # Leemos paquetes de longitud FRAMES
    dataInt = struct.unpack(str(FRAMES) + 'h', data)   # Convertimos los datos que se encuentran empaquetados en bytes
    
    line.set_ydata(dataInt)                            # Asignamos los datos a la curva de la variación temporal

    M_gk = abs(fft(dataInt)/FRAMES)                    # Calculamos la FFT y la Magnitud de la FFT del paqute de datos
    ax1.set_ylim(0,np.max(M_gk+10)) 
    line_fft.set_ydata(M_gk)                           # Asigmanos la Magnitud de la FFT a la curva del espectro   
    M_gk = M_gk[0:FRAMES//2]                           # Tomamos la mitad del espectro para encontrar la Frecuencia Dominante
    Posm = np.where(M_gk == np.max(M_gk)) 
    F_fund = F[Posm]                                   # Encontramos la frecuencia que corresponde con el máximo de M_gk
    if ant != F_fund : 
        ant = F_fund
    else:
        i = i +1

    if i == 10 :
        nota = str(librosa.hz_to_note(F_fund))
        print(nota)
        
    elif i > 10 :
        i = 0        
    
    fig.canvas.draw()
    fig.canvas.flush_events()