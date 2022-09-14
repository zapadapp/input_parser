import turtle
import sys
import os
import time

FILE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, FILE_PATH)
import audio2chord

class Drawer:
    def __init__(self, t, width, height):
        self.drawnNotes = []
        self.drawnElements = []
        self.t = t
        self.t.speed(0)
        #self.t.hideturtle()
        self.scoreX = 0
        self.scoreY = 0
        self.lowestY = 0
        self.compassWeight = 0
        self.maxCompasses = 4
        self.compassSplits = 0

        #t.screensize(2000,2000)
            
        x, y = self.t.position()
        self.initScoreX = x - (width/2 - 10)
        self.initScoreY = y + (height/2 - 50)
        self.drawCompassTempo(self.initScoreX, self.initScoreY+10)

        self.drawScore()
    
    def drawScore(self):
        self.goto(self.initScoreX, self.initScoreY)

        for y in range(4):
            self.t.forward(1500)
            self.t.backward(1500)
            self.t.right(90)
            self.t.forward(20)
            self.t.left(90)

        self.t.forward(1500)
        self.t.backward(1500)

        self.scoreX, self.scoreY = self.t.position()

    def splitScore(self):
        self.compassSplits = 0
        self.drawnElements = []
        self.gotoBase()
        self.initScoreX, y = self.t.position()
        self.initScoreY = y - 80
        self.drawScore()

    def drawCompassTempo(self, x, y):
        self.goto(x, y)
        self.t.width(2)
        self.t.goto(x,y+10)
        self.t.goto(x,y+5)
        self.t.goto(x-5,y+5)
        self.t.goto(x-5,y+10)

        self.goto(x+5, y)
        x, y = self.t.position()
        self.t.goto(x+2, y+10)
        self.t.goto(x, y)

        self.goto(x+12, y)
        x, y = self.t.position()
        self.t.goto(x,y+10)
        self.t.goto(x,y+5)
        self.t.goto(x-5,y+5)
        self.t.goto(x-5,y+10)

        self.t.width(1)

    def drawNote(self, note, type):
        y = int(self.getNoteYPos(note))
        if y == -1:
            print("invalid note")
            return
        x = self.scoreX + int((len(self.drawnElements) * 40) + 20)

        # check if it is a sharp note
        sharp = note.__contains__('#')

        self.drawExtraLines(x,y)
        match type:
            case "round":
                self.drawRound(x, y, sharp, False)
                self.drawnNotes.append(note)
                self.drawnElements.append(note)
                self.gotoBase()
                self.compassWeight = self.compassWeight + 1
                for i in range(3):
                    # "draw" a blank
                    self.drawnElements.append("blank")
                    self.compassWeight = self.compassWeight + 1
                    self.gotoBase()
                    self.drawSplitLine()
            case "white":
                self.drawWhite(x, y, sharp, False)
                self.drawnNotes.append(note)
                self.drawnElements.append(note)
                self.gotoBase()
                self.compassWeight = self.compassWeight + 1
                # "draw" a blank
                self.drawnElements.append("blank")
                self.compassWeight = self.compassWeight + 1
                self.gotoBase()
                self.drawSplitLine()       
            case "black":
                self.drawBlack(x, y, sharp, False)
                self.compassWeight = self.compassWeight + 1
                self.drawnNotes.append(note)
                self.drawnElements.append(note)
                self.gotoBase()
                self.drawSplitLine()       
            case "quaver":
                self.compassWeight = self.compassWeight + 0.5
                self.drawQuaver(x, y, sharp, False)
                self.drawnNotes.append(note)
                self.drawnElements.append(note)
                self.gotoBase()
                self.drawSplitLine()       
            case "semiquaver":
                self.compassWeight = self.compassWeight + 0.25
                self.drawSemiQuaver(x, y, sharp, False)
                self.drawnNotes.append(note)
                self.drawnElements.append(note)
                self.gotoBase()
                self.drawSplitLine()    

    def drawChord(self, chord, type):
        octave = chord[len(chord)-1]
        notes = audio2chord.getNotesFromChords(chord[:len(chord)-1], int(octave))
        if len(notes) != 3:
            return 
        
        firstNotePosY = int(self.getNoteYPos(notes[0]))
        if firstNotePosY == -1:
            print("invalid note")
            return

        secondNotePosY = int(self.getNoteYPos(notes[1]))
        if secondNotePosY == -1:
            print("invalid note")
            return

        thirdNotePosY = int(self.getNoteYPos(notes[2]))
        if thirdNotePosY == -1:
            print("invalid note")
            return    

        x = self.scoreX + int((len(self.drawnElements) * 40) + 20)

        self.drawExtraLines(x,firstNotePosY)
        self.drawExtraLines(x,thirdNotePosY)

        match type:
            case "round":
                self.drawRound(x, firstNotePosY, notes[0].__contains__('#'), True)
                self.gotoBase()
                self.drawRound(x, secondNotePosY, notes[1].__contains__('#'), True)
                self.gotoBase()
                self.drawRound(x, thirdNotePosY, notes[2].__contains__('#'), True)
                self.drawnNotes.append(chord)
                self.drawnElements.append(chord)
                self.gotoBase()
                self.compassWeight = self.compassWeight + 1
                for i in range(3):
                    # "draw" a blank
                    self.drawnElements.append("blank")
                    self.compassWeight = self.compassWeight + 1
                    self.gotoBase()
                    self.drawSplitLine()
            case "white":
                self.drawWhite(x, firstNotePosY, notes[0].__contains__('#'), True)
                self.gotoBase()
                self.drawWhite(x, secondNotePosY, notes[1].__contains__('#'), True)
                self.gotoBase()
                self.drawWhite(x, thirdNotePosY, notes[2].__contains__('#'), True)                
                self.drawnNotes.append(chord)
                self.drawnElements.append(chord)
                self.gotoBase()
                self.compassWeight = self.compassWeight + 1
                # "draw" a blank
                self.drawnElements.append("blank")
                self.compassWeight = self.compassWeight + 1
                self.gotoBase()
                self.drawSplitLine()       
            case "black":
                self.drawBlack(x, firstNotePosY, notes[0].__contains__('#'), True)
                self.gotoBase()
                self.drawBlack(x, secondNotePosY, notes[1].__contains__('#'), True)
                self.gotoBase()
                self.drawBlack(x, thirdNotePosY, notes[2].__contains__('#'), True)                
                self.drawnNotes.append(chord)
                self.drawnElements.append(chord)
                self.compassWeight = self.compassWeight + 1
                self.gotoBase()
                self.drawSplitLine()       
            case "quaver":
                self.compassWeight = self.compassWeight + 0.5
                self.drawQuaver(x, firstNotePosY, notes[0].__contains__('#'), True)
                self.gotoBase()
                self.drawQuaver(x, secondNotePosY, notes[1].__contains__('#'), True)
                self.gotoBase()
                self.drawQuaver(x, thirdNotePosY, notes[2].__contains__('#'), True)                
                self.drawnNotes.append(chord)
                self.drawnElements.append(chord)
                self.gotoBase()
                self.drawSplitLine()       
            case "semiquaver":
                self.compassWeight = self.compassWeight + 0.25
                self.drawSemiQuaver(x, firstNotePosY, notes[0].__contains__('#'), True)
                self.gotoBase()
                self.drawSemiQuaver(x, secondNotePosY, notes[1].__contains__('#'), True)
                self.gotoBase()
                self.drawSemiQuaver(x, thirdNotePosY, notes[2].__contains__('#'), True)                
                self.drawnNotes.append(chord)
                self.drawnElements.append(chord)
                self.gotoBase()
                self.drawSplitLine()   

    def drawBlack(self, x, y, sharp, isChord):
        self.goto(x, y)
        self.t.begin_fill()
        self.t.circle(10)
        self.t.end_fill()
        self.goto(x+10,y+10)
        self.t.width(3)
        self.t.left(90)
        self.t.forward(25)
        self.t.width(1)

        if sharp:
            self.drawSharp(x, y, isChord)

        return      

    def drawWhite(self, x, y, sharp, isChord):
        self.goto(x, y)
        self.t.width(2)
        self.t.circle(9)
        self.t.width(1)
        self.goto(x+10,y+10)
        self.t.width(3)
        self.t.left(90)
        self.t.forward(25)
        self.t.width(1)

        if sharp:
            self.drawSharp(x, y, isChord)
            
        return

    def drawRound(self, x, y, sharp, isChord):
        self.goto(x, y)
        self.t.width(2)
        self.t.circle(9)
        self.t.width(1)

        if sharp:
            self.drawSharp(x, y, isChord)
            
        return    

    def drawQuaver(self, x, y, sharp, isChord):
        self.goto(x, y)
        self.t.begin_fill()
        self.t.circle(10)
        self.t.end_fill()
        self.goto(x+10,y+10)
        self.t.width(3)
        self.t.left(90)
        self.t.forward(25)
        self.t.right(90)
        self.t.forward(6)
        self.t.width(1)

        if sharp:
            self.drawSharp(x, y, isChord)
            
        return

    def drawSemiQuaver(self, x, y, sharp, isChord):
        self.goto(x, y)
        self.t.begin_fill()
        self.t.circle(10)
        self.t.end_fill()
        self.goto(x+10,y+10)
        self.t.width(3)
        self.t.left(90)
        self.t.forward(25)
        self.t.right(90)
        self.t.forward(6)
        self.t.bk(6)
        self.t.right(90)
        self.t.fd(6)
        self.t.left(90)
        self.t.fd(6)
        self.t.width(1)

        if sharp:
            self.drawSharp(x, y, isChord)
            
        return   

    def drawSharp(self, x, y, isChord):
        self.t.setheading(0)
        self.t.width(2)
        self.goto(x, y)
        if isChord:
            self.goto(x-20,y+5)
        else:    
            self.goto(x-7,y+25)
        newX, newY = self.t.position()
        
        self.t.left(90)
        self.t.fd(12)
        self.goto(newX+4, newY)
        self.t.fd(12)
        self.t.right(90)
        self.goto(newX-4, newY+4)
        self.t.fd(12)
        self.goto(newX-4, newY+8)
        self.t.fd(12)
        self.t.width(1)
        return

    def goto(self, x, y):
        self.t.up()
        self.t.goto(x, y)
        self.t.down()    
    
    def gotoBase(self):
        self.t.up()
        self.t.goto(self.scoreX, self.scoreY)
        self.t.setheading(0)
        self.t.down()  
    
    def getNoteYPos(self, note):
        match note:
            case "B3" | "B#3" :
                return self.scoreY - 40
            case "C4" | "C#4":
                return self.scoreY - 30
            case "D4" | "D#4": 
                return self.scoreY - 20    
            case "E4" | "E#4":
                return self.scoreY - 10
            case "F4" | "F#4":
                return self.scoreY
            case "G4" | "G#4":
                return self.scoreY + 10
            case "A4" | "A#4":
                return self.scoreY + 20  
            case "B4" | "B#4":
                return self.scoreY + 30  
            case "C5" | "C#5":
                return self.scoreY + 40
            case "D5" | "D#5": 
                return self.scoreY + 50    
            case "E5" | "E#5":
                return self.scoreY + 60
            case "F5" | "F#5":
                return self.scoreY + 70
            case "G5" | "G#5":
                return self.scoreY + 80
            case "A5" | "A#5":
                return self.scoreY + 90  
            case "B5" | "B#5":
                return self.scoreY + 100                 

        return -1   

    def drawSplitLine(self):
        if self.compassWeight >= 4:
            x = self.scoreX + int((len(self.drawnElements) * 40) + 20)
            self.goto(x, self.scoreY)
            self.t.left(90)
            self.t.forward(80)
            self.gotoBase()
            self.drawnElements.append("split")
            self.compassSplits = self.compassSplits + 1

            leftover = self.compassWeight%4
            self.compassWeight = leftover

            if self.compassSplits == self.maxCompasses:
                self.splitScore()


    def drawExtraLines(self, x, y):
        if y < self.scoreY - 10 :
            self.drawBottomLines(x, y)
        elif  y > self.scoreY + 70:
            self.drawTopLines(x, y)

        return

    def drawBottomLines(self, x, y):
        aux = self.scoreY
        
        while aux > y + 10:
            self.goto(x, aux-20)
            self.t.fd(15)
            self.t.bk(30)
            self.t.fd(15)

            aux = aux - 20

    def drawTopLines(self, x, y):
        aux = self.scoreY + 80
        
        while aux < y + 10:
            self.goto(x, aux+20)
            self.t.fd(15)
            self.t.bk(30)
            self.t.fd(15)

            aux = aux + 20

    def clearScore(self):
        self.t.clear()
        self.drawScore()        

    def waiting(self):
        self.t.speed(1)
        self.t.hideturtle()
        self.t.right(90)
        self.t.up()
        self.t.forward(15)
        self.t.left(90)
        self.t.down()
        while True:
            for i in range(3):
                self.t.dot()
                self.t.up()
                self.t.forward(15)
                self.t.down()

            self.t.up()
            self.t.backward(15)
            self.t.down()

            self.t.color("white")

            for j in range(3):
                self.t.dot()
                self.t.up()
                self.t.backward(15)
                self.t.down()

            self.t.up()
            self.t.forward(15)
            self.t.down()    

            self.t.color("black")

    def saveScore(self):
        cv = self.t.getcanvas()
        cv.postscript(file="score{}.ps".format(time.time()), colormode='color')        



