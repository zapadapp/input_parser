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
import drawer


FILE_PATH = os.path.dirname(os.path.realpath(__file__))
WORKSPACE = os.path.dirname(FILE_PATH)
NFFT = 512
HOP_LENGTH = 1024
SHAPE = 100
N_MELS = 50
sys.path.insert(0, os.path.join(WORKSPACE, "note"))
sys.path.insert(0, os.path.join(WORKSPACE, "chord_cnn"))


#Categories from version 04
CHORD_CATEGORIES = ["A","A#","A#-","A-","B","B-","C","C#", 
              "C#-","C-","D","D#","D#-","D-","E","E-",
              "F","F#","F#-","F-","G#","G#-","G","G-",
              "A","A#","A#-","A-","B","B-","C","C#", 
              "C#-","C-","D","D#","D#-","D-","E","E-",
              "F","F#","F#-","F-","G","G#","G#-","G-"]

INSTRUMENT = ["Guitar","Piano"]

NOTE_CATEGORIES = ["A#2","A#3","A#4","A2","A3","A4","B2","B3","B4","C#3","C#4","C#5",
 			   "C3","C4","C5","D#3","D#4","D#5","D3","D4","D5","E2","E3","E4",
 			   "F#2","F#3","F#4","F2","F3","F4", "G#2","G#3","G#4","G2","G3","G4",
               "A#3","A#4","A#5","A3","A4","A5","B3","B4","B5","C#3","C#4","C#5",
               "C3","C4","C5","D#3","D#4","D#5","D3","D4","D5","E3","E4","E5",
               "F#3","F#4","F#5","F3","F4","F5","G#3","G#4","G#5","G3","G4","G5"]


note_model = keras.models.load_model('../notes/modelo-notas-v03.h5')
chord_model = keras.models.load_model('../chord_cnn/modelo-acordesV06.h5')
## Function that filters lower samples generated by input noise.


def getNoteAndInstrumentFromRNN(s, q, scorePath, y, sr, samples, a, b):
    
    instrument = INSTRUMENT[1]
    nota = "not recognize"
    if b == 999:
        data = y[samples[a]:]
    else:    
        data = y[samples[a]:samples[b]]
        
    
    mel_spec = librosa.feature.melspectrogram(y=data, sr=sr, n_mels=N_MELS,fmin=100, fmax= 650) 
    if not correctNoteShape(mel_spec.shape[1]) :
        mel_spec =  normalizeNoteShape(mel_spec)
    if correctNoteShape(mel_spec.shape[1]):
        mel_reshape = tf.reshape(mel_spec, [ 1,N_MELS,SHAPE ])
        my_prediction = note_model.predict(mel_reshape)
        index = np.argmax(my_prediction)
        nota = NOTE_CATEGORIES[index]
    
        if index < 36 :
            instrument = INSTRUMENT[0]
        
    print("Instrument {}\n".format( instrument))
    print("Note {}\n".format(nota))

    return instrument, nota

def getFigure(time):
    vector_figure = ["semiquaver","quaver","black","white","round"]
    i = 0
    figure_time = 0.25 ##Arranca en semi-corchea
    min_duration = 4.0
    figure = vector_figure[1]
    while i < 5:
        duration = abs(figure_time - time) 
        if duration <  min_duration:  
            figure = vector_figure[i] 
            min_duration = duration 
        i = i + 1                      
        figure_time = figure_time * 2 
    return figure 

#Without RNNOTES
def detectAndPrintNote(s, q, drawer, scorePath, y, sr, samples, a, b):
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
            #print(s.write('lily.png', fp=os.path.join("../front/tmp", scorePath)))
            drawer.drawNote(nota,"black")

def convertToNote(val) :
    print("nota: {}".format(val))
    nota = str.replace(str.replace(val, "['", ""), "']", "")
    if len(nota) == 3:
        nota = nota[0] + "#" + nota[2]

    if len(nota) == 4 and nota[2] == "-":    
        nota = nota[0] + "#" + nota[3]

    return nota

