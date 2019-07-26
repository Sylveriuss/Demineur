from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os
import random
import sys

NB_COTES = 10 # Pour avoir COTE*COTE cases
NB_MINES = 10

INFOBANNER_WIDTH = 100
CASE_SIZE = 50
MARGIN = 20

STATUS_READY = 0
STATUS_PLAYING = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

class Case():
    mined = False
    digged = False
    flagged = False
    cote = 0

    def __init__(self):
        pass

    def getMine(self):
        return self.mined

    def setMine(self):
        self.mined = True
        self.cote = -1

    def incrementCote(self):
        if not self.mined:
            self.cote += 1

    def getDig(self):
        return self.digged

    def dig(self):
        if not self.flagged :
            self.digged = True

        return self.cote

    def getFlag(self):
        return self.flagged

    def setFlag(self):
        if not self.digged:
            self.flagged = not self.flagged
            return True
        else:
            return False

    def value(self):
        if self.digged:
            return str(self.cote)
        elif self.flagged:
            return 'F'
        else :
            return 'X'

    def valueCote(self):
        return str(self.cote)


    def reveal(self):
        self.flagged = False
        self.digged = True

        return self.cote


class Map(QObject):
    updateState = pyqtSignal(int,int,str)
    gamemap = {}
    visited = set()

    def __init__(self):
        super().__init__()
        self.initMap()

    def initMap(self):
        for i in range(NB_COTES):
            for j in range(NB_COTES):
                tmp = (i, j)
                self.gamemap[tmp] = Case()

        # Set Mines
        self.setMines()

    def displayMap(self, hidden=True):
        print()
        print()
        for i in range(NB_COTES):
            for j in range(NB_COTES):
                tmp = (i, j)
                if hidden:
                    print(self.gamemap[tmp].value(), '\t| ', end='')
                else:
                    print(self.gamemap[tmp].valueCote(), '\t| ', end='')
            print()

    def setMines(self):
        nb_mines_l = 0
        while (nb_mines_l < NB_MINES):
            i_t = random.randint(0, NB_COTES-1)
            j_t = random.randint(0, NB_COTES-1)
            tmp = (i_t, j_t)

            if not self.gamemap[tmp].getMine() :
                self.gamemap[tmp].setMine()
                self.setCotes(i_t, j_t)
                nb_mines_l += 1


    def setCotes(self, i_, j_):
        for i in range(max(0,i_-1), min(NB_COTES,i_+2)):

            for j in range(max(0,j_-1), min(NB_COTES,j_+2)):

                tmp = (i, j)

                if not self.gamemap[tmp].getMine() :
                    self.gamemap[tmp].incrementCote()


    def visitNeighbours(self, i_, j_):
        tmp_ = (i_, j_)
        for i in range(max(0,i_-1), min(NB_COTES,i_+2)):

            for j in range(max(0,j_-1), min(NB_COTES,j_+2)):

                tmp= (i, j)
                if tmp not in self.visited:
                    out = self.gamemap[tmp].valueCote()
                    if out == '0':
                        self.select(i,j)
                    elif self.gamemap[tmp_].valueCote() == '0' and out != '-1':
                        out = self.gamemap[tmp].dig()
                        self.visited.add(tmp)
                        self.sendState(i,j,out)


    def setFlag(self, i, j):
        tmp= (i, j)
        if self.gamemap[tmp].setFlag():
            if self.gamemap[tmp].getFlag():
                self.updateState.emit(i,j,'F')
            else:
                self.updateState.emit(i,j,'X')
        else:
            self.updateState.emit(i,j,self.gamemap[tmp].valueCote())
        return STATUS_PLAYING


    def select(self,i,j):
        tmp= (i, j)

        if tmp not in self.visited and not self.gamemap[tmp].getFlag():
            out = self.gamemap[tmp].dig()
            self.visited.add(tmp)
            self.visitNeighbours(i,j)
            self.sendState(i,j,out)
            if out == -1:
                return STATUS_FAILED
            else:
                if len(self.visited) == ((NB_COTES*NB_COTES)-NB_MINES):
                    return STATUS_SUCCESS
                else:
                    return STATUS_PLAYING
        else:
            return STATUS_PLAYING


    def sendState(self, i, j, out):
        self.updateState.emit(i,j,str(out))

    def revealAll(self):
        for i in range(NB_COTES):
            for j in range(NB_COTES):
                tmp= (i, j)
                if tmp not in self.visited:
                    out = self.gamemap[tmp].reveal()
                    self.visited.add(tmp)
                    self.sendState(i,j,out)

    def reset(self):
        self.gamemap = {}
        self.visited = set()
        self.initMap()


class InfoBanner(QWidget):
    reset = pyqtSignal()
    quit = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, INFOBANNER_WIDTH, CASE_SIZE*NB_COTES)

        self.layout = QVBoxLayout(self)

        self.text = QLabel()
        self.text.setText('NEW GAME')
        self.layout.addWidget(self.text)

        buttonReset = QPushButton("Reset")
        buttonReset.clicked.connect(self.reset)
        self.layout.addWidget(buttonReset)

        buttonLeave = QPushButton("Leave")
        buttonLeave.clicked.connect(self.quit)
        self.layout.addWidget(buttonLeave)

        self.setLayout(self.layout)


    @pyqtSlot(str)
    def updateState(self, state):
        self.text.setText(state)



