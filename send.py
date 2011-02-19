from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from settings import humanAmount, humanToAmount, SpesmiloSettings

class SendDialog(QDialog):
    def __init__(self, core, parent):
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
        self.show()
        self.destaddy.setFocus()

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
    translator = QTranslator()
    #translator.load('data/translations/eo_EO')
    app = QApplication(sys.argv)
    uri = SpesmiloSettings.getEffectiveURI()
    core = core_interface.CoreInterface(uri)
    send = SendDialog(core, None)
    sys.exit(app.exec_())
