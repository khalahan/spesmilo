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
import subprocess
from PySide.QtCore import *
from PySide.QtGui import *

import anynumber

_settings = QSettings('Bitcoin', 'Spesmilo')

def icon(*ss):
    if not ss:
        if not hasattr(icon, '_default'):
            icon._default = icon(*icon._defaultSearch)
        return icon._default
    if len(ss) == 1:
        ss += ('icons/%s.png' % (ss[0],),)
    for s in ss:
        if not s:
            continue
        if '/' in s:
            return QIcon(s)
        if QIcon.hasThemeIcon(s):
            return QIcon.fromTheme(s)
    return QIcon()
icon._defaultSearch = ('spesmilo', 'bitcoin', 'icons/bitcoin32.png')

def quietPopen(*args, **kwargs):
    if 'startupinfo' not in kwargs and hasattr(subprocess, 'STARTUPINFO'):
        kwargs['startupinfo'] = subprocess.STARTUPINFO()
    if 'startupinfo' in kwargs:
        kwargs['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW if hasattr(subprocess, 'STARTF_USESHOWWINDOW') else 1
    try:
        return subprocess.Popen(*args, **kwargs)
    except:
        class dummy:
            def wait(self):
                return -1
        return dummy()

class SettingsTabBASE(QWidget):
    def __init__(self, parent = None, dlg = None):
        super(SettingsTabBASE, self).__init__(parent)

        if parent:
            self.pp = parent.parent()
            self.pphas = lambda x: hasattr(self.pp, x)
        else:
            self.pphas = lambda x: False

        self.options = []
        self._build()

        self._dlg = dlg
        nea = lambda: dlg.enableApply()
        for o in self.options:
            o._onChange(nea)

    def loadSettings(self, settings = None):
        for o in self.options:
            o._CV = o._load(settings)
            o._OV = o._CV
            o._set(o._CV)

    def checkSettings(self):
        pass

    def saveSettings(self, settings = None):
        RR = False
        for o in self.options:
            nv = o._get()
            if nv != o._CV and nv != o._OV:
                o._CV = nv
                if hasattr(o, '_apply'):
                    if o._apply(nv):
                        RR = True
                    else:
                        o._OV = nv
                else:
                    RR = True
            o._save(settings, nv)
        if RR:
            self._dlg.requireRestart()

class SettingsWidgetMixIn(object):
    def __init__(self, *args, **kwargs):
        self._key = kwargs['key']
        self._default = kwargs['default']
        del kwargs['key']
        del kwargs['default']
        super(SettingsWidgetMixIn, self).__init__(*args, **kwargs)

    def _load(self, settings):
        return settings.value(self._key, self._default)
    def _save(self, settings, newvalue):
        settings.setValue(self._key, newvalue)

class SettingsQCheckBox(SettingsWidgetMixIn, QCheckBox):
    def _onChange(self, slot):
        self.stateChanged.connect(slot)

    def _load(self, settings):
        r = settings.value(self._key, None)
        if r is None:
            return self._default
        return r != 'False'
    def _save(self, settings, newvalue):
        settings.setValue(self._key, repr(newvalue))

    def _get(self):
        return self.isChecked()
    def _set(self, newvalue):
        self.setChecked(newvalue)

class SettingsQComboBox(SettingsWidgetMixIn, QComboBox):
    def _onChange(self, slot):
        self.currentIndexChanged.connect(slot)

    def _get(self):
        return self.itemData(self.currentIndex())
    def _set(self, newvalue):
        self.setCurrentIndex(self.findData(newvalue))

class SettingsQLineEdit(SettingsWidgetMixIn, QLineEdit):
    def _onChange(self, slot):
        self.textChanged.connect(slot)

    def _get(self):
        return self.text()
    def _set(self, newvalue):
        self.setText(newvalue)

class SettingsTabCore(SettingsTabBASE):
    def _build(self):
        cblay = QFormLayout()
        self.cbInternal = SettingsQCheckBox(self, key='core/internal', default=True)
        self.options.append(self.cbInternal)
        self.lblInternal = QLabel(self.tr('Use internal core'))
        cblay.addRow(self.cbInternal, self.lblInternal)
        self.cbInternal.stateChanged.connect(self.updateURIValidity)
        
        lelay = QFormLayout()
        self.lblURI = QLabel(self.tr('URI:'))
        self.leURI = SettingsQLineEdit(key='core/uri', default='http://user:pass@localhost:8332')
        self.options.append(self.leURI)
        lelay.addRow(self.lblURI, self.leURI)

        mainlay = QVBoxLayout(self)
        mainlay.addLayout(cblay)
        mainlay.addLayout(lelay)
    
    def checkSettings(self):
        if quietPopen( ('bitcoind', '--help') ).wait():
            self.cbInternal.setChecked(False)
            self.cbInternal.setEnabled(False)
            self.lblInternal.setEnabled(False)
    
    def updateURIValidity(self):
        en = not self.cbInternal.isChecked()
        self.lblURI.setEnabled(en)
        self.leURI.setEnabled(en)

class SettingsTabLanguage(SettingsTabBASE):
    def _build(self):
        self._deferred = {}
        
        mainlay = QFormLayout(self)
        
        self.lang = SettingsQComboBox(key='language/language', default='')
        langlist = [
            (self.tr('(Default)'), ''),
            (self.tr('American'), 'en_US'),
            (self.tr('English'), 'en_GB'),
            (self.tr('Esperanto'), 'eo'),
            (self.tr('Dutch'), 'nl'),
            (self.tr('French'), 'fr'),
        ]
        langlist.sort()
        for lang in langlist:
            if not (lang[1] in ('', 'en_US') or os.path.exists("i18n/%s.qm" % (lang[1],))):
                continue
            self.lang.addItem(*lang)
        self.options.append(self.lang)
        mainlay.addRow(self.tr('Language:'), self.lang)
        
        nslay = QHBoxLayout()
        self.strength = SettingsQComboBox(key='units/strength', default='Assume')
        self.strength._apply = lambda nv: self._defer_update('amounts')
        self.strength.addItem(self.tr('Assume'), 'Assume')
        self.strength.addItem(self.tr('Prefer'), 'Prefer')
        self.strength.addItem(self.tr('Force'), 'Force')
        self.options.append(self.strength)
        nslay.addWidget(self.strength)
        self.numsys = SettingsQComboBox(self, key='units/numsys', default='Decimal')
        self.numsys._apply = lambda nv: self._defer_update('counters', 'amounts')
        self.numsys.addItem(self.tr('Decimal'), 'Decimal')
        self.numsys.addItem(self.tr('Tonal'), 'Tonal')
        self.options.append(self.numsys)
        nslay.addWidget(self.numsys)
        mainlay.addRow(self.tr('Number system:'), nslay)
        
        self.hideTLA = SettingsQCheckBox(self.tr('Hide preferred unit name'), key='units/hideTLA', default=True)
        self.hideTLA._apply = lambda nv: self._defer_update('amounts')
        self.options.append(self.hideTLA)
        mainlay.addRow(self.hideTLA)
    
    def _defer_update(self, *updates):
        RR = False
        for update in updates:
            update = 'update_%s' % (update,)
            if self.pphas(update):
                self._deferred[update] = True
            else:
                RR = True
        return RR

    def saveSettings(self, *args, **kwargs):
        super(SettingsTabLanguage, self).saveSettings(*args, **kwargs)
        for du in self._deferred.iterkeys():
            getattr(self.pp, du)()
        self._deferred = {}

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super(SettingsDialog, self).__init__(parent)
        
        self.settings = _settings
        
        tabw = QTabWidget()
        
        self.tabs = []
        self.tabs.append((self.tr('Core'), SettingsTabCore(self, self)))
        self.tabs.append((self.tr('Language'), SettingsTabLanguage(self, self)))
        
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

    def requireRestart(self):
        if not (hasattr(self.parent(), 'core') and self.parent().core):
            return
        msg = QMessageBox(QMessageBox.Information,
                          self.tr('Restart required'),
                          self.tr('Restarting Spesmilo is required for some changes to take effect.'))
        msg.exec_()

class SpesmiloSettings:
    def isConfigured(self):
        NC = 'NOT CONFIGURED'
        return _settings.value('core/internal', NC) != NC
    
    def useInternalCore(self):
        return _settings.value('core/internal', 'True') != 'False'
    
    def getInternalCoreAuth(self):
        if not hasattr(self, '_ICA'):
            from random import random
            passwd = random()
            self._ICA = ('spesmilo', passwd, 8342)
        return self._ICA

    def getEffectiveURI(self):
        if self.useInternalCore():
            return 'http://%s:%s@127.0.0.1:%d' % self.getInternalCoreAuth()
        return _settings.value('core/uri', 'http://user:pass@localhost:8332')

    def getNumberSystem(self):
        return _settings.value('units/numsys', 'Decimal')

    def getNumberSystemStrength(self):
        return _settings.value('units/strength', 'Assume')

    def getHideUnitTLA(self):
        return _settings.value('units/hideTLA', 'True') != 'False'

    def format_number(self, n, addSign = False, wantDelimiters = False):
        ns = self.getNumberSystem()
        if ns == 'Tonal':
            n = anynumber.Tonal(n)
        else:
            n = anynumber.Decimal(n)
        return n.format(addSign=addSign, wantDelimiters=wantDelimiters)

    def _toBTC(self, n, addSign = False, wantTLA = None, wantDelimiters = False):
        n = anynumber.Decimal(n) / 100000000
        s = n.format(addSign=addSign, wantDelimiters=wantDelimiters)
        if '.' not in s:
            s += '.00'
        elif s[-2] == '.':
            s += '0'
        if wantTLA is None:
            wantTLA = not self.getHideUnitTLA()
        if wantTLA:
            s += " BTC"
        return s

    def _fromBTC(self, s):
        s = anynumber.Decimal(s)
        s = int(s * 100000000)
        return s

    def _toTBC(self, n, addSign = False, wantTLA = None, wantDelimiters = False):
        n = anynumber.Tonal(n) / 0x10000
        s = n.format(addSign=addSign, wantDelimiters=wantDelimiters)
        if wantTLA is None:
            wantTLA = not self.getHideUnitTLA()
        if wantTLA:
            s += " TBC"
        return s

    def _fromTBC(self, s):
        n = int(anynumber.Tonal(s) * 0x10000)
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
        lang = _settings.value('language/language', '')
        if not lang:
            lang = os.getenv('LC_ALL') \
                or os.getenv('LC_MESSAGES') \
                or os.getenv('LANG')
            if not lang:
                return
        if not hasattr(self, 'translator'):
            self.translator = QTranslator()
        self.translator.load(lang, 'i18n')
        app = QCoreApplication.instance()
        app.installTranslator(self.translator)

    debugMode = False

SpesmiloSettings = SpesmiloSettings()
format_number = SpesmiloSettings.format_number
humanAmount = SpesmiloSettings.humanAmount
humanToAmount = SpesmiloSettings.humanToAmount

import urllib
class _NotFancyURLopener(urllib.FancyURLopener):
    def tr(self, s):
        from PySide.QtGui import qApp
        return qApp.translate('_NotFancyURLopener', s)

    def prompt_user_passwd(self, host, realm):
        raise NotImplementedError(self.tr("Wrong or missing username/password"))
urllib._urlopener = _NotFancyURLopener()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    SpesmiloSettings.loadTranslator()
    dlg = SettingsDialog(None)
    sys.exit(app.exec_())
