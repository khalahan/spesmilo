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

import jsonrpc
from jsonrpc.proxy import JSONRPCException

class CoreInterface:
    def __init__(self, uri):
        basea = jsonrpc.ServiceProxy(uri)
        self.rpcversion = 0
        for access in (basea.bitcoin.__getattr__('1'), basea.bitcoin.v1, basea):
            try:
                info = access.getinfo()
            except JSONRPCException:
                continue
            if not 'rpcversion' in info:
                info['rpcversion'] = 0
            if not info['rpcversion'] in (0, 1):
                continue
            self.rpcversion = info['rpcversion']
            self.access = access
            break

    def _fromAmount(self, n):
        if self.rpcversion == 0:
            return int(round(n * 100000000))
        return int(n)

    def transactions(self, *args):
        txl = self.access.listtransactions(*args)
        for tx in txl:
            for k in ('amount', 'fee'):
                if k in tx: tx[k] = self._fromAmount(tx[k])
        return txl

    def get_transaction(self, txid):
        # NOTE: returns a list like transactions, in case we both sent and received
        tx = self.access.gettransaction(txid)
        for detail in tx['details']:
            for k, v in tx.iteritems():
                if k == 'details': continue
                detail[k] = v
        return tx['details']

    def balance(self):
        b = self.access.getbalance()
        b = self._fromAmount(b)
        return b

    def stop(self):
        return self.access.stop()

    def validate_address(self, address):
        return self.access.validateaddress(address)['isvalid']

    def send(self, address, amount):
        if amount % 1:
            raise ValueError('Bitcoin does not support precision requested')
        if self.rpcversion == 0:
            if amount % 1000000 and self.access.getinfo()['version'] < 32100:
                raise ValueError('This server does not support precision requested')
            amount /= 100000000.
        return self.access.sendtoaddress(address, amount)

    def default_address(self):
        return self.access.getaccountaddress('')

    def new_address(self):
        return self.access.getnewaddress('')
    
    def is_initialised(self):
        info = self.access.getinfo()
        if 'isinitialized' in info:
            return info['isinitialized']
        # This only happens on older bitcoind which only respond when initialized...
        return True
