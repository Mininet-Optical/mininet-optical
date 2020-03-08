#!flask/bin/python
from flask import Flask
import sys

pid = sys.argv[1]
print(pid)

app = Flask(__name__)

@app.route('/')
def index():
    return "Node is established!"

def setupServer(portId):
    app.run(host='127.0.0.1', port=portId)

if __name__ == '__main__':
    portId = int(pid)
    setupServer(portId)

