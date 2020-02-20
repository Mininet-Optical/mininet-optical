import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import matplotlib.font_manager
import numpy as np


# figure(num=None, figsize=(11.7, 8.7), dpi=256)
# del matplotlib.font_manager.weight_dict['roman']
# matplotlib.font_manager._rebuild()
#
# plt.rcParams["font.family"] = "Times New Roman"
# plt.rcParams["font.size"] = 34


with open('wdg2.txt') as f:
    content = f.readlines()
# you may also want to remove whitespace characters like `\n` at the end of each line
content = [float(x) for x in content]
content_flipped = []
for i in content:
    if i < 0:
        content_flipped.append(i + 2*abs(i))
    else:
        content_flipped.append(i - 2 * i)
plt.plot(content_flipped, color='k')
plt.xlabel("Channel index")
plt.ylabel("Ripple Gain (dB)")
plt.xticks(np.arange(0, 100, 10))
plt.yticks(np.arange(-0.5, 0.6, 0.1))
# plt.savefig('wdg2_yeo_johnson.eps', format='eps')
plt.show()
