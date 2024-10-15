""" 
This module contains all plot related functionality. The functions under this module does not return any output, but only visualise a plot and/or save it on the hard disk.

.. warning:: `Inkscape <https://inkscape.org/>`_ must be installed to export figures as an .emf file. 

The functions rely on a default Inscape path (*C:/Program Files/Inkscape/bin/inkscape.exe*), which can be overridden by providing the path to the *inkscape* keyword argument. 
"""

import matplotlib.pyplot as plt
import subprocess, os

 # Export the output as emf
def export_as_emf(fig, inkscape_path, file_path):
    '''
    Exports the current figure as an .emf file. 
    
    Args:
        - **fig** (figure): The current figure (may be the turn function or polygons iteself)
        - **inkscape_path** (str): The path to the Inkscape.exe.
        - **file_path** (str): The path of the output .emf file. 
        

    '''
      
    path, filename = os.path.split(file_path)
    filename, extension = os.path.splitext(filename)
     
    svg_filepath = os.path.join(path, filename+'.svg')
    emf_filepath = os.path.join(path, filename+'.emf')
     
    fig.savefig(svg_filepath, format='svg')
    subprocess.call([inkscape_path, svg_filepath, '--export-filename', emf_filepath])
    os.remove(svg_filepath)

def plot_turning_function(turn, **kwargs):  
    '''
    Plots the cumulative length turn function. 
    
    Args:
        - **turn** (*dict*): The turn dictionary of a polygon.
        - **kwargs**:
            - edge_labels: The edge labels would also be printed on the turn function to increase legibility. The first digitised node's label is assumed to be *a*, the second *b*, and so on.  A constant is used, *one_char_shift* that centers the label with respect to the turn functions edge.
            - file_path: The turn function is saved as an .emf file to the designated *file_path*. Inkscpace is used to convert .svg to .emf. The path to Inkscape may require update.

    '''
    
    fig, ax = plt.subplots()
    
    # Plot the turn function
    cum_sum_lengths = [] + turn["lengths"] 
    cum_sum_angles = [] + turn["angles"]
        
    for i in range(1,len(turn["lengths"])):
        cum_sum_angles[i] = cum_sum_angles[i] + cum_sum_angles[i-1]
        cum_sum_lengths[i] = cum_sum_lengths[i] + cum_sum_lengths[i-1]
    
    #multiply with two to obtain the piecewise nature to plot
    piece_wise_angles = [0]*(len(cum_sum_angles)*2)
    piece_wise_lengths = [0]*(len(cum_sum_angles)*2)
    
    for i in range(len(cum_sum_angles)):
        # y
        piece_wise_angles[i*2] = cum_sum_angles[i]
        piece_wise_angles[i*2 + 1] = cum_sum_angles[i]
    
    for i in range(len(cum_sum_lengths)-1):
        # x
        piece_wise_lengths[i*2 + 1] = cum_sum_lengths[i]  
        piece_wise_lengths[i*2 + 2] = cum_sum_lengths[i]
    piece_wise_lengths[-1] = cum_sum_lengths[-1]
    
    
    plt.plot(piece_wise_lengths, piece_wise_angles)
    plt.xlabel("Length of edges", fontsize=14)
    plt.ylabel("Turn angles", fontsize=14)
    
    if('edge_labels' in kwargs):
        # Assumption: First digitised node is labelled with "a" and then continues alphabetically
        # Generate the edge labels
        
        edge_labels = []
        node_a = "b" # the next label
        
        for i in range(len(cum_sum_lengths)-2):
            label = node_a + chr(ord(node_a) + 1)
            if(i==0):
                x = cum_sum_lengths[i] / 2
            else:
                x = ((cum_sum_lengths[i] - cum_sum_lengths[i-1])  / 2) + cum_sum_lengths[i-1]
            
            edge_labels.append([x, cum_sum_angles[i], label])
        
            # Prepare for the next edge
            node_a = chr(ord(node_a) + 1)
        
        # Determine the label of the last edge and the first edge
        # Last edge
        last_edge_x = ((cum_sum_lengths[i+1] - cum_sum_lengths[i])  / 2) + cum_sum_lengths[i]
        label = node_a + "a"
        edge_labels.append([last_edge_x, cum_sum_angles[i+1], label])
        # First edge
        first_edge_x = ((cum_sum_lengths[i+2] - cum_sum_lengths[i+1])  / 2) + cum_sum_lengths[i+1]
        label = "ab"
        edge_labels.append([first_edge_x, cum_sum_angles[i+2], label])
        
        if(type(kwargs['edge_labels']) == list):
           # Edge labels are provided as an input
           # Override the default labels
           for i in range(len(kwargs['edge_labels'])):
               edge_labels[i][2] = kwargs['edge_labels'][i]
               
            
        
        # Print the edge labels
        # Shift the x position a little towards left to center the piecewise unit - one character
        one_char_shift = 0.03
        for i in range(len(edge_labels)):
            plt.text(edge_labels[i][0] - one_char_shift, edge_labels[i][1], edge_labels[i][2], fontsize=12)
        
    plt.show()
    
    # Hide the right and top spines - better view
    # REF: https://stackoverflow.com/questions/925024/how-can-i-remove-the-top-and-right-axis-in-matplotlib
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    
    
    # Export the turn function as an emf file
    if('file_path' in kwargs):
        inkscape_path = kwargs.get('inkscape', "C://Program Files//Inkscape//bin//inkscape.exe")
        file_path = kwargs.get('file_path', None)
        
        # Export the output as emf
        export_as_emf(fig, inkscape_path, file_path)
        

