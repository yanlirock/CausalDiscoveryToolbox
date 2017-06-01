"""
Graph utilities : Definition of classes
Cycles detection & removal
Author : Diviyan Kalainathan & Olivier Goudet
Date : 21/04/2017
"""

import numpy as np
from copy import deepcopy
from collections import defaultdict

def cyclic(g):
    """
        Return True if the directed graph g has a cycle.
        g must be represented as a dictionary mapping vertices to
        iterables of neighbouring vertices.

        :Exemple:
            >>> cyclic({1: (2,), 2: (3,), 3: (1,)})
            True
            >>> cyclic({1: (2,), 2: (3,), 3: (4,)})
            False

    """
    path = set()
    visited = set()

    def visit(vertex):
        if vertex in visited:
            return False
        visited.add(vertex)
        path.add(vertex)
        for neighbour in g.get(vertex, ()):
            if neighbour in path or visit(neighbour):
                return True
        path.remove(vertex)
        return False

    return any(visit(v) for v in g)


def cycles(g):
    """Return the list of cycles of the directed graph g .
    g must be represented as a dictionary mapping vertices to
    iterables of neighbouring vertices. For example:

    >>> cycles({1: (2,), 2: (3,), 3: (1,)})
    [1,2,3,1]
    >>> cycles({1: (2,), 2: (3,), 3: (4,)})
    []

    """

    def dfs(graph, start, end):
        fringe = [(start, [])]
        # print(len(graph))
        while fringe:
            state, path = fringe.pop()
            if path and state == end:
                yield path
                continue
            for next_state in graph[state]:
                if next_state in path:
                    continue
                fringe.append((next_state, path + [next_state]))

    return [[node] + path for node in g for path in dfs(g, node, node) if path]


def list_to_dict(links):
    dic = defaultdict(list)
    for link in links:
        dic[int(link[0][1:])].append(int(link[1][1:]))
        if int(link[1][1:]) not in dic:
            dic[int(link[1][1:])] = []
    return dic



class DirectedGraph(object):
    """ Graph data structure, directed. """

    def __init__(self, df=None):
        """ Create a new directed graph structure"""
        self._graph = defaultdict(dict)
        connections = []
        if df:
            for idx, row in df.iterrows():
                connections.append(row)
            self.add_connections(connections)

    def add_edges(self, connections):
        """ Add connections (list of tuple pairs) to graph

        :param connections: List of tuples (cause, effect, weight)
        :type connections: list
        """

        for node1, node2, weight in connections:
            self.add(node1, node2, weight)

    def add(self, node1, node2, weight):
        """ Add or update directed connection from node1 to node2

        :param node1: cause of the edge
        :param node2: effect of the edge
        :param weight: value of edge
        :type weight: float
        """

        self._graph[node1][node2] = weight

    def reverse_edge(self, node1, node2, weight=None):
        """ Reverse the edge between node1 and node2
        with possibly a new weight value

        :param node1: initial cause of the edge
        :param node2: initial effect of the edge
        :param weight: new value of edge
        :type weight: float
        """

        if not weight:
            weight = self._graph[node1][node2]
        self.remove_edge(node1, node2)
        self.add(node2, node1, weight)

    def remove_edge(self, node1, node2):
        """ Remove the edge from node1 to node2

        :param node1: cause of the edge
        :param node2: effect of the edge
        """
        del self._graph[node1][node2]
        if len(self._graph[node1]) == 0:
            del self._graph[node1]

    def get_parents(self, node):
        """ Get the list of parents of a node

        :param node: Selected node
        :return: list of parents of the nodes
        :rtype: list
        """
        parents = []
        for i in self._graph:
            if node in list(self._graph[i]):
                parents.append(i)
        return parents

    def get_list_nodes(self):
        """ Get list of all nodes in graph

        :return: List of nodes
        :rtype: list

        """

        nodes = []
        for i in self._graph:
            if i not in nodes:
                nodes.append(i)
            for j in list(self._graph[i]):
                if j not in nodes:
                    nodes.append(j)
        return nodes

    def get_list_edges(self, order_by_weight=True, descending=False):
        """ Get list of edges according to order defined by parameters

        :param order_by_weight: List of edges will be ordered by weight values
        :param descending: order elements by decreasing weights
        :return: List of edges and their weights
        :rtype: (list,list)"""

        list_edges = []
        weights = []
        for i in self._graph:
            for j in list(self._graph[i]):
                list_edges.append([i, j])
                weights.append(self._graph[i][j])

        if order_by_weight and descending:
            weights, list_edges = (list(i) for i
                                   in zip(*sorted(zip(weights, list_edges),
                                                  reverse=True)))
        elif order_by_weight:
            weights, list_edges = (list(i) for i
                                   in zip(*sorted(zip(weights, list_edges))))
        return list_edges, weights

    def get_adjacencyMatrix(self):
        """Get the adjacency matrix of the graph

        :return: Adjacency Matrix (size : Nodes x Nodes), List of nodes
        :rtype: (numpy.ndarray, list)
        """

        nodes = self.get_list_nodes()
        edges, weights = self.get_list_edges(order_by_weight=False)

        M = np.zeros((len(nodes), len(nodes)))

        for idx, e in enumerate(edges):
            cause = nodes.index(e[0])
            effect = nodes.index(e[1])

            M[cause,effect] = weights[idx]

        return M, nodes

    def get_dict_nw(self):
        """Get dictionary of graph without weight values

        :return: Dictionary of the directed graph
        :rtype: dict

        """

        dict_nw = defaultdict(list)
        for i in self._graph:
            for j in list(self._graph[i]):
                dict_nw[i].append(j)
                if j not in dict_nw:
                    dict_nw[j] = []
        return dict(dict_nw)

    def remove_node(self, node):
        """ Remove all references to node

        :param node: node to remove
        :type node: str

        """

        for n, cxns in self._graph.iteritems():
            try:
                cxns.remove(node)
            except KeyError:
                pass
        try:
            del self._graph[node]
        except KeyError:
            pass

    def remove_cycles(self, verbose=True):
        """ Remove all cycles in graph by using the weights"""

        list_ordered_edges = self.get_list_edges()
        while cyclic(self.get_dict_nw()):
            cc = cycles(self.get_dict_nw())
            # Select the first link:
            s_cycle = cc[0]
            r_edge = next(edge for edge in list_ordered_edges if
                          any(edge == s_cycle[i:i + 2]
                              for i in range(len(s_cycle) - 1)))
            print('CC:' + str(cc))
            print(r_edge)
            # Look if the edge can't be reversed
            test_graph = deepcopy(self)
            test_graph.reverse_edge(r_edge[0], r_edge[1])
            print(test_graph)
            if len(cycles(test_graph.get_dict_nw())) < len(cc):
                self.reverse_edge(r_edge[0], r_edge[1])
                if verbose:
                    print('Link {} got reversed !'.format(r_edge))

            else:  # remove the edge
                self.remove_edge(r_edge[0], r_edge[1])
                if verbose:
                    print('Link {} got deleted !'.format(r_edge))

    def __str__(self):
        return '{}({})'.format(self.__class__.__name__, dict(self._graph))