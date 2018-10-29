import sys, os, time, glob, random
from threading import Thread
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import QThread
import queue

basedir = '/sys/bus/w1/devices/'
probe1 = '28-031671bda9ff/'
tempfile = basedir+probe1+'w1_slave'
tempvalid = False

#UI Files
qtCreatorFile = "Temp_Display.ui" # Enter file here.
ProfileMenu = "ProfileSetup.ui"

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
Ui_ProfileSetup, QtBaseClass = uic.loadUiType(ProfileMenu)

class tempThread(QThread):
    def __init__(self):
        QThread.__init__(self)
        
    def __del__(self):
        self.wait()
    
    def _get_temperature(self):
        f = open(tempfile)
        raw_data = f.readlines()
        if 'YES' in raw_data[0]:
            tempvalid = True
            temp_pos = raw_data[1].find('t=')
            temp_str = raw_data[1][temp_pos+2:]
            temp = float(temp_str)/1000
            temp_f = temp*9/5+32
        #Test random temperatures if no probe hooked up        
        #temp_f = random.randrange(60, 80)
        return temp_f

    def write_temp(self, temp_form, datafile):
        os.chdir('data')
        fname = time.strftime('%d%m%Y')
        f=open(datafile + ".csv", 'a')
        f.write(time.strftime('%S%M%H%d') + ',' + temp_form + "\n")
        f.close()
        os.chdir("..")

    def run(self):
        #setup data file
        os.chdir('data')
        datafile = time.strftime('%M%H%d%m%Y')
        f=open(datafile + ".csv", 'w')
        f.close()
        os.chdir("..") 
        while True:
            temp = self._get_temperature()
            temp_form = "{0:.2f}".format(temp)
            self.write_temp(temp_form, datafile)
            self.emit(QtCore.SIGNAL("disp_temp(QString)"), temp_form)
            self.emit(QtCore.SIGNAL("float_temp"), temp)
            #q.put(temp_form)
            print(temp_form)
            self.sleep(1)

class MyApp(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        #Start variable, heating cooling variables, 
        self.started = False
        self.coolON = False
        self.heatON = False
        #Set Temperature, heat delta, cool delta variables default
        self.settempvar = 68.0
        self.heatdelta = 1.0
        self.cooldelta = 1.0
        #Connect start and stop buttons, profile setup
        self.startButton.clicked.connect(self.start)
        self.stopButton.clicked.connect(self.stop)
        self.actionSettings.triggered.connect(self.ProfileMenuStart)
        self.actionClose.triggered.connect(self.closeEvent)
        self.setTemp.setText(str(self.settempvar))
        #set up LEDs, remove button border, default off
        self.heatLED.setStyleSheet('border:none')
        self.coolLED.setStyleSheet('border:none')
        self.LEDon = QtGui.QIcon('red-led-on-hi.png')
        self.LEDoff = QtGui.QIcon('red-led-off-hi.png')
        self.heatLED.setIcon(self.LEDoff)
        self.coolLED.setIcon(self.LEDoff)
        #auto updates on change
        self.setTemp.textChanged.connect(self.settempoverride)


    def start(self):
        if not self.started:
            self.started = True
            self.get_thread = tempThread()
            self.connect(self.get_thread, QtCore.SIGNAL("disp_temp(QString)"), self.disp_temp)
            self.connect(self.get_thread, QtCore.SIGNAL("float_temp"), self.heating_cooling)
            self.get_thread.start()
        else:
            print('Already started')
        
    def stop(self):
        self.started = False
        self.tempDisplay.setText("")
        self.get_thread.terminate()
        self.heatLED.setIcon(self.LEDoff)
        self.coolLED.setIcon(self.LEDoff)
        
    def disp_temp(self, temp_form):
        self.tempDisplay.setText(temp_form + " Farenheit")

    def heating_cooling(self, temp):
        settemp = self.settempvar
        #Cooling Condition
        if (temp > (settemp+self.cooldelta) and self.coolON == False):
            self.coolON = True
            self.heatON = False
            self.heatLED.setIcon(self.LEDoff)
            self.coolLED.setIcon(self.LEDon)
        #Heating Condition
        elif (temp < (settemp-self.heatdelta) and self.heatON == False):
            self.heatON = True
            self.coolON = False
            self.heatLED.setIcon(self.LEDon)
            self.coolLED.setIcon(self.LEDoff)
        
        #continue cooling until set temperature
        elif (temp > settemp and self.coolON == True):
            print('cooling')
         
        #continue heating until set temperature
        elif (temp < settemp and self.heatON == True):
            print('heating')

        else:
            self.heatON = False
            self.coolON = False
            self.heatLED.setIcon(self.LEDoff)
            self.coolLED.setIcon(self.LEDoff)

    def ProfileMenuStart(self):
        self.profilemenustart = ProfileSetupMenu(self)
        self.connect(self.profilemenustart, QtCore.SIGNAL("setTempProfile"), self.updateProfile)
        self.profilemenustart.show()
    
    def updateProfile(self, setTempProfile, coolDeltaProfile, heatDeltaProfile):
        self.settempvar = setTempProfile
        print(self.settempvar)
        self.cooldelta = coolDeltaProfile
        print(self.cooldelta)
        self.heatdelta = heatDeltaProfile
        print(self.heatdelta)
        self.setTemp.setText(str(setTempProfile))

#manual override for the Set Temperature
    def settempoverride(self):
        self.settempvar = float(self.setTemp.text())
        return self.settempvar
        
    def closeEvent(self, event):
        self.close()

class ProfileSetupMenu(QtGui.QWidget, Ui_ProfileSetup):
    def __init__(self, parent=None):
        #init
        QtGui.QWidget.__init__(self)
        Ui_ProfileSetup.__init__(self)
        self.setupUi(self)
        ##
        #Default Profile Setup Values
        self.setTempProfile.setText('71')
        self.coolDelta.setText('0.5')
        self.heatDelta.setText('1.0')
        #connect buttons
        self.Cancel.clicked.connect(self.closeEvent)
        self.Apply.clicked.connect(self.applyProfile)
        
    def applyProfile(self):
        setTempProfile = float(self.setTempProfile.text())
        coolDeltaProfile = float(self.coolDelta.text())
        heatDeltaProfile = float(self.heatDelta.text())
        self.emit(QtCore.SIGNAL("setTempProfile"), setTempProfile, coolDeltaProfile, heatDeltaProfile)
        #float_coolDelta = float(coolDelta)
        #float_heatDelta = float(heatDelta)
        self.close()
        
    def closeEvent(self, event):
        self.close()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    window.show()
    q=queue.Queue(maxsize = 3)
    sys.exit(app.exec_())