def processAudio(s, drawer, q, audioPath, scorePath,lastNote, lastDuration,detected):
    y, sr = librosa.load(audioPath)
    duration = 0.0
    instrumento  = ""
    nota = ""
    chord = ""
    if isSound(y,sr):
        ONSET_PARAM = 20
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        velocity_audio = 60*len(beats)/2
        if velocity_audio > 40 and velocity_audio <= 80 :
            ONSET_PARAM = 10
        elif velocity_audio > 80 and velocity_audio <= 100:
            ONSET_PARAM = 7
        elif velocity_audio > 100:
            ONSET_PARAM = 5
       
        onset_env = librosa.onset.onset_strength(y=y, sr=sr, max_size=5)
        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env,backtrack=True, normalize =True,wait=ONSET_PARAM, pre_avg=ONSET_PARAM, post_avg=ONSET_PARAM, pre_max=ONSET_PARAM, post_max=ONSET_PARAM)
        # convert frames to samples
        samples = librosa.frames_to_samples(onset_frames)

        filteredSamples = filterLowSamples(samples)

        indexes = np.where(filteredSamples>0)

        onset_times = librosa.frames_to_time(onset_frames)

        ##Draw the last note 
        if lastNote != "":
            drawer.drawNote(lastNote,getFigure(lastDuration + onset_times[0]))

        length = len(indexes[0])
        j = 0
        if detected == 'note':
            for i in indexes[0]:
                j = i
                
                if j < length-1:
                    _ , nota = getNoteAndInstrumentFromRNN(s,q,scorePath, y, sr, filteredSamples, j, j+1)
                    if nota != 'not recognize' :
                        duration = onset_times[j + 1] - onset_times[j]
                        figure = getFigure(duration)    
                        drawer.drawNote(nota,figure)
                elif j == length-1:
                    _ , nota = getNoteAndInstrumentFromRNN(s,q,scorePath, y, sr, filteredSamples, j, 999)
                    duration = onset_times[length-1] - onset_times[j]
                    # figure = getFigure(duration)
                    # drawer.drawNote(nota,figure)
            lastDuration = 2 - onset_times[len(onset_times)-1]
        elif detected == 'chord':
            for i in indexes[0]:
                j = i
        
                if j < length-1:
                    _ , chord = detectAndPrintChord(s, q, y, sr, filteredSamples, j, j+1, scorePath)
                    if nota != 'not recognize' :
                        duration = onset_times[j + 1] - onset_times[j]
                        figure = getFigure(duration)    
                        drawer.drawChord(chord,figure)
                elif j == length-1:
                    _ , chord =  detectAndPrintChord(s, q, y, sr, filteredSamples, j, 999, scorePath)
                    duration = onset_times[len(onset_times)-1] - onset_times[j]
                    figure = getFigure(duration)  
                    drawer.drawChord(chord,duration)
            lastDuration = 2 - onset_times[len(onset_times)-1]
    else:
        if lastNote != "":
            if detected == 'note':
                drawer.drawNote(lastNote,getFigure(lastDuration+0.5))
            elif detected == 'chord':
                drawer.drawChord(lastNote,getFigure(lastDuration+0.5))
        else:
            drawer.drawNote("blank", "white")
        lastDuration = 0
        
    return nota, lastDuration

#RESHAPES NOTES AND CHORDS
def correctNoteShape(mel_shape):
    return mel_shape == SHAPE

def normalizeNoteShape(mel_mat):
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

def correctChordShape(chroma_shape):
    return chroma_shape == 130

def normalizeChordShape(chroma_mat):
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

def getChroma(signal,sample_rate):
    # extract Chroma
    chroma = librosa.feature.chroma_cens(y=signal, sr=sample_rate,fmin=130,n_octaves=2)
    
    if not correctChordShape(chroma.shape[1]) :
        chroma = normalizeChordShape(chroma)
    return chroma

def getChordAndIntrumentFromRNN(signal, sample_rate):
    chroma = getChroma(signal,sample_rate)
    chroma_reshape = tf.reshape(chroma, [ 1,12,130])
    my_prediction = chord_model.predict(chroma_reshape)
    index = np.argmax(my_prediction)
    chord= CHORD_CATEGORIES[index]
    instrument = INSTRUMENT[1]
    if index < 24:
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
    playedChord = ""
    playedIntrument = ""
    if len(data) == 0:
        return playedIntrument, playedChord
    octava = 4
    playedIntrument, playedChord = getChordAndIntrumentFromRNN(data,sr)
    q.put(playedChord)
    triada = getNotesFromChords(playedChord,octava)
    showLog(playedIntrument,playedChord,triada,octava)
    return playedIntrument, playedChord


## Function that filters lower samples generated by input noise.
def filterLowSamples(samples):
    # find indexes of all elements lower than 2000 from samples
    indexes = np.where(samples < 2000)
    # remove elements for given indexes
    return np.delete(samples, indexes)

def showLog(playedIntrument,playedChord,triada,octava):
    print("RESUME THE RECOGNITION\n")
    print("-----------------------\n")
    print("Detected octave: {}\n".format(octava))
    print("Detected instrument: {}\n".format(playedIntrument))
    print("Detected chord: {}\n".format(playedChord))
    print("Notes from chord: {}".format(triada))
    print("--WAIT FOR THE NEXT CHORD--")
    return  