class CaseDraw(QWidget):
    action = pyqtSignal(int, int, int)
    stateColor= Qt.black
    i = -1
    j = -1
    text = 'X'

    def __init__(self, parent, i_, j_):
        super().__init__(parent)
        self.i = i_;
        self.j = j_;
        self.setGeometry(0, 0, CASE_SIZE, CASE_SIZE)

    def reset(self):
        self.stateColor= Qt.black
        self.text = 'X'
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(QColor(self.stateColor))
        qp.fillRect(0,0,CASE_SIZE,CASE_SIZE, QColor(self.stateColor))
        qp.setPen(QColor(Qt.black))
        qp.drawText(25, 25, self.text)
        qp.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.action.emit(self.i, self.j, 1)
        elif event.button() == Qt.RightButton:
            self.action.emit(self.i, self.j, 2)

    @pyqtSlot(str)
    def updateState(self, state):
        if state == 'X':
            self.stateColor= Qt.black
        elif state == '-1':
            self.stateColor= Qt.red
        elif state == 'F':
            self.stateColor= Qt.blue
        else:
            self.stateColor= Qt.green
        self.text = state
        self.update()


class Grid(QWidget):
    action = pyqtSignal(int, int, int)

    caseMap = {}

    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, CASE_SIZE*NB_COTES, CASE_SIZE*NB_COTES)
        self.initUI()

    def initUI(self):

        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

        for i in range(NB_COTES):
            for j in range(NB_COTES):
                case = CaseDraw(self,i,j)
                case.action.connect(self.action)
                self.caseMap[(i, j)] = case
                self.layout.addWidget(self.caseMap[(i, j)], i, j)


    @pyqtSlot(int, int, str)
    def updateState(self, i, j, state):
        self.caseMap[(i, j)].updateState(state)

    def reset(self):
        for i in range(NB_COTES):
            for j in range(NB_COTES):
                self.caseMap[(i, j)].reset()

class MainWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, CASE_SIZE*NB_COTES+INFOBANNER_WIDTH+MARGIN, CASE_SIZE*NB_COTES+MARGIN)
        self.initUI()

    def initUI(self):
        self.infoBanner = InfoBanner(self)
        self.infoBanner.setFixedWidth(INFOBANNER_WIDTH)
        self.grid = Grid(self)
        self.grid.setFixedWidth(CASE_SIZE*NB_COTES)

        layout = QHBoxLayout()
        layout.addWidget(self.infoBanner, 1)
        layout.addWidget(self.grid, 5)

        self.setLayout(layout)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.resize(CASE_SIZE*NB_COTES+INFOBANNER_WIDTH+MARGIN, CASE_SIZE*NB_COTES+MARGIN)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Démineur')
        self.central_widget = MainWidget(self)
        self.setCentralWidget(self.central_widget)


class GameMgr(QObject):
    action = pyqtSignal(int, int, int)
    endGame = pyqtSignal()
    state = STATUS_READY

    def __init__(self):
        super().__init__()
        self.map = Map()
        self.window = MainWindow()

        self.map.updateState.connect(self.window.central_widget.grid.updateState)
        self.window.central_widget.grid.action.connect(self.action)
        self.window.central_widget.infoBanner.reset.connect(self.reset)
        self.window.central_widget.infoBanner.quit.connect(self.quit)
        self.action.connect(self.actionAsk)

        self.window.show()


    @pyqtSlot(int, int, int)
    def actionAsk(self, i, j, state):

        if self.state == STATUS_READY or self.state == STATUS_PLAYING:
            if state == 2:
                self.state = self.map.setFlag(i, j)
            else:
                self.state = self.map.select(i, j)

        if self.state == STATUS_SUCCESS:
            self.window.central_widget.infoBanner.updateState('YOU WON')
            self.end()
            return
        elif self.state == STATUS_FAILED:
            self.window.central_widget.infoBanner.updateState('YOU LOST')
            self.end()
            return

        if self.state == STATUS_PLAYING:
            self.window.central_widget.infoBanner.updateState('PLAYING')

    def end(self):
        self.map.revealAll()
        #choice = input('Quitting \n')
        #self.endGame.emit()

    @pyqtSlot()
    def quit(self):
        self.endGame.emit()

    @pyqtSlot()
    def reset(self):
        self.state = STATUS_READY
        self.window.central_widget.infoBanner.updateState('NEW GAME')
        self.map.reset()
        self.window.central_widget.grid.reset()

#    def run(self):
#        while (self.state != STATUS_SUCCESS and self.state != STATUS_FAILED):
#            print()
#            self.map.displayMap()
#            self.state = self.play()
#            if self.state == STATUS_FAILED:
#                self.map.displayMap()
#                print("YOU FAILED")
#            elif self.state == STATUS_SUCCESS:
#                self.map.displayMap()
#                print("YOU WON")
#            print()
#        self.map.displayMap(False)


#    def play(self):
#        choice = input('Select F to put a Flag or D to dig\n')
#        if choice == 'F':
#            print()
#            i = input('Select line i from 0 to '+str(NB_COTES-1)+' \n')
#            j = input('Select column j from 0 to '+str(NB_COTES-1)+' \n')
#            print()
#            return self.map.setFlag(int(i),int(j))
#        else:
#            print()
#            i = input('Select line i from 0 to '+str(NB_COTES-1)+' \n')
#            j = input('Select column j from 0 to '+str(NB_COTES-1)+' \n')
#            print()
#            return self.map.select(int(i),int(j))



if __name__ == '__main__':

    app = QApplication(sys.argv)
    game = GameMgr()
    game.endGame.connect(app.exit)
    sys.exit(app.exec_())
