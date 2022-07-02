import webrtcvad
import pyaudio
import wave
import librosa
import numpy as np
from scipy.signal import find_peaks
from scipy.fft import fft
from warnings import simplefilter
from queue import Queue
from threading import Thread
from music21 import note,environment
from music21 import stream as m21stream

simplefilter(action='ignore', category=FutureWarning)

us = environment.UserSettings()
us['lilypondPath'] = '/usr/bin/lilypond'

vad = webrtcvad.Vad()
vad.set_mode(2)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 960
RECORD_SECONDS = 3
WAVE_OUTPUT_FILENAME = "file.wav"

audio = pyaudio.PyAudio()

info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
defaultIndex = 0

# show all input devices found.
for i in range(0, numdevices):
    if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", audio.get_device_info_by_host_api_device_index(0, i).get('name'))
        if audio.get_device_info_by_host_api_device_index(0, i).get('name') == "default":
            defaultIndex = i

# request the desired device to use as input. If none is selected we use the default.
userInput = input("Select an input device (or hit enter to use default): ")

chosenDevice = defaultIndex
if userInput != '':
    chosenDevice = int(userInput)

print("chosen device: {} - {}".format(chosenDevice, audio.get_device_info_by_host_api_device_index(0, chosenDevice).get('name')))

# start Recording input from selected device
stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK, input_device_index=chosenDevice)


q = Queue()
s = m21stream.Stream()

## Function that filters lower samples generated by input noise.
def filterLowSamples(samples):
    # find indexes of all elements lower than 2000 from samples
    indexes = np.where(samples < 2000)

    # remove elements for given indexes
    return np.delete(samples, indexes)

## Function that calculates the FFT of a part of an audio sample (part determined by indexes 'a' and 'b' of the parameterized samples) and finds 
## the fundamental frequency to get the corresponding note.
def detectAndPrintNote(q, y, sr, samples, a, b):
    # limit the audio input from sample in index a to sample in index b, unless b is 999 which means that it is the end of the audio data
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]
    
    # calculate FFT and absolute values
    X = fft(data)
    X_mag = np.absolute(X)

    # generate x values (frequencies)
    f = np.linspace(0, sr, len(X_mag))
    f_bins = int(len(X_mag)*0.1) 
    
    #plt.plot(f[:f_bins], X_mag[:f_bins])

    # find peaks in Y values. Use height value to filter lower peaks
    _, properties = find_peaks(X_mag, height=100)
    if len(properties['peak_heights']) > 0:
        y_peak = properties['peak_heights'][0]

        # get index for the peak
        peak_i = np.where(X_mag[:f_bins] == y_peak)

        # if we found an for a peak we print the note
        if len(peak_i) > 0:
            nota = convertToNote(str(librosa.hz_to_note(f[peak_i[0]])))
            print("Detected note: {}".format(nota))
            s.append(note.Note(nota))
            #print(s)
            q.put(s)
            #print("Detected note: {}".format(str(librosa.hz_to_note(f[peak_i[0]]))))
            return 

    #print("No detected note")            

def convertToNote(val) :
    nota = str.replace(str.replace(val, "['", ""), "']", "")
    if len(nota) == 3 :
        nota = nota[0] + "#" + nota[2]

    return nota


def consumer(in_q):
    while True:
        # Get some data
        s = in_q.get()
        print(s.write('lily.png', fp='tmp/score'))

consumerThread = Thread(target = consumer, args =(q, ))
consumerThread.start()

# change this as you see fit
audio_path = 'file.wav'
image_path = 'tmp/tmp.jpg'

def processAudio(q, y, sr):
    ############################################################
    ##############    Actual audio processing    ###############
    ############################################################

    # Note: we should be doing this in another thread so that we do not have to wait for this to finish to record another wave file.

    # generate image showing the audio input with the onset times
    #plt.figure(figsize=(14, 5))
    #librosa.display.waveshow(y, sr)

    onset_frames = librosa.onset.onset_detect(y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
    #onset_times = librosa.frames_to_time(onset_frames)
    
    #plt.vlines(onset_times, -0.8, 0.79, color='r', alpha=0.8) 
    #plt.savefig(image_path)
    # plt.show()
    # plt.close()

    # convert frames to samples
    samples = librosa.frames_to_samples(onset_frames)

    # filter lower samples
    filteredSamples = filterLowSamples(samples)

    # get indexes of all samples in the numpy array
    indexes = np.where(filteredSamples>0)

    length = len(indexes[0])
    j = 0

    # iterate over all indexes of the onsets. What we do here is group indexes by two, so that we have the beginning and ending of 
    # the audio sample that we will use to get the note from.
    # For example, if we have 4 onsets (indexes 0 to 3) we use these segments:
    # 0 to 1
    # 1 to 2
    # 2 to 3
    # Next step: we should also use whatever piece of audio before the first index and after the last one.
    for i in indexes[0]:
        j = i
        
        if j < length-1:
            detectAndPrintNote(q, y, sr, filteredSamples, j, j+1)
        elif j == length-1:
            detectAndPrintNote(q, y, sr, filteredSamples, j, 999)


    # comment or uncomment break for testing single audio recordings
    # break
# infinite recording loop
while True:
    frames = []

    print("recording...")
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    print("finished recording")

    waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
    waveFile.close()

    y, sr = librosa.load(audio_path)

    processThread = Thread(target = processAudio, args =(q, y, sr))
    processThread.start()


# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()