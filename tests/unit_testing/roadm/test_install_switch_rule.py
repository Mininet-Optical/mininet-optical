import topo.ofc_demo as OFCDemo
from tests.ofc.failure_recovery.switching_tuples import SwitchTuples as st
import numpy as np


def install_switch_rules_roadm1_after_transmit(r1):
    """
    Expected outcome: ROADM1 will trigger a switch function after the
    installation of rules. ROADMs 2 & 3 should complain about not
    being able to find a rule.
    :return:
    """
    proc = st()
    proc.switch_main()
    for pr in proc.roadm1:
        r1.install_switch_rule(**pr)


def install_switch_rules_roadm2_after_transmit(r2):
    """
    Expected outcome: ROADM1 will complain of not being able to
    find switching rules for any of the channels. The installation
    of rules into ROADM2 should not trigger the switching function.
    :return:
    """
    proc = st()
    proc.switch_main()
    for pr in proc.roadm2:
        r2.install_switch_rule(**pr)


def install_switch_rules_after_transmit(r1, r2, r3):
    """
    Expected outcome: All transmissions will be successful
    :return:
    """
    proc = st()
    proc.switch_main()
    for pr in proc.roadm1:
        r1.install_switch_rule(**pr)
    for pr in proc.roadm2:
        r2.install_switch_rule(**pr)
    for pr in proc.roadm3:
        r3.install_switch_rule(**pr)


if __name__ == '__main__':
    """
    Expected outome: only ROADM1 complains about being unable to
    find switch rules. The other ROADMs shouldn't even know
    there is a transmission taking place in the network.
    :return:
    """
    net = OFCDemo.build()

    n = net.name_to_node
    lt1, lt2, lt3 = [n['lt%d' % i] for i in (1, 2, 3)]
    roadm1, roadm2, roadm3 = [n['roadm%d' % i] for i in (1, 2, 3)]

    # Install switch rules into the ROADM nodes
    channels1 = list(np.arange(1, 11, 1))
    channels2 = list(np.arange(11, 21, 1))
    channels3 = list(np.arange(21, 31, 1))

    rw = channels1 + channels2 + channels3

    # Set resources to use and initiate transmission
    resources = {'transceiver': lt1.name_to_transceivers['t1'],
                 'required_wavelengths': rw}
    net.transmit(lt1, roadm1, resources=resources)

    # install_switch_rules_roadm1_after_transmit(roadm1)
    install_switch_rules_roadm2_after_transmit(roadm2)
    # install_switch_rules_after_transmit(roadm1, roadm2, roadm3)
