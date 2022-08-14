""" Lumentum ROADM 20 Control API

Author:   Jiakai Yu (jiakaiyu@email.arizona.edu)
Created:  2019/03/09
Version:  2.1

Last modified by Jiakai: 2020/08/11
Cleaned up slightly by BL: 2022
"""

import atexit
import xmltodict as x2d
import ncclient
from ncclient import manager
from ncclient.xml_ import to_ele

from traceback import print_exception, print_tb, print_exc
from pprint import pprint

class xmltodict:
    @staticmethod
    def parse( xml, **kwargs):
        kwargs.update(process_namespaces=True, namespaces={
            'urn:ietf:params:xml:ns:netconf:base:1.0': None,
            'http://www.lumentum.com/lumentum-ote-connection': None} )
        return x2d.parse( xml, **kwargs)

USERNAME = "superuser"
PASSWORD = "Sup%9User"

class Lumentum:

    connections = {}

    def __init__(self, IP_addr, username=USERNAME, password=PASSWORD):
        self.IP_addr = IP_addr
        self.m = Lumentum.connections.get(IP_addr)
        if self.m:
            return
        port = 830
        if ':' in IP_addr:
            ip, port = IP_addr.split(':')
            port = int(port)
        try:
            print("CONNECTING TO", ip, port)
            self.m = manager.connect(
                host=ip, port=port, username=username, password=password,
                hostkey_verify=False)
            self.connections[IP_addr] = self.m
        except Exception as e:
            print('connection failed')
        atexit.register(self.cleanup)

    def cleanup(self):
        if self.m:
            self.m.close_session()
        if self.IP_addr in Lumentum.connections:
            del Lumentum.connections[self.IP_addr]

    @staticmethod
    def lookup(node, path):
        """Look up path in a dict tree and return the result
           note for /some/0/path '0' is looked up as an int"""
        print("LOOKING UP", node, path)
        for entry in path.split('/'):
            if entry[0] in '0123455789':
                try:
                    entry = int(entry)
                except:
                    pass
                node = node[entry]
        return node

    @staticmethod
    def lookupstr(node, path):
        "Look up path and node and return it as a string"
        return str(Lumentum.lookup(node, path))

    def edfa_status(self):
        "Return status of Boost and Preamp EDFAs"
        filter_edfa = '''
        <filter>
          <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa"
                 xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
          </edfas>
        </filter>
        '''
        try:
            edfa = self.m.get(filter_edfa)
            edfa_details = xmltodict.parse(edfa.data_xml)
            result = {}
            for field, num in (('PRE-AMP', 0), ('BOOSTER'), 1):
                edfa = self.lookup(edfa, f'data/edfas/edfa/{num}')
                def E(path): return self.lookupstr(edfa, path)
                entry = {
                    'control mode': E(f'config/lotee:control-mode'),
                    'gain mode':  E(f'config/lotee:gain-switch-mode'),
                    'target gain': E(f'config/lotee:target-gain'),
                    'target power': E(f'config/lotee:target-power'),
                    'input power': E(f'state/input-power'),
                    'output': E(f'state/output-power'),
                    'status': E(f'config/lotee:maintenance-state')}
                # Add VOA info for booster amp
                if num == 1:
                    entry.update({
                        'voa input power': E(f'state/voas/voa/voa-input-power'),
                        'voa output power': E(f'state/voas/voa/voa-input-power'),
                        'voa attenuation': E(f'state/voas/voa/voa-attentuation')})
                result[field] = entry
            return result

        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return None


    def ALS_disable(self, module):

        service = ('<disable-als>xmlns="http://www.lumentum.com/lumentum-ote-edfa">'
                   f'<dn>ne=1;chassis=1;card=1;edfa={module}</dn><timeout-period>600'
                   '</timeout-period></disable-als>')
        try:
            reply = self.m.dispatch(to_ele(service))
            return reply
        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return 0


    def edfa_config(self,
                     module,
                     ctrl_mode,
                     status,
                     gain_mode,
                     target_power,
                     target_gain,
                     tilt,
                     ALS
                     ):
        rpc_reply = 0
        self.edfa_data = self.edfa_status()
        # print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        # print(self.edfa_data)

        ####### out-of-service #######
        service0 = f'''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa"
                   xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa={module}</dn>
                <config>
                  <maintenance-state>out-of-service</maintenance-state>
                </config>
              </edfa>
            </edfas>
          </xc:config>'''

        ####### configure #######
        service1 = f'''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa"
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa={module}</dn>
                <config>
                  <maintenance-state>{status}</maintenance-state>
                  <control-mode>{ctrl_mode}</control-mode>
                  <gain-switch-mode>{gain_mode}</gain-switch-mode>
                  <target-gain>{target_gain}</target-gain>
                  <target-power>{target_power}</target-power>
                  <target-gain-tilt>{tilt}</target-gain-tilt>
                </config>
              </edfa>
            </edfas>
          </xc:config>
        '''

        ####### in-service #######
        service2 = f'''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa"
                   xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa={module}</dn>
                <config>
                  <maintenance-state>in-service</maintenance-state>
                </config>
              </edfa>
            </edfas>
          </xc:config>
        '''

        edfa_module = 'pre-amp' if int(module) == 0 else 'booster'
        if status == 'out-of-service':
            rpc_reply = self.m.edit_config(target='running', config=service0)

        elif self.edfa_data[edfa_module]['status'] == 'out-of-service':
            rpc_reply = self.m.edit_config(target='running', config=service1)

        elif status=='in-service':
            if (ctrl_mode == self.edfa_data[edfa_module]['control mode']
                and gain_mode == self.edfa_data[edfa_module]['gain mode']):
                rpc_reply = self.m.edit_config(target='running', config=service1)
            else:
                rpc_reply0 = self.m.edit_config(target='running', config=service0)
                rpc_reply1 = self.m.edit_config(target='running', config=service1)
                rpc_reply_als = None
                if ALS:
                    rpc_reply_als = self.ALS_disable(module)
                if rpc_reply0 and rpc_reply1 and rpc_reply_als:
                    rpc_reply = 1
        return rpc_reply


    class WSSConnection:
        def __init__(self,
                     module,
                     connection_id,
                     operation,
                     blocked,
                     input_port,
                     output_port,
                     start_freq,
                     end_freq,
                     attenuation,
                     name
                     ):
            self.module = module
            self.connection_id = connection_id
            self.operation = operation
            self.blocked = blocked
            self.input_port = input_port
            self.output_port = output_port
            self.start_freq = start_freq
            self.end_freq = end_freq
            self.attenuation = attenuation
            self.name = name


    class WSSConnectionStatus(WSSConnection):
        def __init__(self,
                     module,
                     connection_id,
                     operation,
                     blocked,
                     input_port,
                     output_port,
                     start_freq,
                     end_freq,
                     attenuation,
                     name,
                     input_power,
                     output_power,
                     ne,
                     chassis,
                     card
                     ):
            super(Lumentum.WSSConnectionStatus, self).__init__(
                module,
                connection_id,
                operation,
                blocked,
                input_port,
                output_port,
                start_freq,
                end_freq,
                attenuation,
                name)
            self.input_power = input_power
            self.output_power = output_power
            self.ne = ne
            self.chassis = chassis
            self.card = card

        @classmethod
        def from_connection_details(cls, connection_details):
            return [
                cls(
                    connection_detail['dn'].split(';')[3].split('=')[1],
                    connection_detail['dn'].split(';')[4].split('=')[1],
                    connection_detail['config']['maintenance-state'],
                    connection_detail['config']['blocked'],
                    connection_detail['config']['input-port-reference'].split(
                        'port=')[1],
                    connection_detail['config']['output-port-reference'].split(
                        'port=')[1],
                    connection_detail['config']['start-freq'],
                    connection_detail['config']['end-freq'],
                    connection_detail['config']['attenuation'],
                    connection_detail['config']['custom-name'],
                    connection_detail['state']['input-channel-attributes']['power'],
                    connection_detail['state']['output-channel-attributes']['power'],
                    connection_detail['dn'].split(';')[0].split('=')[1],
                    connection_detail['dn'].split(';')[1].split('=')[1],
                    connection_detail['dn'].split(';')[2].split('=')[1]
                )
                for connection_detail in connection_details['data']['connections']['connection']
                if connection_detail
            ]


    def wss_add_connections(self, connections):

        def gen_connection_xml(wss_connection):
            w = wss_connection
            return f'''<connection>
              <dn>ne=1;chassis=1;card=1;module={w.module};connection={w.connection_id}</dn>
              <config>
                <maintenance-state>{w.operation}</maintenance-state>
                <blocked>{w.blocked}</blocked>
                <start-freq>{w.start_freq}</start-freq>
                <end-freq>{w.end_freq}</end-freq>
                <attenuation>{w.attenuation}</attenuation>
                <input-port-reference>ne=1;chassis=1;card=1;port={w.input_port}</input-port-reference>
                <output-port-reference>ne=1;chassis=1;card=1;port={w.output_port}</output-port-reference>
                <custom-name>{w.name}</custom-name>
              </config>
            </connection>'''

        conn_xml = '\n'.join(gen_connection_xml(c) for c in connections)
        services = f'''<xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <connections xmlns="http://www.lumentum.com/lumentum-ote-connection"
        xmlns:lotet="http://www.lumentum.com/lumentum-ote-connection">
            {conn_xml}
        </connections>
        </xc:config>'''

        try:
            reply = self.m.edit_config(target='running', config=services)
            if '<ok/>' in str(reply):
                print('Successfully Added Connections')
                return 1
            return 0
        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return 0


    def wss_delete_connection(self, module_id, connection_id):
        try:
            if connection_id == 'all':
                reply = self.m.dispatch(to_ele(f'''
                <remove-all-connections
                xmlns="http://www.lumentum.com/lumentum-ote-connection">
                <dn>ne=1;chassis=1;card=1;module={module_id}</dn>
                </remove-all-connections>
                '''))
            else:
                reply = self.m.dispatch(to_ele('''
                <delete-connection xmlns="http://www.lumentum.com/lumentum-ote-connection">
                <dn>ne=1;chassis=1;card=1;module={module_id};connection={connection_id}</dn>
                </delete-connection>
                '''))
            if '<ok/>' in str(reply):
                print('Successfully Deleted Connection')
                return 1
            return 0
        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return 0


    def wss_get_connections(self):
        command = '''
                <filter>
                  <connections xmlns="http://www.lumentum.com/lumentum-ote-connection">
                  </connections>
                </filter>
                '''
        try:
            conn = self.m.get(command)
            connection_details = xmltodict.parse(conn.data_xml)
            # print(connection_details['data']['connections']['connection'])
        except Exception as e:
            connection_details = None
            print("Encountered the following RPC error!")
            print(e)
        connections = None
        connections = (
            Lumentum.WSSConnectionStatus.from_connection_details(connection_details)
            if connection_details else None)
        return connections


    @staticmethod
    def freqRangeGHz(channel):
        "Return frequency range (startGHz, endGHz) for channel"
        half_channel_width = 25  # in GHz
        start_center_frequency = 191350.0  # in GHz
        center_frequency = start_center_frequency + (channel-1) * 50
        start_freq = str(center_frequency - half_channel_width)
        end_freq = str(center_frequency + half_channel_width)
        return start_freq, end_freq

    @staticmethod
    def gen_dwdm_connections(module, input_port, output_port, loss=0.0,
                             channel_spacing=50.0, channel_width=50.0):
        """
        :param module:
        :param input_port:
        :param output_port:
        :param channel_spacing: in GHz
        :param channel_width: in GHz
        :return:
        """
        connections = []
        for i in range(96):
            channel = i+1
            center_frequency = start_center_frequency + i * channel_spacing
            start_freq, end_freq = Lumentum.freqRangeGHz(channel)
            connection = Lumentum.WSSConnection(
                module,
                str(channel),
                'in-service',
                'false',
                input_port,
                output_port,
                str(start_freq),
                str(end_freq),
                loss,
                'CH' + str(channel)
            )
            connections.append(connection)
        return connections


