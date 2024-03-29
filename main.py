#!/usr/bin/python
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

import socket

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtNetwork import *
import core_interface
import cashier
import send
from settings import SpesmiloSettings, SettingsDialog, icon, quietPopen

def receive_uri(w, uri):
    import send
    sw = send.SendDialog(w.core, w.parent(), uri=uri)
    sw.setFocus()

def _startup(rootwindow, *args, **kwargs):
    if SpesmiloSettings.useInternalCore():
        import os
        user, passwd, port = SpesmiloSettings.getInternalCoreAuth()
        cmd = ('bitcoind', '-rpcuser=%s' % (user,), '-rpcpassword=%s' % (passwd,), '-rpcallowip=127.0.0.1', '-rpcport=%d' % (port,))
        if len(args):
            options = args[0]
            cmd += options.bitcoind
        quietPopen(cmd)
        import ipc
        ipcsrv = ipc.ipc_handler('Bitcoin')
        ipcsrv.have_uri.connect(lambda x: receive_uri(rootwindow, x), Qt.QueuedConnection)
        ipcsrv.start()
        rootwindow.ipcsrv = ipcsrv
    rootwindow.start(*args, **kwargs)

class ConnectingDialog(QDialog):
    def __init__(self, parent):
        super(ConnectingDialog, self).__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(QLabel(self.tr('Connecting...')))
        progressbar = QProgressBar()
        progressbar.setMinimum(0)
        progressbar.setMaximum(0)
        main_layout.addWidget(progressbar)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cfgbtn = QPushButton(self.tr('&Configure'))
        cfgbtn.clicked.connect(self.config)
        self.cfgbtn = cfgbtn
        button_layout.addWidget(cfgbtn)
        abortbtn = QPushButton(self.tr('&Abort'))
        abortbtn.clicked.connect(self.stop)
        button_layout.addWidget(abortbtn)
        main_layout.addLayout(button_layout)

        if parent is not None:
            self.setWindowIcon(parent.bitcoin_icon)
        self.setWindowTitle(self.tr('Connecting...'))
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.show()

    def config(self):
        self.hide()
        rootwindow = self.parent()
        rootwindow.config()

    def stop(self):
        self.hide()
        self.parent().stop()

    def closeEvent(self, event):
        self.hide()
        event.ignore()

class TrayIcon(QSystemTrayIcon):
    def __init__(self, core, parent):
        super(TrayIcon, self).__init__(parent)
        self.core = core
        self.current_window = None
        self.create_menu()
        self.setIcon(self.parent().bitcoin_icon)
        self.activated.connect(self.toggle_window)
        self.show()
    
    def create_menu(self):
        tray_menu = QMenu()
        self.cash_act = QAction(self.tr('&Cashier'), self)
        self.cash_act.triggered.connect(self.show_cashier)
        self.cash_act.setDisabled(True)
        tray_menu.addAction(self.cash_act)
        self.send_act = QAction(self.tr('&Send funds'), self)
        self.send_act.triggered.connect(self.show_send)
        self.send_act.setDisabled(True)
        tray_menu.addAction(self.send_act)
        tray_menu.addSeparator()
        quit_act = QAction(self.tr('&Quit'), self)
        quit_act.triggered.connect(self.quit)
        tray_menu.addAction(quit_act)
        self.setContextMenu(tray_menu)

    def delete_window(self):
        if self.current_window is not None:
            self.current_window.deleteLater()

    def create_connecting(self):
        self.delete_window()
        self.current_window = ConnectingDialog(self.parent())

    def create_cashier(self):
        if hasattr(self.current_window, 'cfgbtn'):
            self.current_window.cfgbtn.setDisabled(True)
        self.cash_act.setDisabled(False)
        self.send_act.setDisabled(False)
        self.delete_window()
        self.current_window = cashier.Cashier(self.core, qApp.clipboard(),
                                              self.parent(),
                                              tray=self)
        self.show_cashier()

    def show_cashier(self):
        self.current_window.show()

    def toggle_window(self, reason):
        if reason == self.Trigger:
            if self.current_window is not None:
                if self.current_window.isVisible():
                    self.current_window.hide()
                else:
                    self.current_window.show()

    def show_send(self):
        send.SendDialog(self.core, self.parent())

    def quit(self):
        self.parent().stop()

