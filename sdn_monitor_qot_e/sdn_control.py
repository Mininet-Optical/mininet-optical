from ofcdemo.fakecontroller import (RESTProxy, fetchNodes)


def run(net, N=3):
    "Configure and monitor network with N=3 channels for each path"

    # Fetch nodes
    net.allNodes = fetchNodes(net)
    print(net.allNodes)


if __name__ == '__main__':
    net = RESTProxy()
    run(net)
