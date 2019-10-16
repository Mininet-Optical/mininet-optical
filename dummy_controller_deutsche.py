from deutsche_telekom import DeutscheTelekom

net = DeutscheTelekom.build()
print("Number of line terminals: %s" % len(net.line_terminals))
print("Number of ROAMDs: %s" % len(net.roadms))
print("Number of links: %s" % len(net.links))
