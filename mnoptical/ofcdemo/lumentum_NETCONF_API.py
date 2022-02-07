""" Lumemtum ROADM 20 Control

Author:   Jiakai Yu (jiakaiyu@email.arizona.edu)
Created:  2019/03/09
Version:  2.0

Last modified by Jiakai: 2020/08/11
"""




import xmltodict
import ncclient
from ncclient import manager
from ncclient.xml_ import to_ele


USERNAME = "superuser"
PASSWORD = "Sup%9User"

class Lumentum(object):

    def __init__(self, IP_addr, usrname=USERNAME, psswd=PASSWORD):
        self.m = None
        try:
            self.m = manager.connect(host=IP_addr, port=830, username=usrname, password=psswd, hostkey_verify=False)
        except Exception as e:
            print('connection failed')

    def __del__(self):
        if self.m:
            self.m.close_session()


    def edfa_status(self):

        filter_edfa = '''
        <filter>
          <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa" xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
          </edfas>
        </filter>
        '''

        try:
            edfa= self.m.get(filter_edfa)
            edfa_details=xmltodict.parse(edfa.data_xml)

            control_mode1 = str(edfa_details['data']['edfas']['edfa'][0]['config']['lotee:control-mode'])
            gain_mode1 = str(edfa_details['data']['edfas']['edfa'][0]['config']['lotee:gain-switch-mode'])
            target_gain1 = str(edfa_details['data']['edfas']['edfa'][0]['config']['lotee:target-gain'])
            target_power1 = str(edfa_details['data']['edfas']['edfa'][0]['config']['lotee:target-power'])
            input_power1 = str(edfa_details['data']['edfas']['edfa'][0]['state']['input-power'])
            output_power1 =str( edfa_details['data']['edfas']['edfa'][0]['state']['output-power'])
            voa_input_power1 = str(edfa_details['data']['edfas']['edfa'][0]['state']['voas']['voa']['voa-input-power'])
            voa_output_power1 = str(edfa_details['data']['edfas']['edfa'][0]['state']['voas']['voa']['voa-input-power'])
            voa_attenuation1 = str(edfa_details['data']['edfas']['edfa'][0]['state']['voas']['voa']['voa-attentuation'])
            status1 = str(edfa_details['data']['edfas']['edfa'][0]['config']['lotee:maintenance-state'])

            control_mode2 =str(edfa_details['data']['edfas']['edfa'][1]['config']['lotee:control-mode'])
            gain_mode2 = str(edfa_details['data']['edfas']['edfa'][1]['config']['lotee:gain-switch-mode'])
            target_gain2 = str(edfa_details['data']['edfas']['edfa'][1]['config']['lotee:target-gain'])
            target_power2 = str(edfa_details['data']['edfas']['edfa'][1]['config']['lotee:target-power'])
            input_power2 = str(edfa_details['data']['edfas']['edfa'][1]['state']['input-power'])
            output_power2 = str(edfa_details['data']['edfas']['edfa'][1]['state']['output-power'])
            voa_input_power2 = str(edfa_details['data']['edfas']['edfa'][1]['state']['voas']['voa']['voa-input-power'])
            voa_output_power2 = str(edfa_details['data']['edfas']['edfa'][1]['state']['voas']['voa']['voa-input-power'])
            voa_attenuation2 = str(edfa_details['data']['edfas']['edfa'][1]['state']['voas']['voa']['voa-attentuation'])
            status2 = str(edfa_details['data']['edfas']['edfa'][1]['config']['lotee:maintenance-state'])

            return {'PRE-AMP':
                        {'control mode': control_mode1,
                         'gain mode': gain_mode1,
                         'target gain': target_gain1,
                         'target power': target_power1,
                         'input power': input_power1,
                         'output power': output_power1,
                         'voa input power': voa_input_power1,
                         'voa output power': voa_output_power1,
                         'voa attenuation': voa_attenuation1,
                         'status': status1},

                    'BOOSTER':
                        {'control mode': control_mode2,
                         'gain mode': gain_mode2,
                         'target gain': target_gain2,
                         'target power': target_power2,
                         'input power': input_power2,
                         'output power': output_power2,
                         'voa input power': voa_input_power2,
                         'voa output power': voa_output_power2,
                         'voa attenuation': voa_attenuation2,
                         'status': status2},
                    }

        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return None


    def ALS_disable(self, module):

        service = '''<disable-alsxmlns="http://www.lumentum.com/lumentum-ote-edfa"><dn>ne=1;chassis=1;card=1;edfa=%sdn><timeout-period>600</timeout-period></disable-als>'''%(module)
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
        #self.module = module
        #self.ctrl_mode = ctrl_mode
        #self.status = status
        #self.gain_mode = gain_mode
        #self.target_power = target_power
        #self.target_gain = target_gain
        #self.tilt = tilt
        #self.ALS = ALS

        rpc_reply = 0
        self.edfa_data = self.edfa_status()
        print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        print(self.edfa_data)

        #######out-of-service#######
        service0 = '''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa" xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa=%s</dn>
                <config>
                  <maintenance-state>out-of-service</maintenance-state>
                </config>
              </edfa>
            </edfas>
          </xc:config>
              '''%(module)

        #######configure#######
        service1 = '''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa" 
            xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa=%s</dn>
                <config>
                  <maintenance-state>%s</maintenance-state>
                  <control-mode>%s</control-mode>
                  <gain-switch-mode>%s</gain-switch-mode>
                  <target-gain>%s</target-gain>
                  <target-power>%s</target-power>
                  <target-gain-tilt>%s</target-gain-tilt>
                </config>
              </edfa>
            </edfas>
          </xc:config>
              '''%(module, status, ctrl_mode, gain_mode, target_gain, target_power, tilt)

        #######in-service#######
        service2 = '''
          <xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <edfas xmlns="http://www.lumentum.com/lumentum-ote-edfa" xmlns:lotee="http://www.lumentum.com/lumentum-ote-edfa">
              <edfa>
                <dn>ne=1;chassis=1;card=1;edfa=%s</dn>
                <config>
                  <maintenance-state>in-service</maintenance-state>
                </config>
              </edfa>
            </edfas>
          </xc:config>
              '''%(module)

        edfa_module = 'pre-amp' if int(module)==0 else 'booster'
        if status=='out-of-service':
            rpc_reply = self.m.edit_config(target='running', config=service0)

        elif self.edfa_data[edfa_module]['status'] == 'out-of-service':
            rpc_reply = self.m.edit_config(target='running', config=service1)

        elif status=='in-service':
            if ctrl_mode == self.edfa_data[edfa_module]['control mode'] and gain_mode == self.edfa_data[edfa_module]['gain mode']:
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


    class WSSConnection(object):

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
                    connection_detail['config']['input-port-reference'].split('port=')[1],
                    connection_detail['config']['output-port-reference'].split('port=')[1],
                    connection_detail['config']['start-freq'],
                    connection_detail['config']['end-freq'],
                    connection_detail['config']['attenuation'],
                    connection_detail['config']['custom-name'],
                    connection_detail['state']['input-channel-attributes']['power'],
                    connection_detail['state']['output-channel-attributes']['power'],
                    connection_detail['dn'].split(';')[0].split('=')[1],
                    connection_detail['dn'].split(';')[1].split('=')[1],
                    connection_detail['dn'].split(';')[2].split('=')[1]
                ) for connection_detail in connection_details['data']['connections']['connection'] if connection_detail
            ]


    def wss_add_connections(self, connections):

        def gen_connection_xml(wss_connection):
            return '''<connection>
              <dn>ne=1;chassis=1;card=1;module=%s;connection=%s</dn>
              <config>
                <maintenance-state>%s</maintenance-state>
                <blocked>%s</blocked>
                <start-freq>%s</start-freq>
                <end-freq>%s</end-freq>
                <attenuation>%s</attenuation>
                <input-port-reference>ne=1;chassis=1;card=1;port=%s</input-port-reference>
                <output-port-reference>ne=1;chassis=1;card=1;port=%s</output-port-reference>
                <custom-name>%s</custom-name>
              </config> 
            </connection>''' % (
                wss_connection.module,
                wss_connection.connection_id,
                wss_connection.operation,
                wss_connection.blocked,
                wss_connection.start_freq,
                wss_connection.end_freq,
                wss_connection.attenuation,
                wss_connection.input_port,
                wss_connection.output_port,
                wss_connection.name
            )

        new_line = '\n'
        services = '''<xc:config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <connections xmlns="http://www.lumentum.com/lumentum-ote-connection" 
        xmlns:lotet="http://www.lumentum.com/lumentum-ote-connection">
            %s
        </connections>
        </xc:config>''' % new_line.join([gen_connection_xml(connection) for connection in connections])

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
                reply = self.m.dispatch(to_ele('''
                <remove-all-connections
                xmlns="http://www.lumentum.com/lumentum-ote-connection">
                <dn>ne=1;chassis=1;card=1;module=%s</dn>
                </remove-all-connections>
                ''' % module_id))
            else:
                reply = self.m.dispatch(to_ele('''
                <delete-connection xmlns="http://www.lumentum.com/lumentum-ote-connection">
                <dn>ne=1;chassis=1;card=1;module=%s;connection=%s</dn>
                </delete-connection>
                ''' % (module_id, connection_id)))
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
        connections = Lumentum.WSSConnectionStatus.from_connection_details(connection_details) if connection_details else None
        return connections


    @staticmethod
    def gen_dwdm_connections(module, input_port, output_port, loss=0.0, channel_spacing=50.0, channel_width=50.0):
        """
        :param module:
        :param input_port:
        :param output_port:
        :param channel_spacing: in GHz
        :param channel_width: in GHz
        :return:
        """
        connections = []
        half_channel_width = channel_width / 2.0  # in GHz
        start_center_frequency = 191350.0  # in GHz
        for i in range(96):
            center_frequency = start_center_frequency + i * channel_spacing
            connection = Lumentum.WSSConnection(
                module,
                str(i + 1),
                'in-service',
                'false',
                input_port,
                output_port,
                str(center_frequency - half_channel_width),
                str(center_frequency + half_channel_width),
                loss,
                'CH' + str(i + 1)
            )
            connections.append(connection)
        return connections