class RootWindow(QMainWindow):
    CLIENT_NONE = 0
    CLIENT_CONNECTING = 1
    CLIENT_DOWNLOADING = 2
    CLIENT_RUNNING = 3

    def __init__(self):
        super(RootWindow, self).__init__()
        self.app = qApp
        
        self.state = self.CLIENT_NONE
    
    def setup(self, options, args):
        icon._default = icon(options.icon, *icon._defaultSearch)
        self.bitcoin_icon = icon()
        self.caption = options.caption
        self.core = None

    def start(self, options = None, args = None):
        self.state = self.CLIENT_NONE
        self.uri = SpesmiloSettings.getEffectiveURI()
        self.core = core_interface.CoreInterface(self.uri)
        self.core.tr = lambda s: self.app.translate('CoreInterface', s)
        if hasattr(self, 'tray'):
            self.tray.hide()
            del self.tray
        self.tray = TrayIcon(self.core, self)

        refresh_state_timer = QTimer(self)
        self.refresh_state_timer = refresh_state_timer
        refresh_state_timer.timeout.connect(self.refresh_state)
        refresh_state_timer.start(1000)
        self.refresh_state()

    def config(self):
        self.stop(doQuit=False)
        sd = SettingsDialog(self)
        self.tray.current_window = sd
        sd.accepted.connect(lambda: _startup(self))
        sd.rejected.connect(lambda: qApp.quit())

    def refresh_state(self):
        is_init = False
        if self.state == self.CLIENT_NONE:
            self.state = self.CLIENT_CONNECTING
            try:
                is_init = self.core.is_initialised()
            except:
                pass
            # show initialising dialog
            self.tray.create_connecting()
        elif self.state == self.CLIENT_CONNECTING:
            try:
                is_init = self.core.is_initialised()
            except Exception, e:
                import traceback
                traceback.print_exc()
                error = QMessageBox(QMessageBox.Critical, 
                                    self.tr('Error connecting'),
                                    self.tr(str(e)))
                error.exec_()
                self.config()
        if is_init:
            # some voodoo here checking whether we have blocks
            self.state = self.CLIENT_RUNNING
            self.tray.create_cashier()

    def closeEvent(self, event):
        super(RootWindow, self).closeEvent(event)
        self.stop()

    def stop(self, doQuit = True):
        try:
            self.refresh_state_timer.stop()
            if SpesmiloSettings.useInternalCore() and self.core:
                # Keep looping until connected so we can issue the stop command
                while True:
                    try:
                        self.core.stop()
                    except core_interface.JSONRPCException:
                        pass
                    except IOError:
                        break
                    except socket.error:
                        break
                    except:
                        raise
                    else:
                        break
        # Re-proprogate exception & trigger app exit so we can break out
        except:
            raise
        finally:
            self.core = None
            if hasattr(self, 'ipcsrv'):
                try:
                    self.ipcsrv.stop()
                except:
                    pass
            if doQuit:
                qApp.quit()

def _RunCLI():
    import code, threading
    try:
        raise None
    except:
        frame = sys.exc_info()[2].tb_frame.f_back
    namespace = frame.f_globals.copy()
    namespace.update(frame.f_locals)

    def CLI():
        code.interact(banner=None, local=namespace)
    threading.Timer(0, CLI).start()

if __name__ == '__main__':
    def vararg_callback(option, opt_str, value, parser):
        assert value is None
        value = []

        for arg in parser.rargs:
            if arg == '--':
                break
            value.append(arg)

        del parser.rargs[:len(value) + 1]
        setattr(parser.values, option.dest, tuple(value))

    import optparse
    import os
    import sys

    if hasattr(sys, 'frozen') and sys.frozen == "windows_exe":
        sys.stderr = sys.stdout

    app = QApplication(sys.argv)
    font = app.font()
    if not QFontMetrics(font).inFont(0xe9d9):
        font.setFamily(font.family() + ', tonal, Tonal (Luxi Mono)')
        app.setFont(font)
    SpesmiloSettings.loadTranslator()

    argp = optparse.OptionParser(usage=app.tr('Usage: %prog [options] [URI]'))
    #argp.add_option('URI', nargs='?', help=app.tr('a bitcoin: URI to open a send dialog to'))
    argp.add_option('--caption', dest='caption', nargs=1, default=None,
                    help=app.tr('Use this caption for the cashier window'))
    #argp.add_option('--cashier', dest='cashier', action='store_true', default=False,
    #                help=app.tr('Opens a view of your transactions'))
    #argp.add_option('--config', dest='config', nargs=1,
    #                help=app.tr('Use an alternative config'))
    argp.add_option('--debug', dest='debug', action='store_true', default=False,
                    help=app.tr('Opens an interactive Python prompt, and enables infinite in-RAM logging'))
    argp.add_option('--icon', dest='icon', nargs=1, default=None,
                    help=app.tr('Use this window icon'))
    argp.add_option('--send', dest='send', action='store_true', default=False,
                    help=app.tr('Opens a dialog to send funds'))
    argp.add_option('--bitcoind', dest='bitcoind', action='callback', callback=vararg_callback, default=(),
                    help=app.tr('Pass remaining arguments to bitcoind (internal core only)'))

    args = app.arguments()
    # Workaround PySide/Windows bug
    if sys.argv[0] in args:
        i = args.index(sys.argv[0])
        if i:
            args[0:i] = ()
    # Workaround KDE bug
    if '-icon' in args:
        args[args.index('-icon')] = '--icon'
    (options, args) = argp.parse_args(args)
    args[0:1] = ()

    if args or options.send:
        if SpesmiloSettings.useInternalCore():
            try:
                import ipc
                ipc.ipc_send('Bitcoin', args[0] if args else 'bitcoin:')
                exit(0)
            except Exception:
                pass
        rootwindow = send.SendDialog(autostart=False)
    else:
        app.setQuitOnLastWindowClosed(False)
        rootwindow = RootWindow()
        rootwindow.setup(options, args)

    if SpesmiloSettings.isConfigured():
        _startup(rootwindow, options, args)
    else:
        sd = SettingsDialog(rootwindow)
        sd.accepted.connect(lambda: _startup(rootwindow, options, args))
        sd.rejected.connect(lambda: qApp.quit())
    if options.debug:
        SpesmiloSettings.debugMode = True
        _RunCLI()
    sys.exit(app.exec_())
