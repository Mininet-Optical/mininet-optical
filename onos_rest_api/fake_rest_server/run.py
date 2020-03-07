import os 
import sys

n = sys.argv[1]
print(n)

os.system('bash run.sh {}'.format(n))
