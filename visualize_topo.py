"""
This File creates a Topology visualization using the Network object using Dash which builts upon react.js and flask

Requirements:

pip install dash
pip install dash-cytoscape

Use the import statement

from visualize_topo import visualize_topology

Call the function visualize_topology(<Network class>)

Open http://127.0.0.1:8050 in the browser after calling the function

"""


import dash
import dash_cytoscape as cyto
import dash_html_components as html
import threading
import node



def visualize_topology(net):

    """
        :param net: Network Object
        :return: Calls the Network Visualization function in a separate thread
    """

    t = threading.Thread(target=visualize, args=(net,))  # Calls the visualization function as a separate thread from the calling script
    t.setDaemon(True)
    t.start()  # Start the thread


"""
Absolute : Required for preset configuration/position of elements

def point(h, k, r,theta):
    #theta = random() * 2 * i
    return h + cos(theta) * r, k + sin(theta) * r

def get_position(component,theta):
    pos_dict={'lt': 40, 'roadm': 80,'amp': 80}
    circle_centre=(1,2)
    for key in pos_dict.keys():
        if key in str(component):
            x,y=point(circle_centre[0],circle_centre[1],pos_dict[key],theta)
    return x,y

def get_theta(net,theta):
    theta_value = theta / len(net.topology)
    return theta_value


"""



def visualize(net):

    """
            :param net: Network Object
            :return: Creates a server accessible at http://127.0.0.1:8050 with Network Topology
    """

    elements = [] # Consists Data-Point for Input for Dash


    # Add ROADMS and LineTerminal to the elements data

    for components in net.topology.keys():

        if isinstance(components,node.LineTerminal): # Check for lineterminal instance and apply 'lt' class to it
            elements.append(
                {'data': {'id': str(components), 'label': str(components)},
                 'classes': "lt"})
            for transceivers in components.name_to_transceivers.keys():
                elements.append(
                    {'data': {'id': str(transceivers), 'label': str(transceivers)},
                     'classes': "transceiver"})
                elements.append({'data': {'source': str(components), 'target': str(transceivers)}})

        if isinstance(components,node.Roadm): # Check for lineterminal instance and apply 'lt' class to it
            elements.append(
                {'data': {'id': str(components), 'label': str(components)},
                 'classes': "roadm"})

    # Check for Amplifiers in each of the links

    for link in net.links:

        if len(link.spans) == 1:
          elements.append({'data': {'source': str(link.node1), 'target': str(link.node2)}})

        else:
            start = link.node1

            for span, amplifier in link.spans:
                if amplifier != None:

                    elements.append(
                        {'data': {'id': str(amplifier.name), 'label': str(amplifier.name)},'classes':'amp'})
                    elements.append({'data': {'source': str(start), 'target': str(amplifier.name)}})
                    start = amplifier.name

            elements.append({'data': {'source': str(start), 'target': str(link.node2)}})


    app = dash.Dash('__main__') # Calling the Dash-App

    # Stylesheet for styling different components in the Topology

    stylesheet = [
        # Group selectors
        {
            'selector': 'node',
            'style': {
                'content': 'data(label)'
            }
        },

        # Class selectors
        {
            'selector': '.lt',
            'style': {
                'background-color': 'red',
                'line-color': 'red'
            }
        },
        {
            'selector': '.roadm',
            'style': {
                'background-color': 'blue',
                'line-color': 'blue'
            }
        },
        {
            'selector': '.amp',
            'style': {
                'shape': 'triangle'
            }
        },
        {
            'selector': '.transceiver',
            'style': {
                'background-color': 'green',
                'shape': 'rectangle'
            }
        }
    ]

    # Layout of the Dash-App

    app.layout = html.Div([
        cyto.Cytoscape(
            id='Optical-Topology',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '800px', "font-size": "1px", "content": "data(label)",
                   "text-valign": "center",
                   "text-halign": "center", 'radius': '10%'},
            elements= elements,
            stylesheet=stylesheet
        )
    ])

    app.run_server(debug= False)