#####################################################################################

class Lumentum_NETCONF:


    def _ConfigWSS(self, node_ip, status, conn_id, module_id, input_port=None,
                   output_port=None, start_freq=None, end_freq=None,
                   attenuation=None, block=None, name=None):
        print ('============ConfigWSS_Setup_Start==============', node_ip)

        try:
            node = Lumentum(node_ip,  str(USERNAME), str(PASSWORD))
            if status=='del':
                rpc_reply = node.wss_delete_connection(str(module_id), str(conn_id))
            elif conn_id == 'all':
                connections = node.gen_dwdm_connections(
                    str(module_id), str(input_port),str(output_port),
                    loss = float(attenuation))
                rpc_reply = node.wss_add_connections(connections)
            else:
                connection = Lumentum.WSSConnection(
                    str(module_id), str(conn_id), str(status), str(block),
                    str(input_port), str(output_port), str(start_freq),
                    str(end_freq), str(attenuation), str(name))

                rpc_reply = node.wss_add_connections([connection])
            return rpc_reply
        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return False

    @staticmethod
    def parseConnections(connections):
        "Return wss_info"
        mux_info = {}
        demux_info = {}
        if connections:
            l = len(connections)
            for i in range(0,l):
                c = connections[i]
                id, module = c.connection_id, c.module
                entry = {
                    'name':c.name, 'blocked':c.blocked, 'status':c.operation,
                    'start frequency':c.start_freq, 'end frequency':c.end_freq,
                    'input port':c.input_port, 'output port': c.output_port,
                    'input power':c.input_power, 'output power': c.output_power,
                    'attenuation':c.attenuation }
                if module == '1':
                    mux_info[id] = entry
                if module == '2':
                    demux_info[id] = entry
        wss_info = {'MUX': mux_info, 'DEMUX': demux_info}
        return wss_info

    def _WSSMonitor(self,node_ip):

        try:
            node = Lumentum(node_ip, USERNAME, PASSWORD)
            connections = node.wss_get_connections()
            return self.parseConnections(connections)

        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return False