# screen = turtle.Screen()
# screen.reset()
# screen.setup(1200, 400)

# t = turtle.Turtle()

# d = Drawer(t, 1200, 400)

# d.drawNote("E4", "quaver")
# d.drawNote("F4", "round")
# d.drawNote("A4", "quaver")
# d.drawNote("A#4", "semiquaver")
# d.drawNote("C4", "black")
# d.drawNote("D4", "black")
# d.drawNote("B#3", "round")
# d.drawNote("B4", "quaver")
# d.drawNote("E#5", "quaver")
# d.drawNote("G4", "round")
# d.drawNote("F#4", "black")
# # d.drawNote("D4", "round")
# # d.drawNote("F#4", "white")
# # d.drawNote("B4", "quaver")
# # d.drawNote("E#4", "semiquaver")
# # d.drawNote("E4", "semiquaver")

# # d.drawChord("C4", "round")

# # d.drawChord("F4", "round")

# # d.drawChord("C5", "black")
# # d.drawChord("C4", "black")
# # d.drawChord("D4", "black")
# d.drawNote("F#4", "black")
# d.drawNote("G#4", "round")
# d.drawNote("C5", "round")

# cv = turtle.getcanvas()
# cv.postscript(file="file_name.ps", colormode='color')

# turtle.done()
