import numpy as np


class SwitchTuples:

    def __init__(self):
        self.roadm1 = []
        self.roadm2 = []
        self.roadm3 = []

    def switch_main(self):
        # Switching procedure: 1 - 2 - 3 & 1 - 3
        channels1 = list(np.arange(1, 11, 1))
        channels2 = list(np.arange(11, 21, 1))
        channels3 = list(np.arange(21, 31, 1))

        self.roadm1 = [{'rule_id': 1, 'in_port': 0, 'out_port': 102, 'signal_indices': channels1},  # switches to roadm3
                       {'rule_id': 2, 'in_port': 0, 'out_port': 101, 'signal_indices': channels2},  # switches to roadm2
                       {'rule_id': 3, 'in_port': 0, 'out_port': 101, 'signal_indices': channels3}]  # switches to roadm2

        self.roadm2 = [{'rule_id': 1, 'in_port': 1, 'out_port': 102, 'signal_indices': channels2},  # switches TO roadm3
                       {'rule_id': 2, 'in_port': 1, 'out_port': 102, 'signal_indices': channels3}]

        self.roadm3 = [{'rule_id': 1, 'in_port': 1, 'out_port': 100, 'signal_indices': channels1},  # FROM roadm1
                       {'rule_id': 2, 'in_port': 2, 'out_port': 100, 'signal_indices': channels2},  # FROM roadm2
                       {'rule_id': 3, 'in_port': 2, 'out_port': 100, 'signal_indices': channels3}]

    def switch_alt(self):
        channels1 = list(np.arange(1, 11, 1))
        channels2 = list(np.arange(11, 21, 1))
        channels3 = list(np.arange(21, 31, 1))
        self.roadm1 = [{'rule_id': 1, 'in_port': 0, 'out_port': 101, 'signal_indices': channels1},  # switches to roadm3
                       {'rule_id': 2, 'in_port': 0, 'out_port': 101, 'signal_indices': channels2},  # switches to roadm2
                       {'rule_id': 3, 'in_port': 0, 'out_port': 101, 'signal_indices': channels3}]  # switches to roadm2

        self.roadm2 = [{'rule_id': 1, 'in_port': 1, 'out_port': 102, 'signal_indices': channels1},
                       {'rule_id': 1, 'in_port': 1, 'out_port': 102, 'signal_indices': channels2},  # switches TO roadm3
                       {'rule_id': 2, 'in_port': 1, 'out_port': 102, 'signal_indices': channels3}]

        self.roadm3 = [{'rule_id': 1, 'in_port': 2, 'out_port': 100, 'signal_indices': channels1},  # FROM roadm1
                       {'rule_id': 2, 'in_port': 2, 'out_port': 100, 'signal_indices': channels2},  # FROM roadm2
                       {'rule_id': 3, 'in_port': 2, 'out_port': 100, 'signal_indices': channels3}]

