import os
import librosa
import numpy as np
import librosa.display
from scipy.signal import find_peaks
from scipy.fft import fft
from music21 import note
import tensorflow as tf
import keras
import sys
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE = os.path.dirname(FILE_PATH)

sys.path.insert(0, os.path.join(WORKSPACE, "note"))

MY_MODEL = keras.models.load_model('../notes/modelo-notas-v01.h5')

CATEGORIES = ["A#2","A#3","A#4","A2","A3","A4","B2","B3","B4","C#3","C#4","C#5",
 			   "C3","C4","C5","D#3","D#4","D#5","D3","D4","D5","E2","E3","E4",
 			   "F#2","F#3","F#4","F2","F3","F4", "G#2","G#3","G#4","G2","G3","G4",
               "A#4","A3","A4","A5","B3","B4","B5","C#4","C3","C4","C5","D#4","D3","D4","D5",
               "E3","E4","E5","F#4","F3","F4","F5","G#4","G3","G4","G5",]

INSTRUMENT = ["Guitar","Piano"]
NFFT = 512
HOP_LENGTH = 1024
SHAPE = 100
N_MELS = 50
## Function that filters lower samples generated by input noise.
def filterLowSamples(samples):
    # find indexes of all elements lower than 2000 from samples
    indexes = np.where(samples < 2000)

    # remove elements for given indexes
    return np.delete(samples, indexes)


def getNoteandInstrumentFromRNN(s, q, scorePath, y, sr, samples, a, b):
    
    instrument = INSTRUMENT[1]
    nota = "not recognize"
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]
    
    if isSound(data,sr):
        mel_spec = librosa.feature.melspectrogram(y=data, sr=sr, n_mels=N_MELS,fmin=100, fmax= 650) 
        if not correctShape(mel_spec.shape[1]) :
            mel_spec =  normalizeShape(mel_spec)

        if correctShape(mel_spec.shape[1]):
            mel_reshape = tf.reshape(mel_spec, [ 1,N_MELS,SHAPE ])
            my_prediction = MY_MODEL.predict(mel_reshape)
            index = np.argmax(my_prediction)
            nota = CATEGORIES[index]
        
            if index < 36 :
                instrument = INSTRUMENT[0]

        if note != "not recognize":
            #nota = convertToNote(str(librosa.hz_to_note(f[peak_i[0]])))
            print("Instrument {}\n".format( instrument))
            print("Note {}\n".format(nota))
            q.put(nota)
            s.append(note.Note(nota))
            print(s.write('lily.png', fp=os.path.join("../front/tmp", scorePath)))    
    else:
        print("PLEASE INIT YOUR ZAPADAPP :D \n")

    return instrument, nota

def isSound(signal,sr):
    X = fft(signal)
    X_mag = np.absolute(X)

    # generate x values (frequencies)
    f = np.linspace(0, sr, len(X_mag))
    f_bins = int(len(X_mag)*0.1) 

    # find peaks in Y values. Use height value to filter lower peaks
    _, properties = find_peaks(X_mag, height=100)
    if len(properties['peak_heights']) > 0:
        y_peak = properties['peak_heights'][0]

        # get index for the peak
        peak_i = np.where(X_mag[:f_bins] == y_peak)
        return len(peak_i) > 0
        # if we found an for a peak we print the note
    return False

def detectAndPrintNote(s, q, scorePath, y, sr, samples, a, b):
    # limit the audio input from sample in index a to sample in index b, unless b is 999 which means that it is the end of the audio data
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]
    
    # return fast in case there is nothing to process
    if len(data) == 0:
        return

    # calculate FFT and absol
    X = fft(data)
    X_mag = np.absolute(X)

    # generate x values (frequencies)
    f = np.linspace(0, sr, len(X_mag))
    f_bins = int(len(X_mag)*0.1) 
    

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
            q.put(nota)
            s.append(note.Note(nota))
            print(s.write('lily.png', fp=os.path.join("../front/tmp", scorePath)))


def convertToNote(val) :
    print("nota: {}".format(val))
    nota = str.replace(str.replace(val, "['", ""), "']", "")
    if len(nota) == 3:
        nota = nota[0] + "#" + nota[2]

    if len(nota) == 4 and nota[2] == "-":    
        nota = nota[0] + "#" + nota[3]

    return nota

def processAudio(s,q, audioPath, scorePath):
    ############################################################
    ##############    Actual audio processing    ###############
    ############################################################

    # Note: we should be doing this in another thread so that we do not have to wait for this to finish to record another wave file.
    
    y, sr = librosa.load(audioPath)


    onset_frames = librosa.onset.onset_detect(y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)

    # convert frames to samples
    samples = librosa.frames_to_samples(onset_frames)

    # filter lower samples
    filteredSamples = filterLowSamples(samples)

    # get indexes of all samples in the numpy array
    indexes = np.where(filteredSamples>0)

    length = len(indexes[0])
    j = 0

    print("len samples {}".format(length))
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
            getNoteandInstrumentFromRNN(s,q,scorePath, y, sr, filteredSamples, j, j+1)
        elif j == length-1:
            getNoteandInstrumentFromRNN(s,q,scorePath, y, sr, filteredSamples, j, 999)


def correctShape(mel_shape):
    return mel_shape == SHAPE

def normalizeShape(mel_mat):
    nums = 0
    #init_shape tiene la dimension de columnas. 
    init_shape= mel_mat.shape[1]
    #Me fijo cuantas columnas faltan por rellenar
    nums = SHAPE - init_shape
    #itero nums copiando el anterior
    arreglo = np.array(mel_mat[:,init_shape-1])
    i = 0
    if nums > 0 :
        while i < nums :
            mel_mat= np.column_stack((mel_mat,arreglo))  
            i = i +1 
    else:
        #print("MY SHAPE IS: {}".format(mel_mat.shape[1]))
        mel_mat = np.array(mel_mat[:,: SHAPE])
        #print("NOW MY SHAPE IS: {}".format(mel_mat.shape[1]))
             
    return mel_mat
