import matplotlib.pyplot as plt
import numpy as np
import networkx as nx

import os
import json
from collections import Counter
from datetime import datetime, timedelta


def draw_graph(G, intervals, curved_arrows=True):

    # Figure for all users
    fig_all, ax_all = plt.subplots(figsize=(12,12))
    ax_all.set_title('All users', fontsize=20)
    ax_all.axis('off')

    # General positions of nodes
    pos = nx.circular_layout(G)
    pos = nx.rescale_layout_dict(pos)

    # Positions for labels to prevent overlapping
    pos_labels = dict()
    for k, p in pos.items():
        pos_labels[k] = pos[k] + (0.25, 0.0) if pos[k][0] > 0.0 else pos[k] + (-0.25, 0.0)

    # Draw nodes figure for all users
    nx.draw_networkx_nodes(G, ax=ax_all, pos=pos, node_size=50, node_color='black')
    nx.draw_networkx_labels(G, ax=ax_all, pos=pos_labels, clip_on=False)


    # Assign colors and create figures for separate users
    colors = iter(['b','r','g','c','m','y'])
    user_colors = dict()
    user_figures = dict()
    for user in intervals.keys():
        user_colors[user] = next(colors)    
        fig_u, ax_u = plt.subplots(figsize=(12,12))
        ax_u.set_title(user, fontsize=20)
        user_figures[user] = (fig_u, ax_u)
        nx.draw_networkx_nodes(G, ax=ax_u, pos=pos, node_size=50, node_color='black')
        nx.draw_networkx_labels(G, ax=ax_u, pos=pos_labels, clip_on=False)
        ax_u.axis('off')

    # Iterate over edges add draw them to appropriate figures
    link_counter = Counter()
    deltas = [0.0]
    for i in range(1, (len(intervals)+1)//2):
        deltas.append(i/100)
        deltas.append(-i/100)

    for i, j, user in G.edges(keys=True):
        p1 = pos[i]
        p2 = pos[j]
        diff = p2-p1
        l = np.linalg.norm(diff)
        new_pos = dict()
        delta = deltas[link_counter[(i,j)]]
        connectionstyle = 'arc3'
        color = user_colors[user]
        if curved_arrows:
            connectionstyle += ',rad='+str(delta/(0.6*l))
            new_pos[i] = p1
            new_pos[j] = p2
        else:
            diff = (diff[1]/l, -diff[0]/l)
            new_pos[i] =  (p1[0]+delta*diff[0], p1[1]+delta*diff[1])
            new_pos[j] =  (p2[0]+delta*diff[0], p2[1]+delta*diff[1])
        nx.draw_networkx_edges(G, ax=ax_all, arrowsize=10, arrowstyle='->',
                               connectionstyle=connectionstyle, pos=new_pos,
                               label=user, edge_color=color, edgelist = [(i,j)])
        nx.draw_networkx_edges(G, ax=user_figures[user][1], arrowsize=15,
                               arrowstyle='-|>', pos=pos, label=user,
                               edge_color=color, edgelist = [(i,j)])
        nx.draw_networkx_edge_labels(G, pos=pos, ax=user_figures[user][1],
                                    font_size=8, alpha=0.5,
                                    edge_labels = {(i,j):G[i][j][user]['weight']})
        link_counter[(i,j)] += 1
        
    plt.show()



def generate_call_graph(pptam_dir, tracing_dir, time_delta):
    user_boundaries, instance_boundaries = detect_users(pptam_dir, time_delta)

    # Get calls and pipelines for each user using logs of each service
    call_counters = dict()
    pipelines = dict()
    for file in os.listdir(tracing_dir):
        if file.endswith(".log"):
            parse_logs(tracing_dir, file, user_boundaries, instance_boundaries, call_counters, pipelines)

    # Sort pipelines by time of call
    for l in pipelines.values():
        l.sort(key = lambda x: x[0])

    # Create networkx' multigraph, edges are identified by User
    user_graphs = dict()
    for user, counter in call_counters.items():
        G = nx.MultiDiGraph()
        user_graphs[user] = G
        for keys, weight in counter.items():
            G.add_edge(keys[0], keys[1], key=keys[2], weight=weight)

    return user_graphs, pipelines


if __name__ == '__main__':
    
    directory = "kubernetes-istio-sleuth-v0.2.1-separate-load"
    pptam_dir = os.path.join(directory, 'pptam')
    tracing_dir = os.path.join(directory, 'tracing-log')
    time_delta = timedelta(hours=-8)
    G, pipelines = generate_call_graph(pptam_dir, tracing_dir, time_delta)
    bundles_service, bundles_endpoint = detect_request_bundle(pipelines)
    #write_pipelines(pipelines)
    #draw_graph(G, intervals)

