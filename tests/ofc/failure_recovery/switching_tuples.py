import numpy as np


class SwitchTuples:

    def __init__(self):
        self.roadm1 = []
        self.roadm2 = []
        self.roadm3 = []
        self.roadm4 = []
        self.roadm5 = []
        self.roadm6 = []

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

    def switch_full(self):
        channels1 = list(np.arange(1, 11, 1))
        channels2 = list(np.arange(11, 21, 1))
        channels3 = list(np.arange(21, 31, 1))
        channels4 = list(np.arange(31, 41, 1))
        channels5 = list(np.arange(51, 61, 1))

        # from line terminal to roadm2 and,
        # from roadm3 to line terminal
        self.roadm1 = [{'rule_id': 1, 'in_port': 0, 'out_port': 101, 'signal_indices': channels1 + channels2},
                       {'rule_id': 2, 'in_port': 2, 'out_port': 100, 'signal_indices': channels4}]

        # from roadm1 to roadm4 and,
        # from roadm3 to line terminal: {'rule_id': 2, 'in_port': 2, 'out_port': 100, 'signal_indices': channels3}
        # from roadm1 to roadm4 for transmission debugging purposes
        self.roadm2 = [{'rule_id': 1, 'in_port': 1, 'out_port': 103, 'signal_indices': channels1 + channels2},
                       {'rule_id': 2, 'in_port': 2, 'out_port': 103, 'signal_indices': channels3}]

        # from roadm5 to roadm2 and,
        # from roadm5 to roadm1
        self.roadm3 = [{'rule_id': 1, 'in_port': 3, 'out_port': 102, 'signal_indices': channels3},
                       {'rule_id': 2, 'in_port': 3, 'out_port': 101, 'signal_indices': channels4}]

        # from roadm2 to roadm5 and,
        # from roadm2 to roadm6 and,
        # from roadm5 to line terminal
        # from roadm2 to terminal for transmission debugging purposes
        self.roadm4 = [{'rule_id': 1, 'in_port': 1, 'out_port': 102, 'signal_indices': channels1},
                       {'rule_id': 2, 'in_port': 1, 'out_port': 103, 'signal_indices': channels2},
                       {'rule_id': 3, 'in_port': 2, 'out_port': 100, 'signal_indices': channels5},
                       {'rule_id': 4, 'in_port': 1, 'out_port': 102, 'signal_indices': channels3}]

        # from roadm4 to line terminal and,
        # from roadm6 to roadm3 and,
        # from roadm6 to roadm4
        self.roadm5 = [{'rule_id': 1, 'in_port': 2, 'out_port': 100, 'signal_indices': channels1},
                       {'rule_id': 2, 'in_port': 3, 'out_port': 101, 'signal_indices': channels3 + channels4},
                       {'rule_id': 3, 'in_port': 3, 'out_port': 102, 'signal_indices': channels5},
                       {'rule_id': 4, 'in_port': 2, 'out_port': 100, 'signal_indices': channels3}]

        # from roadm4 to line terminal and,
        # from line terminal to roadm 6
        self.roadm6 = [{'rule_id': 1, 'in_port': 1, 'out_port': 100, 'signal_indices': channels2},
                       {'rule_id': 2, 'in_port': 0, 'out_port': 102,
                        'signal_indices': channels3 + channels4 + channels5}]

    def recovery_link_r1_r2(self):
        channels1 = list(np.arange(1, 11, 1))
        channels2 = list(np.arange(11, 21, 1))

        self.roadm6 = [{'rule_id': 3, 'in_port': 2, 'out_port': 100, 'signal_indices': channels2}]

        self.roadm5 = [{'rule_id': 4, 'in_port': 1, 'out_port': 100, 'signal_indices': channels1},
                       {'rule_id': 5, 'in_port': 1, 'out_port': 103, 'signal_indices': channels2}]

        self.roadm3 = [{'rule_id': 3, 'in_port': 1, 'out_port': 103, 'signal_indices': channels1 + channels2}]
