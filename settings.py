# -*- coding: utf-8 -*-
# Spesmilo -- Python Bitcoin user interface
# Copyright © 2011 Luke Dashjr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 only.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from decimal import Decimal
import os
import re
from PySide.QtCore import *
from PySide.QtGui import *

_settings = QSettings('BitCoin', 'Spesmilo')

def icon(*ss):
    if not ss:
        if not hasattr(icon, '_default'):
            icon._default = icon(*icon._defaultSearch)
        return icon._default
    for s in ss:
        if not s:
            continue
        if '/' in s:
            return QIcon(s)
        if QIcon.hasThemeIcon(s):
            return QIcon.fromTheme(s)
    return QIcon()
icon._defaultSearch = ('spesmilo', 'bitcoin', 'icons/bitcoin32.xpm')

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

class SettingsTabLanguage(QWidget):
    def __init__(self, parent, enableApply = None):
        super(SettingsTabLanguage, self).__init__(parent)
        
        mainlay = QFormLayout(self)
        
        self.lang = QComboBox()
        self.lang.addItem(self.tr('American'), 'en_US')
        self.lang.addItem(self.tr('English'), 'en_GB')
        self.lang.addItem(self.tr('Esperanto'), 'eo_EO')
        mainlay.addRow(self.tr('Language:'), self.lang)
        
        nslay = QHBoxLayout()
        self.strength = QComboBox()
        self.strength.addItem(self.tr('Assume'), 'Assume')
        self.strength.addItem(self.tr('Prefer'), 'Prefer')
        self.strength.addItem(self.tr('Force'), 'Force')
        nslay.addWidget(self.strength)
        self.numsys = QComboBox(self)
        self.numsys.addItem(self.tr('Decimal'), 'Decimal')
        self.numsys.addItem(self.tr('Tonal'), 'Tonal')
        nslay.addWidget(self.numsys)
        mainlay.addRow(self.tr('Number system:'), nslay)
        
        self.hideTLA = QCheckBox(self.tr('Hide preferred unit name'))
        mainlay.addRow(self.hideTLA)

        if enableApply is not None:
            self.lang.currentIndexChanged.connect(lambda: enableApply())
            self.numsys.currentIndexChanged.connect(lambda: enableApply())
            self.strength.currentIndexChanged.connect(lambda: enableApply())
            self.hideTLA.stateChanged.connect(lambda: enableApply())
    
    def loadSettings(self, settings = None):
        self.lang.setCurrentIndex(self.lang.findData(settings.value('language/language', 'en_GB')))
        self.numsys.setCurrentIndex(self.numsys.findData(settings.value('units/numsys', 'Decimal')))
        self.strength.setCurrentIndex(self.strength.findData(settings.value('units/strength', 'Assume')))
        self.hideTLA.setChecked(settings.value('units/hideTLA', 'True') != 'False')
    
    def checkSettings(self):
        pass
    
    def saveSettings(self, settings = None):
        settings.setValue('language/language', self.lang.itemData(self.lang.currentIndex()))
        SpesmiloSettings.loadTranslator()
        settings.setValue('units/numsys', self.numsys.itemData(self.numsys.currentIndex()))
        settings.setValue('units/strength', self.strength.itemData(self.strength.currentIndex()))
        settings.setValue('units/hideTLA', repr(self.hideTLA.isChecked()))

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        
        self.settings = _settings
        
        tabw = QTabWidget()
        
        self.tabs = []
        self.tabs.append(('Core', SettingsTabCore(self, self.enableApply)))
        self.tabs.append(('Language', SettingsTabLanguage(self, self.enableApply)))
        
        for name, widget in self.tabs:
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
        
        self.setWindowIcon(icon())
        self.setWindowTitle(self.tr('Settings'))
        self.show()
    
    def loadSettings(self):
        settings = self.settings
        for x, widget in self.tabs:
            widget.loadSettings(settings)
        self.applybtn.setEnabled(False)
    
    def checkSettings(self):
        for x, widget in self.tabs:
            widget.checkSettings()
        
    def saveSettings(self):
        settings = self.settings
        for x, widget in self.tabs:
            widget.saveSettings(settings)
        self.applybtn.setEnabled(False)

    def enableApply(self):
        self.applybtn.setEnabled(True)

