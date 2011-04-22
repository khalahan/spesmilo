# -*- coding: utf-8 -*-
import sys
from PySide.QtCore import *

class ipc_handler(QThread):
    have_uri = Signal(object)

    def __init__(self, addr, *args, **kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.setTerminationEnabled(True)
        if sys.platform == 'win32':
            addr = r'\\.\pipe\%s' % (addr,)
        self._addr = addr

    def run(self):
        import multiprocessing.connection

        srv = multiprocessing.connection.Listener(self._addr)
        self._srv = srv

        while True:
            c = srv.accept()
            arg = c.recv_bytes()
            c.close()
            self.have_uri.emit(arg)

    def stop(self):
        self.terminate()

def ipc_send(addr, arg):
    import multiprocessing.connection

    cln = multiprocessing.connection.Client(addr)
    cln.send_bytes(arg)
