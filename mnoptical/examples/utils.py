class Queue:
    """A container with a first-in-first-out (FIFO) queuing policy."""

    def __init__(self):
        self.list = []

    def push(self, item):
        """Enqueue the 'item' into the queue"""
        self.list.insert(0, item)

    def pop(self):
        """
          Dequeue the earliest enqueued item still in the queue. This
          operation removes the item from the queue.
        """
        return self.list.pop()

    def isEmpty(self):
        """Returns true if the queue is empty"""
        return len(self.list) == 0


class NodeInformation:
    """Store link connection information - linein/lineout that can be used to automate connection script"""

    def __init__(self, nodeid, neighid, linein, lineout, reverse=False):
        self.node_id = nodeid
        self.neigh_id = neighid
        self.lineout = lineout
        self.linein = linein
        self.reverse = reverse

    def get_link(self):
        """return lineout and linein information"""
        # TODO: add check to verify whether all ports are used. if yes, update bfs algorithm to check this before deciding optimal path.
        return self.lineout.pop(0), self.linein.pop(0)
