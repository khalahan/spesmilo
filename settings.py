# -*- coding: utf-8 -*-
from PySide.QtCore import *
from PySide.QtGui import *

_settings = QSettings('BitCoin', 'Spesmilo')

class SettingsTabCore(QWidget):
    def __init__(self, parent, enableApply = None):
        super(SettingsTabCore, self).__init__(parent)
        
        cblay = QFormLayout()
        self.cbInternal = QCheckBox(self)
        self.lblInternal = QLabel(self.tr('Use internal core'))
        cblay.addRow(self.cbInternal, self.lblInternal)
        self.cbInternal.stateChanged.connect(self.updateURIValidity)
        
        lelay = QFormLayout()
        self.lblURI = QLabel(self.tr('URI:'))
        self.leURI = QLineEdit()
        lelay.addRow(self.lblURI, self.leURI)

        mainlay = QVBoxLayout(self)
        mainlay.addLayout(cblay)
        mainlay.addLayout(lelay)
        
        if enableApply is not None:
            self.cbInternal.stateChanged.connect(lambda: enableApply())
            self.leURI.textChanged.connect(lambda: enableApply())
    
    def loadSettings(self, settings = None):
        self.cbInternal.setChecked(settings.value('core/internal', 'True') != 'False')
        self.leURI.setText(settings.value('core/uri', 'http://user:pass@localhost:8332'))
    
    def checkSettings(self):
        if os.system('bitcoind --help'):
            self.cbInternal.setChecked(False)
            self.cbInternal.setEnabled(False)
            self.lblInternal.setEnabled(False)
    
    def saveSettings(self, settings = None):
        settings.setValue('core/internal', repr(self.cbInternal.isChecked()))
        settings.setValue('core/uri', self.leURI.text())
    
    def updateURIValidity(self):
        en = not self.cbInternal.isChecked()
        self.lblURI.setEnabled(en)
        self.leURI.setEnabled(en)

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        
        self.settings = _settings
        
        tabw = QTabWidget()
        
        self.tabs = {}
        self.tabs['Core'] = SettingsTabCore(self, self.enableApply)
        
        for name, widget in self.tabs.items():
            tabw.addTab(widget, name)
        
        mainlay = QVBoxLayout(self)
        mainlay.addWidget(tabw)
        
        actionlay = QHBoxLayout()
        actionlay.addStretch()
        
        okbtn = QPushButton(self.tr('&OK'))
        okbtn.clicked.connect(self.accept)
        okbtn.setAutoDefault(True)
        actionlay.addWidget(okbtn)
        
        applybtn = QPushButton(self.tr('&Apply'))
        self.applybtn = applybtn
        applybtn.clicked.connect(lambda: self.saveSettings())
        actionlay.addWidget(applybtn)
        
        cancelbtn = QPushButton(self.tr('&Cancel'))
        cancelbtn.clicked.connect(self.reject)
        actionlay.addWidget(cancelbtn)

        mainlay.addLayout(actionlay)
        
        self.loadSettings()
        self.checkSettings()
        
        self.accepted.connect(lambda: self.saveSettings())
        
        if parent is not None:
            self.setWindowIcon(parent.bitcoin_icon)
        self.setWindowTitle(self.tr('Settings'))
        self.show()
    
    def loadSettings(self):
        settings = self.settings
        for widget in self.tabs.values():
            widget.loadSettings(settings)
        self.applybtn.setEnabled(False)
    
    def checkSettings(self):
        for widget in self.tabs.values():
            widget.checkSettings()
        
    def saveSettings(self):
        settings = self.settings
        for widget in self.tabs.values():
            widget.saveSettings(settings)
        self.applybtn.setEnabled(False)

    def enableApply(self):
        self.applybtn.setEnabled(True)

class SpesmiloSettings:
    def getEffectiveURI(self):
        if _settings.value('core/internal', 'True') == 'False':
            return _settings.value('core/uri', 'http://user:pass@localhost:8332')
        return 'http://user:pass@localhost:8332'

SpesmiloSettings = SpesmiloSettings()

if __name__ == '__main__':
    import os
    import sys
    translator = QTranslator()
    #translator.load('data/translations/eo_EO')
    app = QApplication(sys.argv)
    dlg = SettingsDialog(None)
    sys.exit(app.exec_())
