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


#CATEGORIES = ["A","A#","B","C","C#","D","D#","E","F","F#","G","G#"]
CATEGORIES = ["A","A#","A#-","A-","B","B-","C","C#","C#-","C-","D","D#",
              "D#-","D-","E","E-","F","F#","F#-","F-","G","G#","G#-","G-"]

SIGNAL_SHAPE = 65760
chord_model = keras.models.load_model('../chord_cnn/modelo-acordes-v02.h5')

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
 
def getOctaveFromChord(signal, sample_rate):
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
            return int(octava)
    return -1
    
def isSoundFromChord(signal, sample_rate):
   octava = getOctaveFromChord(signal, sample_rate) 
   print("ISSOUND {} ".format(octava))
   x = fft(signal)
   x_mag = np.absolute(x)
   return (octava > 2 and octava < 6 )  and np.mean(x_mag) > 1

def getChroma(signal,sample_rate):
    # extract Chroma
    chroma = librosa.feature.chroma_cens(y=signal, sr=sample_rate,fmin=130,n_octaves=2)
    
    if not correctShape(chroma.shape[1]) :
        chroma = normalizeShape(chroma)
    return chroma


def getChordFromRNN(signal, sample_rate):
    chroma = getChroma(signal,sample_rate)
    chroma_reshape = tf.reshape(chroma, [ 1,12,130])
    my_prediction = chord_model.predict(chroma_reshape)
    index = np.argmax(my_prediction)
    chord= CATEGORIES[index]
    print("chord: {}" .format(chord))
    #octava = getOctaveFromChord(signal,sample_rate)
    #chord = chord + str(octava)
    return chord

def getNotesFromChords(chord,signal,sr):
    notas_string = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    nota_2 =''
    nota_3 =''
   # octaveIndex = 2
    secondNoteIndex = 4
    octava = getOctaveFromChord(signal,sr)
    print("La octava es {}".format(octava))
    if '-' in chord :
      secondNoteIndex = 3
      if '#' in chord:
        chord = chord[0] + chord [1]
      else:
        chord = chord[0]
            	
    indice = notas_string.index(chord)
    if ((indice + secondNoteIndex) / 12) >= 1 :
        print(indice + secondNoteIndex)
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

    #("The shape of signal is: {}".format(data.shape))
    #ACA DEBERIAMOS RELLENAR HASTA LOS 3 SEGUNDOS LA SEÑAL
    data = resizeSignal(data)
    if isSoundFromChord(data,sr):
        playedChord = getChordFromRNN(data,sr)
        q.put(playedChord)
        triada = getNotesFromChords(playedChord,data,sr)
        s.append(chord.Chord(triada))
        print(s.write('lily.png', fp=os.path.join("tmp", scorePath)))
        print("Detected chord: {}\n".format(playedChord))
        #print("eighth chord:{}\n".format(getOctaveFromChord(y,sr)))
        print("Notes from chord: {}".format(triada))
    return    

def resizeSignal(signal):
    signal_size = signal.shape[0]
    last_date = signal[signal_size - 1]
    while  signal_size < SIGNAL_SHAPE:
        signal = np.append(signal,last_date)
        signal_size = signal_size + 1
    return signal    

def processAudio(s,q, audioPath, scorePath):
  
    y, sr = librosa.load(audioPath)
   
    onset_frames = librosa.onset.onset_detect(y, sr=sr, wait=1, pre_avg=1, post_avg=1, pre_max=1, post_max=1)
    samples = librosa.frames_to_samples(onset_frames)

    # filter lower samples
    filteredSamples = filterLowSamples(samples)

    # get indexes of all samples in the numpy array
    indexes = np.where(filteredSamples>0)

    length = len(indexes[0])
    print("len samples {}".format(length))
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
