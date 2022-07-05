import webrtcvad
import pyaudio
import wave
from warnings import simplefilter
from threading import Thread
from music21 import stream as m21stream
import audio2note
    
simplefilter(action='ignore', category=FutureWarning)

class Recorder:
    def __init__(self, outputFile, scoreFile):
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(2)
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 22050
        self.CHUNK = 1024
        self.RECORD_SECONDS = 3
        self.WAVE_OUTPUT_FILENAME = outputFile
        self.SCORE_PATH = scoreFile
        self.recording = False

    def setup(self, deviceChoice):
        self.audio = pyaudio.PyAudio()

        # info = self.audio.get_host_api_info_by_index(0)
        # numdevices = info.get('deviceCount')
        # defaultIndex = 0

        # # show all input devices found.
        # for i in range(0, numdevices):
        #     if (self.audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        #         print("Input Device id ", i, " - ", self.audio.get_device_info_by_host_api_device_index(0, i).get('name'))
        #         if self.audio.get_device_info_by_host_api_device_index(0, i).get('name') == "default":
        #             defaultIndex = i

        # # request the desired device to use as input. If none is selected we use the default.
        # userInput = input("Select an input device (or hit enter to use default): ")

        # chosenDevice = defaultIndex
        # if userInput != '':
        #     chosenDevice = int(userInput)

        # print("chosen device: {} - {}".format(chosenDevice, self.audio.get_device_info_by_host_api_device_index(0, chosenDevice).get('name')))

        self.stream = self.audio.open(format=self.FORMAT, channels=self.CHANNELS,
                rate=self.RATE, input=True,
                frames_per_buffer=self.CHUNK, input_device_index=deviceChoice)

    def record(self, note_q):
        self.recording = True
        self.noteStream = m21stream.Stream()

        while self.recording == True:
            frames = []
            print("recording...")
            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                data = self.stream.read(self.CHUNK)
                frames.append(data)
            print("finished recording")

            waveFile = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
            waveFile.setnchannels(self.CHANNELS)
            waveFile.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            waveFile.setframerate(self.RATE)
            waveFile.writeframes(b''.join(frames))
            waveFile.close()

            processThread = Thread(target = audio2note.processAudio, args =(self.noteStream,note_q,self.WAVE_OUTPUT_FILENAME, self.SCORE_PATH))
            processThread.start()

    def stop(self):
        self.recording = False

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()


# rec = Recorder("file.wav", "score")
# rec.setup()
# recorderThread = Thread(target = rec.record, args =())

# # rec1 = Recorder("file1.wav", "score1")
# # rec1.setup()
# # recorderThread1 = Thread(target = rec1.record, args =())

# recorderThread.start()
# #recorderThread1.start()

# stopOpt = input("press 's' to stop: ")   
# if stopOpt == 's':
#     rec.stop()
#     rec.close()
#     #rec1.stop()
#     #rec1.close()
