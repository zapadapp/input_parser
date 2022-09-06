import webrtcvad
import pyaudio
import wave
from warnings import simplefilter
from threading import Thread
from music21 import stream as m21stream
import time
# solve local imports
import os, sys
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, FILE_PATH)
import audio2note
import audio2chord
    
simplefilter(action='ignore', category=FutureWarning)

class Recorder:
    def __init__(self, outputFile, scoreFile):
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 22050
        self.CHUNK = 1024
        self.RECORD_SECONDS = 2
        self.WAVE_OUTPUT_FILENAME = outputFile
        self.SCORE_PATH = scoreFile
        self.recording = False

    def setup(self, deviceChoice):
        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                rate=self.RATE, input=True,
                frames_per_buffer=self.CHUNK, input_device_index=deviceChoice)

    def record(self, note_q, detect, drawer):  
        if self.recording == True :
            print("Pase Por aqui")
            return  
        self.recording = True
        self.noteStream = m21stream.Stream()

        while self.recording == True:
            frames = []
            print("recording...")
            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                data = self.stream.read(self.CHUNK,exception_on_overflow=False)
                frames.append(data)
            print("finished recording")

            waveFile = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
            waveFile.setnchannels(self.CHANNELS)
            waveFile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)
            waveFile.writeframes(b''.join(frames))
            waveFile.close()

            if detect == 'note':
                self.processThread = Thread(target = audio2note.processAudio, args =(self.noteStream,drawer,note_q,self.WAVE_OUTPUT_FILENAME, self.SCORE_PATH))
                self.processThread.start()
            else:
                self.processThread = Thread(target = audio2chord.processAudio, args =(self.noteStream,drawer, note_q,self.WAVE_OUTPUT_FILENAME, self.SCORE_PATH))
                self.processThread.start()
        ##CUANDO SE STOPEA, ESPERO QUE TERMINEN LOS THREADS DE TRABAJAR
        self.processThread.join()

    def stop(self):
        self.processThread.is_alive = False
        self.recording = False
        ## SE AGREGA SLEEP PARA ESPERAR QUE LOS THREADS TERMINEN SU TRABAJO 
        time.sleep(2)
        self.stream.stop_stream()

    def reproduce(self):
        self.noteStream.show("midi")   
       

    def close(self):     
        self.stream.close()
        self.audio.terminate()
