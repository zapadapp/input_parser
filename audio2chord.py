import os
import librosa
import numpy as np
import librosa.display
from scipy.signal import find_peaks
from scipy.fft import fft
import tensorflow as tf
from music21 import chord
from music21 import stream as m21stream
from array import ArrayType
import keras
import librosa
import tensorflow as tf

# solve local imports
import sys
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE = os.path.dirname(FILE_PATH)

sys.path.insert(0, os.path.join(WORKSPACE, "chord_cnn"))
#from parser_data import normalizeShape, correctShape

CATEGORIES = ["A#3","A#4","A#5","A3","A4","A5",
              "B3", "B4","B5","C#3","C#4","C#5",
              "C3","C4","C5","D#3","D#4", "D#5",
              "D3","D4","D5","E3","E4", "E5",
              "F#3","F#4", "F#5","F3","F4","F5",
              "G#3","G#4","G#5","G3","G4","G5",]

chord_model = keras.models.load_model('../chord_cnn/modelo-acordes-v01.h5')

## Function that filters lower samples generated by input noise.
def filterLowSamples(samples):
    # find indexes of all elements lower than 2000 from samples
    indexes = np.where(samples < 2000)

    # remove elements for given indexes
    return np.delete(samples, indexes)

def correctShape(chroma_shape):
    return chroma_shape == 130

def normalizeShape(chroma_mat):
    nums = 0
    #init_shape tiene la dimension de columnas. 
    init_shape= chroma_mat.shape[1]
    #Me fijo cuantas columnas faltan por rellenar
    nums = 130 - init_shape
    #itero nums copiando el anterior
    arreglo = np.array(chroma_mat[:,init_shape-1])
   
    i = 0
    while i < nums :
        chroma_mat= np.column_stack((chroma_mat,arreglo))  
        i = i +1 
    return chroma_mat


def getChordFromRNN(signal, sample_rate):
      
    #ESTO SE REPITE TODO EN audio2note
    X = fft(signal)
    X_mag = np.absolute(X)

    # generate x values (frequencies)
    f = np.linspace(0, sample_rate, len(X_mag))
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
    ## HASTA ACA 
            # extract Chroma
            chroma = librosa.feature.chroma_cens(y=signal, sr=sample_rate)

            if not correctShape(chroma.shape[1]) :
                chroma = normalizeShape(chroma)

            chroma_reshape = tf.reshape(chroma, [ 1,12,130])
            my_prediction = chord_model.predict(chroma_reshape)
   
            index = np.argmax(my_prediction)
            print("chord: " + CATEGORIES[index])

            return CATEGORIES[index]

def getNotesFromChords(chord):
    notas_string = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']	
    nota_2 =''
    nota_3 =''
    octaveIndex = 2
    secondNoteIndex = 3

    if len(chord) == 2:
        octaveIndex = 1
        secondNoteIndex = 4
	
    nota = chord[0]
    octava = int(chord[octaveIndex])
    indice = notas_string.index(nota)
    if ((indice + secondNoteIndex) / 12) >= 1 :
        print(indice + secondNoteIndex)
        nota_2 = notas_string[((indice + secondNoteIndex )%12)] + str(octava + 1)
    else:
        nota_2 = notas_string[(indice + secondNoteIndex)]  + str(octava)
    if ((indice + 7) / 12) >= 1 :
        nota_3 = notas_string[((indice + 7) %12)] + str(octava + 1)
    else:
        nota_3 = notas_string[(indice + 7)]  + str(octava)

    triada = [chord, nota_2, nota_3]
     	 	
    return triada

def detectAndPrintChord(s,q, y, sr, samples, a, b, scorePath):
    # limit the audio input from sample in index a to sample in index b, unless b is 999 which means that it is the end of the audio data
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]

    playedChord = getChordFromRNN(data,sr)
    print("chord: " + playedChord)
    
    q.put(playedChord)
    triada = getNotesFromChords(playedChord)
    s.append(chord.Chord(triada))
    print(s.write('lily.png', fp=os.path.join("tmp", scorePath)))
    #q.put(s)
    print("Detected chord: {}".format(playedChord))
    print("Notes from chord: {}".format(triada))
    return    

def processAudio(s,q, audioPath, scorePath):
    ############################################################
    ##############    Actual audio processing    ###############
    ############################################################

    # Note: we should be doing this in another thread so that we do not have to wait for this to finish to record another wave file.
    
    y, sr = librosa.load(audioPath)
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
            detectAndPrintChord(s, q, y, sr, filteredSamples, j, j+1, scorePath)
        elif j == length-1:
            detectAndPrintChord(s, q, y, sr, filteredSamples, j, 999, scorePath)