def plot_polygon(poly_a):
    '''
    Plots an input polygon
    
    Args:
        - **poly_a** (*polygon*): The input polygon to be plotted.
    
    Returns:
        - The plotted polygon
    '''
    fig, ax = plt.subplots()
    
    # Plot the edges
    for i in range(len(poly_a.exterior.coords)-1):
        ax.plot([poly_a.exterior.coords[i][0], poly_a.exterior.coords[i+1][0]], 
                 [poly_a.exterior.coords[i][1], poly_a.exterior.coords[i+1][1]], 'b')
    
    # Plot the nodes
    for i in range(len(poly_a.exterior.coords)-1):
        ax.plot(poly_a.exterior.coords[i][0], 
                 poly_a.exterior.coords[i][1], 'bo',
                 markersize = 12,
                 fillstyle = 'none')
    
    # Remove the axes
    fig.patch.set_visible(False)
    ax.axis('off')

def plot_x2polygons(poly_a, poly_b, **kwargs):
    '''
    Plots two matching (homologous) polygons - one from OSM and the other from the reference dataset.
    
    Args:
        - **poly_a** (*polygon*): First polygon
        - **poly_b** (*polygon*): Second polygon
        - *kwargs*: 
            - **file_path** (*str*): Output path of the output .emf file. 
            - **with_node_labels**: If the node labels with their coordinates are to displayed, the user is required to provide the label_drift list that provides the shift in *x* and *y* axis. The values should be adjusted based on the plausibility of the outcome. 

    Examples:
        
        >>> plot_x2polygons(poly_a, poly_b, file_path = "C:/Users/ijgis/Desktop/out.emf")
        >>> plot_x2polygons(poly_a, poly_b, with_node_labels = [1, 0.3])
    '''
    fig, ax = plt.subplots()
    
    # First polygon
    # Plot the edges 
    for i in range(len(poly_a.exterior.coords)-1):
        ax.plot([poly_a.exterior.coords[i][0], poly_a.exterior.coords[i+1][0]], 
                 [poly_a.exterior.coords[i][1], poly_a.exterior.coords[i+1][1]], 'r')
        
    # Plot the nodes
    for i in range(len(poly_a.exterior.coords)-1):
        ax.plot(poly_a.exterior.coords[i][0], 
                 poly_a.exterior.coords[i][1], 'rs',
                 markersize = 12,
                 fillstyle = 'full',
                 label = "A")
    
    # Second polygon
    # Plot the edges 
    for i in range(len(poly_b.exterior.coords)-1):
        ax.plot([poly_b.exterior.coords[i][0], poly_b.exterior.coords[i+1][0]], 
                 [poly_b.exterior.coords[i][1], poly_b.exterior.coords[i+1][1]], 'b',
                 linestyle='dashed')
        
    # Plot the nodes
    for i in range(len(poly_b.exterior.coords)-1):
        ax.plot(poly_b.exterior.coords[i][0], 
                 poly_b.exterior.coords[i][1], 'bo',
                 markersize = 8,
                 fillstyle = 'full',
                 label = 'B')
    
    # Remove the axes
    fig.patch.set_visible(False)
    ax.axis('off')
    
    # Make sure the length of one unit in X & Y axis is the same
    ax.set_aspect('equal')
    
    # Setting the axis limits
    # ax.set_xlim(-2, 12)
    # ax.set_ylim(-2, 12)
    
    
    # Do not repeat the legend labels (i.e. for each node).
    # REF: https://stackoverflow.com/questions/13588920/stop-matplotlib-repeating-labels-in-legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc = 'center')
    
    
    # Node labels 
    save_nodes = []
    if ('with_node_labels' in kwargs):
        # Position the labels w.r.t. to the location of the nodes - how much to shift?
        label_drift = kwargs['with_node_labels']
        
        # For polygon A
        for i in range(len(poly_a.exterior.coords)-1):
            if( (int(poly_a.exterior.coords[i][0]) - poly_a.exterior.coords[i][0] ) != 0):
                x_val = str(poly_a.exterior.coords[i][0])
            else:
                x_val = str(int(poly_a.exterior.coords[i][0])) # for better visualisation
            
            if( (int(poly_a.exterior.coords[i][1]) - poly_a.exterior.coords[i][1] ) != 0):
                y_val = str(poly_a.exterior.coords[i][1])
            else:
                y_val = str(int(poly_a.exterior.coords[i][1]))
            
            node_label = 'a' + str(i) + "(" + x_val + "," + y_val + ")"  
            ax.text(poly_a.exterior.coords[i][0]-label_drift[0], poly_a.exterior.coords[i][1]-label_drift[0], 
                    node_label, 
                    style='italic',
                    color='red')
            save_nodes.append((poly_a.exterior.coords[i][0], poly_a.exterior.coords[i][1]))
        
        # For Polygon B
        for i in range(len(poly_b.exterior.coords)-1):
            # If a node B coincides with a node from A, skip its coordinates
            if( (int(poly_b.exterior.coords[i][0]) - poly_b.exterior.coords[i][0] ) != 0):
                x_val = str(poly_b.exterior.coords[i][0])
            else:
                x_val = str(int(poly_b.exterior.coords[i][0]))
            
            if( (int(poly_b.exterior.coords[i][1]) - poly_b.exterior.coords[i][1] ) != 0):
                y_val = str(poly_b.exterior.coords[i][1])
            else:
                y_val = str(int(poly_b.exterior.coords[i][1]))
            
            node_tmp = (poly_b.exterior.coords[i][0], poly_b.exterior.coords[i][1])
            if (node_tmp in save_nodes):
                node_label = 'b' + str(i)
            else:
                node_label = 'b' + str(i) + "(" + x_val + "," + y_val + ")"  
            
            ax.text(poly_b.exterior.coords[i][0]+label_drift[1], poly_b.exterior.coords[i][1]+label_drift[1], 
                    node_label, 
                    style='italic',
                    color='blue')
        
            #ax.text -> bbox={'facecolor': 'red', 'alpha': 0.5, 'pad': 10}

    # Save the plot as a vector graphic
    # REF: https://stackoverflow.com/questions/9266150/matplotlib-generating-vector-plot
    if('file_path' in kwargs):
        inkscape_path = kwargs.get('inkscape', "C://Program Files//Inkscape//bin//inkscape.exe")
        filepath = kwargs.get('file_path', None)
        
        export_as_emf(fig, inkscape_path, filepath)
            
        

    
    
    

    