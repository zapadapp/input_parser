import webrtcvad
import pyaudio
import wave
from warnings import simplefilter
from threading import Thread
from music21 import stream as m21stream
import time
import music21
from queue import Queue

# solve local imports
import os, sys
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, FILE_PATH)
import processAudio

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
        self.scoreFile = scoreFile

    def setup(self, deviceChoice):
        self.audio = pyaudio.PyAudio()
        self.deviceChoice = deviceChoice

    def record(self, note_q, detect, drawer):  
        if self.recording == True :
            print("Already recording")
            return  
        self.recording = True
        self.noteStream = m21stream.Stream()
        self.dataQ = Queue() 

        noteCO = ""
        timeCO = 0

        self.recDataThread = Thread(target = self.recData, args =()).start()

        while self.recording == True or self.dataQ.qsize != 0:
            frames = self.dataQ.get()
            waveFile = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
            waveFile.setnchannels(self.CHANNELS)
            waveFile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)
            waveFile.writeframes(b''.join(frames))
            waveFile.close()

            noteCO, timeCO = processAudio.processAudio(self.noteStream,drawer,note_q,self.WAVE_OUTPUT_FILENAME, self.SCORE_PATH, noteCO, timeCO,detect)
          
    def recData(self):
        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                        rate=self.RATE, input=True,
                        frames_per_buffer=self.CHUNK, input_device_index=self.deviceChoice)

        while self.recording == True:
            frames = []
            print("recording...")
            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                data = self.stream.read(self.CHUNK,exception_on_overflow=False) 
                frames.append(data)  
            print("finished recording")

            self.dataQ.put(frames)

    def stop(self):
        self.recording = False
        ## Small sleep to let recorder finish creating the file if necessary before cloging the stream
        time.sleep(self.RECORD_SECONDS)
        self.stream.stop_stream()

    def reproduce(self):
        fp = self.noteStream.write('midi', fp=os.path.join('files',self.scoreFile+'.mid'))
        fctr = 2 
        score = music21.converter.Converter()
        score.parseFile(fp)
        newscore = score.stream.augmentOrDiminish(fctr)
        newscore.show('midi') 
       
    def saveScore(self, path):
        self.noteStream.write('lily.png', fp=path)


    def close(self):     
        self.stream.close()
        self.audio.terminate()