#####################################################################################

class Lumentum_NETCONF(object):

    def _ConfigWSS(self, node_ip, status, conn_id, module_id, input_port=None, output_port=None, start_freq=None, end_freq=None, attenuation=None, block=None, name=None):
        print ('============ConfigWSS_Setup_Start==============')
        
        try:
            node = Lumentum(str(node_ip), str(USERNAME), str(PASSWORD))
            if status=='del':
                rpc_reply = node.wss_delete_connection(str(module_id), str(conn_id))
            elif conn_id == 'all':
                connections = node.gen_dwdm_connections(str(module_id), str(input_port),str(output_port), loss= float(attenuation))
                rpc_reply = node.wss_add_connections(connections)
            else:
                connection = Lumentum.WSSConnection(str(module_id), str(conn_id), str(status), str(block),
                                                    str(input_port), str(output_port), str(start_freq),
                                                    str(end_freq), str(attenuation), str(name))

                rpc_reply = node.wss_add_connections([connection])
            return rpc_reply
        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return False


    def _WSSMonitor(self,node_ip):
        
        mux_info = {}
        demux_info = {}
        try:
            node = Lumentum(str(node_ip), str(USERNAME), str(PASSWORD))
            connections = node.wss_get_connections()
            if connections:
                l = len(connections)
                for i in range(0,l):
                    id = connections[i].connection_id
                    module = connections[i].module
                    name = connections[i].name
                    status = connections[i].operation
                    start_freq = connections[i].start_freq
                    end_freq = connections[i].end_freq
                    attenuation = connections[i].attenuation
                    block = connections[i].blocked
                    input_port = connections[i].input_port
                    output_port = connections[i].output_port
                    input_power = connections[i].input_power
                    output_power = connections[i].output_power
                    if module == '1':
                        mux_info[id] = {'name':name, 'blocked':block, 'status':status,
                                             'start frequency':start_freq, 'end frequency': end_freq,
                                             'input port': input_port, 'output port': output_port,
                                             'input power': input_power, 'output power': output_power,
                                             'attenuation':attenuation }
                    if module == '2':
                        demux_info[id] = {'name':name, 'blocked':block, 'status':status,
                                             'start frequency':start_freq, 'end frequency': end_freq,
                                             'input port': input_port, 'output port': output_port,
                                             'input power': input_power, 'output power': output_power,
                                             'attenuation':attenuation }

            wss_info = {'MUX': mux_info, 'DEMUX': demux_info}
            return  wss_info

        except Exception as e:
            print("Encountered the following RPC error!")
            print(e)
            return False
