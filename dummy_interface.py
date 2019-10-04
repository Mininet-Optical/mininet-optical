class DummyInterface(object):

    """
    A Dummy Interface is aimed to provide a bridge between user/application
    commands and nodes configuration/operation functions.

    In principle, these will be replaced with appropriate protocol APIs such as
    OpenConfig, OpenROADM, TAPI, etc.
    """
    def __init__(self, name, node=None):
        self.name = name
        self.node = node


class OLTInterface(DummyInterface):
    """
    Enable access to the transceiver in an OLT
    """

    def __init__(self, name, node=None):
        DummyInterface.__init__(self, name, node)
        self.configs = ['update', 'delete']

    def configure_transceiver(self, transceiver_name, cmd=None, **kwargs):
        if cmd not in self.configs:
            raise ValueError("DummyInterface.OLTInterface.configure_transceiver: command does not exist!")
        if transceiver_name not in self.node.name_to_transceivers:
            raise ValueError("DummyInterface.OLTInterface.configure_transceiver: transceiver not found in OLT!")
        if cmd is 'update':
            self.node.update_transceiver(transceiver_name, kwargs)
        elif cmd is 'delete':
            self.node.delete_transceiver(transceiver_name)
