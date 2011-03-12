import jsonrpc
from jsonrpc.proxy import JSONRPCException

class CoreInterface:
    def __init__(self, uri):
        self.access = jsonrpc.ServiceProxy(uri)
        self.rpcversion = 0
        try:
            if self.access.bitcoin.__getattr__('1').getinfo()['rpcversion'] != 1:
                raise JSONRPCException()
            # If we get this far, RPCv1 is supported
            self.rpcversion = 1
            self.access = self.access.bitcoin.__getattr__('1')
        except JSONRPCException:
            pass

    def _fromAmount(self, n):
        if self.rpcversion == 0:
            return int(n * 100000000)
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
