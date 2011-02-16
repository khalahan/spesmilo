import jsonrpc
from jsonrpc.proxy import JSONRPCException

class CoreInterface:
    def __init__(self, uri):
        self.access = jsonrpc.ServiceProxy(uri)

    def transactions(self):
        return self.access.listtransactions()

    def balance(self):
        return self.access.getbalance()

    def stop(self):
        return self.access.stop()

    def validate_address(self, address):
        return self.access.validateaddress(address)['isvalid']

    def send(self, address, amount):
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
