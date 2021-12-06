"""
This File creates a Topology visualization using the Network object using Dash which builts upon react.js and flask

Requirements:

pip install dash
pip install dash-cytoscape

Use the import statement

from mininet_optical.visualize_topo import visualize_topology

Call the function visualize_topology(<Network class>)

Open http://127.0.0.1:8050 in the browser after calling the function

"""


import dash
import dash_cytoscape as cyto
import dash_html_components as html
import threading
import mininet_optical.node as node
from mininet_optical.node import db_to_abs, abs_to_db
import dash_core_components as dcc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots



def extract_power(component,mode='in'):
    """
    :param component : Component (Amplifiers, ROADM) for which power needs to be extracted
    :param mode: The power values to extracted from input or output mode
    :return signal_index: Returns signal_index (channel index used for transmission)
    :return power: Returns power (power values at the port in transmission)
    """

    power_list = []
    signal_index = []

    if (isinstance(component,node.Amplifier)):
        if mode=='in':
            for signal, power in component.input_power.items():
                signal_index.append(signal.index)
                power_list.append(abs_to_db(power))

            return signal_index, power_list
        if mode=='out':
            for signal, power in component.output_power.items():
                signal_index.append(signal.index)
                power_list.append(abs_to_db(power))

            return signal_index, power_list

    if (isinstance(component,node.Roadm)):
        roadm_power_type = {}
        if mode == 'in':
            roadm_power_type = component.port_to_optical_signal_power_in
        if mode == 'out':
            roadm_power_type = component.port_to_optical_signal_power_out

        for port in sorted(roadm_power_type):
            signal_powers = roadm_power_type[port]
            signal_index = []
            if signal_powers:

                for signal, power in signal_powers.items():
                    signal_index.append(signal.index)
                    power_list.append(abs_to_db(power))

        return signal_index, power_list

def visualize_topology(net):

    """
    :param net: Network Object
    :return: Calls the Network Visualization function in a separate thread
    """

    t = threading.Thread(target=visualize, args=(net,))  # Calls the visualization function as a separate thread from the calling script
    t.setDaemon(True)
    t.start()  # Start the thread

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


    app = dash.Dash() # Calling the Dash-App

    # Stylesheet for styling different components in the Topology

    stylesheet = [
        # Group selectors
        {
            'selector': 'node',
            'style': {
                'content': 'data(label)'
            }
        },
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
        html.Div(cyto.Cytoscape(
            id='mininet-optical',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '800px', "font-size": "1px", "content": "data(label)",
                   "text-valign": "center",
                   "text-halign": "center", 'radius': '10%'},
            elements= elements,
            stylesheet=stylesheet
        ), className="container"),

        html.Div(id='graph')



    ])

    @app.callback(
        Output('graph', 'children'),
        [Input('mininet-optical', 'tapNodeData')])
    def plot_power(data):

        """
                    :param tapNodeData: Selected Node
                    :return: Returns the plot division to graph container
        """

        n = net.name_to_node   # extract network object
        component = n[data['id']]  # extract the selected component from the network

        # Extract input and output power for the component

        signal_index_in, power_in = extract_power(component,mode='in')
        signal_index_out, power_out= extract_power(component, mode='out')

        layout = go.Layout(
            xaxis={ 'type':'category','title': "Channel-Index"},
            yaxis={'type': 'linear', 'title': "Power (dBm)"},
            # margin={'l': 60, 'b': 40, 'r': 10, 't': 10},
        )

        fig = make_subplots(rows=1, cols=2,subplot_titles=(str(data['id']),str(data['id'])))

        # Plot input power

        fig.add_trace(
            go.Scatter(x=signal_index_in, y=power_in, name="Power-In"),
            row=1, col=1
        )

        # plot output power

        fig.add_trace(
            go.Scatter(x=signal_index_out, y=power_out,name="Power-Out"),
            row=1, col=2
        )

        fig.update_layout(layout)
        fig.update_xaxes(title_text="Channel-Index", row=1, col=2,type='category')
        fig.update_yaxes(title_text="Power (dBm)", row=1, col=2)

        return html.Div(dcc.Graph(figure=fig))

    app.run_server(debug= False)

