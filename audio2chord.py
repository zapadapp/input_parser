import os
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
import audio2note
# solve local imports
import sys
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE = os.path.dirname(FILE_PATH)

sys.path.insert(0, os.path.join(WORKSPACE, "chord_cnn"))
#from parser_data import normalizeShape, correctShape

#Categories from version 04
CATEGORIES = ["A","A-","A#","B","B-","C", "C-","C#","D","D-","D#","D#-","E","E-",
              "F","F-","F#","F#-","G","G-","G#","G#-",
              "A","A-","A#","A#-","B","B-","C","C-","C#","C#-",
              "D","D-","D#","D#-","E","E-","F","F-","F#","F#-",
              "G","G-","G#","G#-"]

INSTRUMENT = ["Guitar","Piano"]
chord_model = keras.models.load_model('../chord_cnn/modelo-acordes-v04.h5')

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
 
def getOctaveAndSoundFromChord(signal, sample_rate):
 # calculate FFT and absolute values
    
    X = fft(signal)
    X_mag = np.absolute(X)

    # generate x values (frequencies)
    f = np.linspace(0, sample_rate, len(X_mag))
    f_bins = int(len(X_mag)*0.1) 

    # find peaks in Y values. Use height value to filter lower peaks
    _, properties = find_peaks(X_mag, height=100)
    if len(properties['peak_heights']) > 0:
        y_peak = properties['peak_heights'][0]

        # get index for the peak
        peak_i = np.where(X_mag[:f_bins] == y_peak)

        # if we found an for a peak we print the note
        if len(peak_i) > 0:
            nota = str(librosa.hz_to_note(f[peak_i[0]]))
            nota = audio2note.convertToNote(nota)
            octava = nota[1]
            if octava == "#":
                octava = nota[2]
            return 4, True
    return -1, False 

def getChroma(signal,sample_rate):
    # extract Chroma
    chroma = librosa.feature.chroma_cens(y=signal, sr=sample_rate,fmin=130,n_octaves=2)
    
    if not correctShape(chroma.shape[1]) :
        chroma = normalizeShape(chroma)
    return chroma


def getChordAndIntrumentFromRNN(signal, sample_rate):
    chroma = getChroma(signal,sample_rate)
    chroma_reshape = tf.reshape(chroma, [ 1,12,130])
    my_prediction = chord_model.predict(chroma_reshape)
    index = np.argmax(my_prediction)
    chord= CATEGORIES[index]
    instrument = INSTRUMENT[1]
    if index < 14:
        instrument = INSTRUMENT[0]
    return instrument, chord

def getNotesFromChords(chord,octava):
    notas_string = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    nota_2 =''
    nota_3 =''
   # octaveIndex = 2
    secondNoteIndex = 4
  
    if '-' in chord :
      secondNoteIndex = 3
      if '#' in chord:
        chord = chord[0] + chord [1]
      else:
        chord = chord[0]
            	
    indice = notas_string.index(chord)
    if ((indice + secondNoteIndex) / 12) >= 1 :
        nota_2 = notas_string[((indice + secondNoteIndex )%12)] + str(octava + 1)
    else:
        nota_2 = notas_string[(indice + secondNoteIndex)]  + str(octava)
    if ((indice + 7) / 12) >= 1 :
        nota_3 = notas_string[((indice + 7) %12)] + str(octava + 1)
    else:
        nota_3 = notas_string[(indice + 7)]  + str(octava)

    chord = chord + str(octava)
    triada = [chord, nota_2, nota_3]
     	 	
    return triada

def detectAndPrintChord(s, q, y, sr, samples, a, b, scorePath):
    # limit the audio input from sample in index a to sample in index b, unless b is 999 which means that it is the end of the audio data
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]

    # return fast in case there is nothing to process
    if len(data) == 0:
        return
    octava, is_sound = getOctaveAndSoundFromChord(data,sr)
    if is_sound:
        playedIntrument, playedChord = getChordAndIntrumentFromRNN(data,sr)
        q.put(playedChord)
        triada = getNotesFromChords(playedChord,octava)
        s.append(chord.Chord(triada))
        s.write('lily.png', fp=os.path.join("tmp", scorePath))
        showLog(playedIntrument,playedChord,triada,octava)
    return    

def showLog(playedIntrument,playedChord,triada,octava):
    print("RESUME THE RECOGNITION\n")
    print("-----------------------\n")
    print("Detected octave: {}\n".format(octava))
    print("Detected instrument: {}\n".format(playedIntrument))
    print("Detected chord: {}\n".format(playedChord))
    print("Notes from chord: {}".format(triada))
    print("--WAIT FOR THE NEXT CHORD--")


def processAudio(s,q, audioPath, scorePath):
  
    y, sr = librosa.load(audioPath)
   
    onset_frames = librosa.onset.onset_detect(y, sr=sr, wait=30, pre_avg=30, post_avg=30, pre_max=30, post_max=30)
    samples = librosa.frames_to_samples(onset_frames)

    # filter lower samples
    filteredSamples = filterLowSamples(samples)

    # get indexes of all samples in the numpy array
    indexes = np.where(filteredSamples>0)

    length = len(indexes[0])
    print("len samples {}".format(length))
    j = 0
    if length > 10 :
        return
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
