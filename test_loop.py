from network import Network
from link import Span
from pprint import pprint

net = Network()


cities = ['berlin', 'bremen', 'dortmund', 'dusseldorf',
          'essen', 'frankfurt', 'hamburg', 'hannover',
          'koln', 'leipzig', 'munchen', 'nurnberg',
          'stuttgart', 'ulm']

transceivers = [('t1', 'C')]
line_terminals = [net.add_lt('lt_%s' % s, transceivers=transceivers) for s in cities]
name_to_lt = {lt.name: lt for lt in line_terminals}

roadms = [net.add_roadm('roadm_%s' % s) for s in cities]
name_to_roadm = {roadm.name: roadm for roadm in roadms}

for lt, roadm in zip(line_terminals, roadms):
    link = net.add_link(lt, roadm)
    link.add_span(Span('SMF', 0.01), amplifier=None)
    bi_link = net.add_link(roadm, lt)
    bi_link.add_span(Span('SMF', 0.01), amplifier=None)


