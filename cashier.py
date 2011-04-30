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

import re
from time import time
from PySide.QtCore import *
from PySide.QtGui import *
import send
from settings import SpesmiloSettings, humanAmount, format_number, icon, style_item, disable_item

class FocusLineEdit(QLineEdit):
    def __init__(self, text):
        super(FocusLineEdit, self).__init__(text)
        self.setReadOnly(True)
        self.setMaxLength(40)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursorPosition(100)
            self.selectAll()
            event.accept()
        else:
            super(FocusLineEdit, self).mousePressEvent(event)

    def focusOutEvent(self, event):
        event.accept()

    def sizeHint(self):
        sizeh = super(FocusLineEdit, self).sizeHint()
        FM = self.fontMetrics()
        aw = [FM.width(L) for L in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz']
        aw.sort()
        mw = aw[30]
        sizeh.setWidth(mw * self.maxLength())
        return sizeh

class TransactionItem(QTableWidgetItem):
    def __init__(self, text, align=Qt.AlignLeft):
        super(TransactionItem, self).__init__(text)
        self.setFlags(Qt.ItemIsEnabled)
        self.setTextAlignment(align|Qt.AlignVCenter)

class TransactionsTable(QTableWidget):
    # These are the proportions for the various columns
    hedprops = (0x80, 0x70, 0x150, 0x68, 0)

    def __init__(self):
        super(TransactionsTable, self).__init__()

        self.setColumnCount(5)
        hedlabels = (self.tr('Status'),
                     self.tr('Date'),
                     self.tr('Transactions'),
                     self.tr('Credits'),
                     self.tr('Balance'))
        self.setHorizontalHeaderLabels(hedlabels)
        for i, sz in enumerate(self.hedprops):
            self.horizontalHeader().resizeSection(i, sz)
        self.hideColumn(4)

        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAlternatingRowColors(True)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setStretchLastSection(True)

    # Resize columns while maintaining proportions
    def resizeEvent(self, event):
        self_width = event.size().width()
        total_prop_width = sum(self.hedprops)
        newszs = [sz * self_width / total_prop_width for sz in self.hedprops]
        for i, sz in enumerate(newszs):
            self.horizontalHeader().resizeSection(i, sz)

    def update_confirmation(self, i, increment, adjustment = True):
        status_item = self.item(i, 0)
        hastxt = len(status_item.text())
        confirms = status_item.confirmations
        if confirms is None:
            return
        category = status_item.category if hasattr(status_item, 'category') else None
        if adjustment:
            if self.confirmation_stage(category, confirms) < 0x100:
                return
            confirms = confirms + increment
        else:
            if increment == confirms and hastxt:
                return
            confirms = increment

        row_disabled = False
        stage = self.confirmation_stage(category, confirms)
        sf = None
        if stage:
            if stage == 0x100:
                status = self.tr('Confirmed (%s)')
            else:
                status = self.tr('Processing... (%s)')
            if self.confirmation_stage(category, status_item.confirmations) < stage:
                sf = self.enable_table_item
        else:
            status = self.tr('Validating... (%s)')
            if not hastxt:
                sf = self.disable_table_item
        status %= (format_number(confirms),)

        status_item.setText(status)
        status_item.confirmations = confirms

        if sf:
            for j in range(0, 5):
                sf(self.item(i, j))

    def update_transaction_time(self, row, unixtime):
        date_formatter = QDateTime()
        date_formatter.setTime_t(unixtime)
        # we need to do this in parts to have a month name translation
        # datetime = date_formatter.toString('hh:mm d ')
        # datetime += self.tr(date_formatter.toString('MMM '))
        # datetime += date_formatter.toString('yy')
        datetime = date_formatter.toString('hh:mm d MMM yy')
        date_item = self.item(row, 1)
        date_item.setText(datetime)

    def add_transaction_entry(self, transaction):
        self.insertRow(0)
        confirms = None
        if 'confirmations' in transaction:
            confirms = transaction['confirmations']
        unixtime = transaction['time']
        address = 'N/A'
        if 'address' in transaction:
            address = transaction['address']
        credit =  transaction['amount']
        balance = 'N/A'
        category = transaction['category']

        status_item = TransactionItem('')
        if confirms is None:
            status_item.setText('N/A')
        status_item.confirmations = confirms
        self.setItem(0, 0, status_item)

        date_item = TransactionItem('')
        self.setItem(0, 1, date_item)
        self.update_transaction_time(0, unixtime)

        if category == 'send':
            description = self.tr('Sent to %s')%address
        elif category == 'receive':
            description = self.tr('Received to %s')%address
        elif category in ('generate', 'immature'):
            description = self.tr('Generated')
            status_item.category = category
        elif category == 'move':
            description = self.tr('Moved')
        else:
            description = self.tr('Unknown')
        trans_item = TransactionItem(description)
        self.setItem(0, 2, trans_item)

        credits_item = TransactionItem(humanAmount(credit), Qt.AlignRight)
        credits_item.amount = credit
        self.setItem(0, 3, credits_item)

        balance_item = TransactionItem(humanAmount(balance), Qt.AlignRight)
        self.setItem(0, 4, balance_item)

        self.update_confirmation(0, confirms, adjustment=False)

        return status_item

    def move_row(self, from_row, to_row):
        items = []
        CC = self.columnCount()
        for col in xrange(CC):
            items.append(self.takeItem(from_row, col))
        self.removeRow(from_row)
        self.insertRow(to_row)
        for col in xrange(CC):
            self.setItem(to_row, col, items[col])

    def update_amounts(self):
        for i in xrange(self.rowCount()):
            credits_item = self.item(i, 3)
            credits_item.setText(humanAmount(credits_item.amount))

    def update_counters(self):
        for i in xrange(self.rowCount()):
            status_item = self.item(i, 0)
            status_item.setText('')
            self.update_confirmation(i, status_item.confirmations, adjustment=False)

    def update_confirmations(self, increment, adjustment = True):
        if increment == 0 and adjustment:
            return
        for i in range(0, self.rowCount()):
            self.update_confirmation(i, increment, adjustment)

    def enable_table_item(self, item):
        if not hasattr(self, '_eti'):
            # Must already be enabled :p
            return
        style_item(item, self._eti)

    def disable_table_item(self, item):
        want_old = not hasattr(self, '_eti')
        rv = disable_item(item, want_old=want_old)
        if want_old:
            self._eti = rv

class Cashier(QDialog):
    def __init__(self, core, clipboard, parent=None, tray=None):
        super(Cashier, self).__init__(parent)
        self.core = core
        self.clipboard = clipboard
        self.tray = tray

        self.create_actions()
        main_layout = QVBoxLayout(self)

        youraddy = QHBoxLayout()
        # Balance + Send button
        self.balance_label = QLabel()
        self.refresh_balance()
        sendbtn = QToolButton(self)
        sendbtn.setDefaultAction(self.send_act)
        # Address + New button + Copy button
        uraddtext = QLabel(self.tr('Your address:'))
        self.addy = FocusLineEdit(self.core.default_address())
        newaddybtn = QToolButton(self)
        newaddybtn.setDefaultAction(self.newaddy_act)
        copyaddybtn = QToolButton(self)
        copyaddybtn.setDefaultAction(self.copyaddy_act)
        # Add them to the layout
        youraddy.addWidget(uraddtext)
        youraddy.addWidget(self.addy)
        youraddy.addWidget(newaddybtn)
        youraddy.addWidget(copyaddybtn)
        youraddy.addStretch()
        settingsbtn = QToolButton(self)
        settingsbtn.setDefaultAction(self.settings_act)
        youraddy.addWidget(settingsbtn)
        youraddy.addStretch()
        youraddy.addWidget(self.balance_label)
        youraddy.addWidget(sendbtn)
        main_layout.addLayout(youraddy)

        self.transactions_table = TransactionsTable()
        main_layout.addWidget(self.transactions_table)

        #webview = QWebView()
        #webview.load('http://bitcoinwatch.com/')
        #webview.setFixedSize(880, 300)
        #mf = webview.page().mainFrame()
        #mf.setScrollBarPolicy(Qt.Horizontal,
        #                      Qt.ScrollBarAlwaysOff)
        #mf.setScrollBarPolicy(Qt.Vertical,
        #                      Qt.ScrollBarAlwaysOff)
        #main_layout.addWidget(webview)

        caption = self.tr('Spesmilo')
        if parent is not None:
            self.setWindowIcon(parent.bitcoin_icon)
            if parent.caption:
                caption = parent.caption
        self.setWindowTitle(caption)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        self.txload_initial = 0x1000
        self.txload_poll = 8
        self.txload_waste = 8
        self._refresh_transactions_debug = []
        self.transactions_table.confirmation_stage = self.confirmation_stage

        refresh_info_timer = QTimer(self)
        refresh_info_timer.timeout.connect(self.refresh_info)
        refresh_info_timer.start(1000)
        # Stores last transaction added to the table
        self.last_tx = None
        self.last_tx_with_confirmations = None
        # Used for updating number of confirms
        self.unconfirmed_tx = []
        #   key=txid, category  val=row, confirms
        self.trans_lookup = {}
        self.refresh_info()
        #self.transactions_table.add_transaction_entry({'confirmations': 3, 'time': 1223332, 'address': 'fake', 'amount': 111, 'category': 'send'})
        #self.transactions_table.add_transaction_entry({'confirmations': 0, 'time': 1223332, 'address': 'fake', 'amount': 111, 'category': 'send'})

        self.resize(640, 420)

    def confirmation_stage(self, category, confirms):
        sch = self.confirmation_stage.sch
        if category not in sch:
            category = None
        sch = sch[category]
        if confirms < sch[0]:
            return 0
        if sch[1] is None or confirms < sch[1]:
            return 0x80
        return 0x100
    confirmation_stage.sch = {}
    confirmation_stage.sch[None] = (2, 6)
    confirmation_stage.sch['generate'] = (100, 120)
    confirmation_stage.sch['immature'] = (100, None)

    def refresh_info(self):
        self.refresh_balance()
        self.refresh_transactions()

    def __etxid(self, t):
        txid = t['txid']
        category = t['category']
        if category == 'immature':
            category = 'generate'
        etxid = "%s/%s" % (txid, category)
        return etxid

    def update_amounts(self):
        self.transactions_table.update_amounts()

    def update_counters(self):
        self.refresh_balance_label()
        self.transactions_table.update_counters()

    def refresh_transactions(self):
        debuglog = []
        fetchtx = self.txload_initial
        utx = {}
        if not self.last_tx is None:
            # Figure out just how many fetches are needed to comfortably update new unconfirmed tx
            fetchtx = 0
            debuglog += [{'raw_unconfirmed_tx': self.unconfirmed_tx}]
            for etxid, status_item in self.unconfirmed_tx:
                row = self.transactions_table.row(status_item)
                utx[etxid] = [status_item, None]
                debuglog += ["Present unconfirmed tx %s at row %d" % (etxid, row)]
                # Allow up to 5 wasted refetches in between unconfirmed refetches
                if row <= fetchtx + self.txload_waste:
                    fetchtx = row + 1
            fetchtx += self.txload_poll
        while True:
            debuglog += ["Fetching %d transactions" % (fetchtx,)]
            transactions = self.core.transactions('*', fetchtx)
            debuglog += [{'raw_txlist': transactions}]

            # Sort through fetched transactions, updating confirmation counts
            ttf = len(transactions)
            transactions.reverse()
            otl = []
            nltwc = None
            nomore = False
            petime = time()
            if self.last_tx:
                petime += .001
            for i in xrange(ttf):
                nowtime = time()
                if petime < nowtime and self.parent():
                    self.parent().app.processEvents()
                    petime = nowtime + .001
                t = transactions[i]
                if 'txid' not in t:
                    continue
                txid = t['txid'] if 'txid' in t else False
                category = t['category']
                if 'confirmations' in t:
                    confirms = t['confirmations']
                    if nltwc is None and self.confirmation_stage(category, confirms) == 0x100:
                        nltwc = t
                        debuglog += ["New last_tx_with_confirmations = %s" % (txid,)]
                    if txid == self.last_tx_with_confirmations:
                        ci = confirms - self.last_tx_with_confirmations_n
                        debuglog += ["Found last_tx_with_confirmations (%s) with %d confirms (+%d)" % (txid, confirms, ci)]
                        if ci:
                            self.transactions_table.update_confirmations(ci)
                        self.last_tx_with_confirmations_n = confirms
                    etxid = self.__etxid(t)
                    if etxid in utx:
                        utx[etxid][1] = (t,)
                if nomore:
                    continue
                if txid == self.last_tx:
                    debuglog += ["Found last recorded tx (%s)" % (txid,)]
                    nomore = True
                    if i >= self.txload_poll:
                        self.txload_poll = i + 1
                    continue
                if category == 'orphan':
                    continue
                otl.append(t)
            transactions = otl

            if nomore or fetchtx > ttf: break

            # If we get here, that means we didn't fetch enough to see our last confirmed tx... retry, this time getting more
            fetchtx *= 2

        if not nltwc is None:
            self.last_tx_with_confirmations = nltwc['txid']
            self.last_tx_with_confirmations_n = nltwc['confirmations']

        if transactions:
            transactions.reverse()
            debuglog += [{'new_txlist': transactions}]

            # Add any new transactions
            for t in transactions:
                etxid = self.__etxid(t)
                if etxid in utx:
                    # When a transaction is goes from 0 to 1 confirmation, bitcoind seems to reset its time and position in the listtransactions list :(
                    status_item = utx[etxid][0]
                    # NOTE: the row may have changed since the start of the function, so don't try to cache it from above
                    row = self.transactions_table.row(status_item)
                    unixtime = t['time']

                    self.transactions_table.move_row(row, 0)
                    self.transactions_table.update_transaction_time(row, unixtime)
                    continue

                status_item = self.transactions_table.add_transaction_entry(t)
                if 'confirmations' not in t: continue
                category = t['category']
                confirms = t['confirmations']
                if self.confirmation_stage(category, confirms) < 0x100:
                    self.unconfirmed_tx.insert(0, (etxid, status_item) )
                    debuglog += ["New unconfirmed tx: %s" % (etxid,)]
            self.last_tx = transactions[-1]['txid']

        # Finally, fetch individual tx info for any old unconfirmed tx
        while len(utx):
            etxid, data = utx.items()[0]
            status_item, transactions = data
            txid = etxid[:etxid.index('/')]
            if transactions is None:
                debuglog += ["Specially fetching unconfirmed tx: %s" % (etxid,)]
                transactions = self.core.get_transaction(txid)
            for t in transactions:
                etxid = self.__etxid(t)
                if etxid in utx:
                    category = t['category']
                    confirms = t['confirmations']
                    txdone = True
                    status_item = utx[etxid][0]
                    # NOTE: the row may have changed since the start of the function, so don't try to cache it from above
                    row = self.transactions_table.row(status_item)
                    if category == 'orphan':
                        debuglog += ["Tx %s (row %d) has been orphaned" % (etxid, row, confirms)]
                        self.transactions_table.removeRow(row)
                    else:
                        debuglog += ["Tx %s (row %d) has %d confirms" % (etxid, row, confirms)]
                        if category in ('generate', 'immature'):
                            status_item.category = category
                        elif hasattr(status_item, 'category'):
                            del status_item.category
                        self.transactions_table.update_confirmation(row, confirms, adjustment=False)
                        if self.confirmation_stage(category, confirms) < 0x100:
                            txdone = False
                    del utx[etxid]
                    if txdone:
                        for i in xrange(len(self.unconfirmed_tx)):
                            if self.unconfirmed_tx[i][0] == etxid:
                                self.unconfirmed_tx[i:i+1] = ()
                                break

        if SpesmiloSettings.debugMode:
            self._refresh_transactions_debug += [debuglog]

    def refresh_balance(self):
        self.balance = self.core.balance()
        self.refresh_balance_label()

    def refresh_balance_label(self):
        bltext = self.tr('Balance: %s') % (humanAmount(self.balance, wantTLA=True),)
        self.balance_label.setText(bltext)
        if hasattr(self, 'tray') and self.tray:
            self.tray.setToolTip(bltext)

    def create_actions(self):
        self.send_act = QAction(icon('go-next'), self.tr('Send'),
            self, toolTip=self.tr('Send bitcoins to another person'),
            triggered=self.new_send_dialog)
        self.newaddy_act = QAction(icon('document-new'),
            self.tr('New address'), self,
            toolTip=self.tr('Create new address for accepting bitcoins'),
            triggered=self.new_address)
        self.copyaddy_act = QAction(icon('copy-bitcoin-address', 'klipper', 'tool_clipboard', 'edit-copy', 'icons/edit-copy.png'),
            self.tr('Copy address'),
            self, toolTip=self.tr('Copy address to clipboard'),
            triggered=self.copy_address)
        self.settings_act = QAction(icon('configure', 'icons/preferences-system.png'),
            self.tr('Settings'),
            self, toolTip=self.tr('Configure Spesmilo'),
            triggered=self.open_settings)

    def new_send_dialog(self):
        if self.parent() is not None:
            send_dialog = send.SendDialog(self.core, self.parent())
        else:
            send_dialog = send.SendDialog(self.core, self)

    def new_address(self):
        self.addy.setText(self.core.new_address())

    def copy_address(self):
        self.clipboard.setText(self.addy.text())

    def open_settings(self):
        if hasattr(self, 'settingsdlg'):
            self.settingsdlg.show()
            self.settingsdlg.setFocus()
        else:
            import settings
            self.settingsdlg = settings.SettingsDialog(self)

if __name__ == '__main__':
    import os
    import sys
    import core_interface
    from settings import SpesmiloSettings
    os.system('/home/genjix/src/bitcoin/bitcoind')
    app = QApplication(sys.argv)
    SpesmiloSettings.loadTranslator()
    uri = SpesmiloSettings.getEffectiveURI()
    core = core_interface.CoreInterface(uri)
    clipboard = qApp.clipboard()
    cashier = Cashier(core, clipboard)
    cashier.show()
    sys.exit(app.exec_())
