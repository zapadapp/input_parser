import webrtcvad
import pyaudio
import wave
import os, sys
import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display
import tensorflow as tf
from scipy.signal import find_peaks
from scipy.fft import fft


vad = webrtcvad.Vad()
vad.set_mode(2)
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 960
RECORD_SECONDS = 2
WAVE_OUTPUT_FILENAME = "file.wav"

audio = pyaudio.PyAudio()

# start Recording
stream = audio.open(format=FORMAT, channels=CHANNELS,
                rate=RATE, input=True,
                frames_per_buffer=CHUNK, input_device_index=11)

def printNote(y, sr, samples, a, b):
    data = y[samples[a]:samples[b]]
    print("y: {}".format(y))
    print("len y: {}".format(len(y)))

    print("data: {}".format(data))
    X = fft(data)
    X_mag = np.absolute(X)

    #plt.figure(figsize=(18, 5))
    
    f = np.linspace(0, sr, len(X_mag))
    f_bins = int(len(X_mag)*0.1) 
    plt.plot(f[:f_bins], X_mag[:f_bins])

    peaks_index, properties = find_peaks(X_mag, height=259)
    print("peak index: {}".format(peaks_index))
    print("props: {}".format(properties))

    y_peak = properties['peak_heights'][0]
    print("pico en Y: {}".format(y_peak))

    peak_i = np.where(X_mag[:f_bins] == y_peak)
    print("indice de pico en Y: {}".format(peak_i[0]))

    print("pico en X: {}".format(f[peak_i[0]]))
    print("nota segun pico: {}".format(str(librosa.hz_to_note(f[peak_i[0]]))))

while True:

    frames = []
    frameCount = 0

    # while frameCount < 5:
    #     data = stream.read(CHUNK)

    #     if vad.is_speech(data, RATE):
    #         frameCount+=1
    #     else:
    #         frameCount = 0
    #     # print frameCount

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


    # change this as you see fit
    audio_path = 'file.wav'
    image_path = 'tmp/tmp.jpg'

    y, sr = librosa.load(audio_path)

    plt.figure(figsize=(14, 5))
    #librosa.display.waveshow(y, sr)

    onset_frames = librosa.onset.onset_detect(y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
    print(onset_frames)
    print("val1: {}| val2: {}".format(onset_frames[0],onset_frames[1]))
    # onset_times = librosa.frames_to_time(onset_frames)
    # print(onset_times)
    # plt.vlines(onset_times, -0.8, 0.79, color='r', alpha=0.8) 
    # plt.savefig(image_path)
    # plt.show()
    # plt.close()

    samples = librosa.frames_to_samples(onset_frames)
    print("samples: {}".format(samples))

    pos1 = 0
    pos2 = 1
    pos3 = 2

    if len(samples) == 4:
        pos1 = samples[1]
        pos2 = samples[2]
        pos3 = samples[3]
    
    printNote(y, sr, samples, pos1, pos2)
    printNote(y, sr, samples, pos2, pos3)



    # print("time1: {} | time2: {}".format(onset_times[0], onset_times[1]))
    # print("data: {}".format(y[onset_frames[0]:onset_frames[1]]))

    # X = fft(y[onset_frames[0]:onset_frames[1]])

    # print("X: {}".format(X))    
    # X_mag = np.absolute(X)

    # plt.figure(figsize=(18, 5))
    
    # f = np.linspace(0, sr, len(X_mag))
    # print("f: {}".format(f))
    # f_bins = int(len(X_mag)*0.5)  
    # print("f_bins: {}".format(f_bins))
    # peaks_index, properties = find_peaks(X_mag, height=0)
    # print("peak indexes {}".format(peaks_index))
    # print("properties: {}".format(properties))
    # y_peak = proper[ 3 19 51]
    # print("pico en Y: {}".format(y_peak))

    # peak_i = np.where(X_mag[:f_bins] == y_peak)
    # print("indice de pico en Y: {}".format(peak_i[0]))

    # print("pico en X: {}".format(f[peak_i[0]]))
    # print("nota segun pico: {}".format(str(librosa.hz_to_note(f[peak_i[0]]))))
    plt.show()

    break


# stop Recording
stream.stop_stream()
stream.close()
audio.terminate()