class SpesmiloSettings:
    def isConfigured(self):
        NC = 'NOT CONFIGURED'
        return _settings.value('core/internal', NC) != NC
    
    def useInternalCore(self):
        return _settings.value('core/internal', 'True') != 'False'
    
    def getEffectiveURI(self):
        if self.useInternalCore():
            return 'http://user:pass@localhost:8332'
        return _settings.value('core/uri', 'http://user:pass@localhost:8332')

    def getNumberSystem(self):
        return _settings.value('units/numsys', 'Decimal')

    def getNumberSystemStrength(self):
        return _settings.value('units/strength', 'Assume')

    def getHideUnitTLA(self):
        return _settings.value('units/hideTLA', 'True') != 'False'

    def _commafy(self, s, groupsize):
        n = ''
        if s[0] == '-':
            n = s[0]
            s = s[1:]
        firstcomma = len(s) % groupsize or groupsize
        n += s[:firstcomma]
        r = s[firstcomma:]
        segments = (n,) + tuple(r[i:i+groupsize] for i in range(0, len(r), groupsize))
        return ','.join(segments)

    def format_decimal(self, n, addSign = False, wantDelimiters = False, centsHack = False):
        if not type(n) is Decimal:
            n = Decimal(str(n))
        if centsHack and not n % Decimal('.1'):
            n = n.quantize(Decimal('0.00'))
            s = str(n)
        else:
            s = str(int(n)) + str(abs(n % 1) + 1)[1:]
            if n < 0 and int(n) == 0:
                s = '-' + s
        if wantDelimiters:
            s = self._commafy(s, 3)
        if addSign and n >= 0:
                s = "+" + s
        return s

    _toTonalDict = dict(((57, u'\ue9d9'), (65, u'\ue9da'), (66, u'\ue9db'), (67, u'\ue9dc'), (68, u'\ue9dd'), (69, u'\ue9de'), (70, u'\ue9df'), (97, u'\ue9da'), (98, u'\ue9db'), (99, u'\ue9dc'), (100, u'\ue9dd'), (101, u'\ue9de'), (102, u'\ue9df')))
    def format_tonal(self, n, addSign = False, wantDelimiters = False):
        s = "%x" % n
        if wantDelimiters:
            s = self._commafy(s, 4)
        n = abs(n) % 1
        if n:
            s += '.'
            while n:
                n *= 16
                s += "%x" % n
                n %= 1
        s = unicode(s).translate(self._toTonalDict)
        if addSign and n >= 0:
                s = "+" + s
        return s

    _fromTonalDict = dict(((0xe9d9, u'9'), (0xe9da, u'a'), (57, u'a'), (0xe9db, u'b'), (0xe9dc, u'c'), (0xe9dd, u'd'), (0xe9de, u'e'), (0xe9df, u'f')))
    def parse_tonal(self, s, mult = 1):
        s = unicode(s).translate(self._fromTonalDict)
        s = ''.join(s.split(','))
        try:
            i = s.index('.')
            s = s.rstrip('0')
        except ValueError:
            i = len(s)
        n = 0
        if i:
            n = int(s[:i], 16)
        n *= mult
        if mult / (16 ** (len(s) - i - 1)) < 1:
            mult = float(mult)
        for j in range(1, len(s) - i):
            d = int(s[i+j], 16)
            n += (d * mult) / (16 ** j)
        return n

    def format_number(self, n, addSign = False, wantDelimiters = False):
        ns = self.getNumberSystem()
        if ns == 'Tonal':
            ens = self.format_tonal
        else:
            ens = self.format_decimal
        return ens(n, addSign=addSign, wantDelimiters=wantDelimiters)

    def _toBTC(self, n, addSign = False, wantTLA = None, wantDelimiters = False):
        n = Decimal(n) / 100000000
        s = self.format_decimal(n, addSign=addSign, wantDelimiters=wantDelimiters, centsHack=True)
        if wantTLA is None:
            wantTLA = not self.getHideUnitTLA()
        if wantTLA:
            s += " BTC"
        return s

    def _fromBTC(self, s):
        s = float(s)
        s = int(s * 100000000)
        return s

    def _toTBC(self, n, addSign = False, wantTLA = None, wantDelimiters = False):
        n /= float(0x10000)
        s = self.format_tonal(n, addSign=addSign, wantDelimiters=wantDelimiters)
        if wantTLA is None:
            wantTLA = not self.getHideUnitTLA()
        if wantTLA:
            s += " TBC"
        return s

    def _fromTBC(self, s):
        n = self.parse_tonal(s, mult=0x10000)
        return n

    def ChooseUnits(self, n, guess = None):
        if float(n) != n:
            raise ValueError()
        ns = self.getNumberSystem()
        nss = self.getNumberSystemStrength()
        ens = None
        if nss != 'Force' and n:
            # If it's only valid as one, and not the other, choose it
            ivD = 0 == n % 1000000
            ivT = 0 == n % 0x100
            if ivD and not ivT:
                ens = 'Decimal'
            elif ivT and not ivD:
                ens = 'Tonal'
            # If it could be either, pick the more likely one (only with 'Assume')
            elif ivD and nss == 'Assume':
                if not guess is None:
                    ens = guess
                dn = n / 1000000
                tn = n / 0x100
                while ens is None:
                    dm = dn % 10 not in (0, 5)
                    tm = tn % 0x10 not in (0, 8)
                    if dm:
                        if tm:
                            break
                        ens = 'Tonal'
                    elif tm:
                        ens = 'Decimal'
                    dn /= 10.
                    tn /= 16.
        if ens is None: ens = ns
        return ens

    def humanAmount(self, n, addSign = False, wantTLA = None):
        ns = self.getNumberSystem()
        try:
            ens = self.ChooseUnits(n)
        except ValueError:
            return n
        if ens != ns:
            wantTLA = True
        if ens == 'Tonal':
            ens = self._toTBC
        else:
            ens = self._toBTC
        return ens(n, addSign, wantTLA)

    def humanToAmount(self, s):
        ens = self.getNumberSystem()
        m = re.search('\s*\\b(BTC|TBC)\s*$', s, re.IGNORECASE)
        if m:
            if m.group(1) == 'TBC':
                ens = 'Tonal'
            else:
                ens = 'Decimal'
            s = s[:m.start()]
        if ens == 'Tonal':
            ens = self._fromTBC
        else:
            ens = self._fromBTC
        return ens(s)

    def loadTranslator(self):
        lang = _settings.value('language/language', 'en_GB')
        if not hasattr(self, 'translator'):
            self.translator = QTranslator()
        self.translator.load('i18n/%s' % (lang,))
        app = QCoreApplication.instance()
        app.installTranslator(self.translator)

    debugMode = False

SpesmiloSettings = SpesmiloSettings()
format_number = SpesmiloSettings.format_number
humanAmount = SpesmiloSettings.humanAmount
humanToAmount = SpesmiloSettings.humanToAmount

import urllib
class _NotFancyURLopener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        raise NotImplementedError("Wrong or missing username/password")
urllib._urlopener = _NotFancyURLopener()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    SpesmiloSettings.loadTranslator()
    dlg = SettingsDialog(None)
    sys.exit(app.exec_())
