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
import re
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from settings import humanAmount, humanToAmount, SpesmiloSettings

class SendDialog(QDialog):
    def __init__(self, core, parent, uri = None):
        super(SendDialog, self).__init__(parent)
        self.core = core
        
        formlay = QFormLayout()
        self.destaddy = QLineEdit()
        self.amount = QLineEdit()
        self.amount.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        amount_max_width = self.fontMetrics().averageCharWidth() * 10
        self.amount.setMaximumWidth(amount_max_width)
        dv = QDoubleValidator(self.amount)
        dv.setDecimals(2)
        dv.setNotation(QDoubleValidator.StandardNotation)
        self.dv = dv
        tv = QRegExpValidator(QRegExp('-?(?:[\d\\xe9d9-\\xe9df]+\.?|[\d\\xe9d9-\\xe9df]*\.[\d\\xe9d9-\\xe9df]{1,4})'), self.amount)
        self.tv = tv
        self.amount_unit = QComboBox(self)
        self.amount_unit.addItem(self.tr("BTC"), "BTC")
        self.amount_unit.addItem(self.tr("TBC"), "TBC")
        self.amount_unit.currentIndexChanged.connect(self.update_validator)
        prefunit = 'TBC' if SpesmiloSettings.getNumberSystem() == 'Tonal' else 'BTC'
        self.amount_unit.setCurrentIndex(self.amount_unit.findData(prefunit))
        formlay.addRow(self.tr('Pay to:'), self.destaddy)
        amountlay = QHBoxLayout()
        amountlay.addWidget(self.amount)
        amountlay.addWidget(self.amount_unit)
        amountlay.addStretch()
        formlay.addRow(self.tr('Amount:'), amountlay)

        actionlay = QHBoxLayout()
        sendbtn = QPushButton(self.tr('&Send'))
        sendbtn.clicked.connect(self.do_payment)
        sendbtn.setAutoDefault(True)
        cancelbtn = QPushButton(self.tr('&Cancel'))
        cancelbtn.clicked.connect(self.reject)
        actionlay.addStretch()
        actionlay.addWidget(sendbtn)
        actionlay.addWidget(cancelbtn)

        # layout includes form + instructions
        instructions = QLabel(self.tr('<i>Enter a bitcoin address (e.g. 1A9Pv2PYuZYvfqku7sJxovw99Az72mZ4YH)</i>'))
        mainlay = QVBoxLayout(self)
        mainlay.addWidget(instructions)
        mainlay.addLayout(formlay)
        mainlay.addLayout(actionlay)

        if parent is not None:
            self.setWindowIcon(parent.bitcoin_icon)
        self.setWindowTitle(self.tr('Send bitcoins'))

        if not uri is None:
            self.load_uri(uri)

        self.show()
        self.destaddy.setFocus()

    def load_uri(self, uri):
        m = re.match(r'^bitcoin\:([1-9A-HJ-NP-Za-km-z]+)(?:\?(.*))?$', uri)
        if m is None:
            raise RuntimeError('Invalid bitcoin URI')
        addr = m.group(1)
        query = m.group(2)
        param = {}
        if not query is None:
            query = re.split(r'[&?;]', query)
            for q in query:
                k, v = q.split('=', 1)
                param[k] = v
        self.destaddy.setText(addr)
        if 'amount' in param:
            amount = param['amount']
            m = re.match(r'^(([\d.]+)(X(\d+))?|x([\da-f]*)(\.([\da-f]*))?(X([\da-f]+))?)$', amount, re.IGNORECASE)
            if m.group(5):
                # TBC
                amount = float(int(m.group(5), 16))
                if m.group(7):
                    amount += float(int(m.group(7), 16)) * pow(16, -(len(m.group(7))))
                if m.group(9):
                    amount *= pow(16, int(m.group(9), 16))
                else:
                    amount *= 0x10000
                NU = 'Tonal'
            else:
                amount = Decimal(m.group(2))
                if m.group(4):
                    amount *= 10 ** int(m.group(4))
                else:
                    amount *= 100000000
                NU = 'Decimal'
            amount = int(amount)
            NU = SpesmiloSettings.ChooseUnits(amount, NU)
            if NU == 'Tonal':
                self.amount_unit.setCurrentIndex(self.amount_unit.findData('TBC'))
                amount = SpesmiloSettings._toTBC(amount, addSign=False, wantTLA=False)
            else:
                self.amount_unit.setCurrentIndex(self.amount_unit.findData('BTC'))
                amount = SpesmiloSettings._toBTC(amount, addSign=False, wantTLA=False)
            self.amount.setText(amount)

    def update_validator(self):
        u = self.amount_unit.itemData(self.amount_unit.currentIndex())
        if u == 'BTC':
            self.amount.setValidator(self.dv)
        elif u == 'TBC':
            self.amount.setValidator(self.tv)
        else:
            self.amount.setValidator(None)

    def do_payment(self):
        if not self.amount.text():
            self.amount.setFocus(Qt.OtherFocusReason)
            return
        self.hide()

        addy = self.destaddy.text()
        if not self.core.validate_address(addy):
            error = QMessageBox(QMessageBox.Critical, 
                                self.tr('Invalid address'),
                                self.tr('Invalid address: %s')%addy)
            error.exec_()
            self.reject()
            return

        amount = self.amount.text()
        amount += ' ' + self.amount_unit.itemData(self.amount_unit.currentIndex())
        amount = humanToAmount(amount)

        balance = self.core.balance()
        if amount > balance:
            error = QMessageBox(QMessageBox.Critical, 
                                self.tr('Insufficient balance'),
                            self.tr('Balance of %g is too small.') % (humanAmount(balance),))
            error.exec_()
            self.reject()
            return

        try:
            self.core.send(addy, amount)
        except Exception, e:
            error = QMessageBox(QMessageBox.Critical, 
                                self.tr('Error sending'),
                            self.tr('Your send failed: %s') % (e,))
            error.exec_()
            self.reject()
            return
        self.accept()

if __name__ == '__main__':
    import os
    import sys
    import core_interface
    from settings import SpesmiloSettings
    os.system('bitcoind')
    app = QApplication(sys.argv)
    SpesmiloSettings.loadTranslator()
    uri = SpesmiloSettings.getEffectiveURI()
    core = core_interface.CoreInterface(uri)
    send = SendDialog(core, None, sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(app.exec_())
