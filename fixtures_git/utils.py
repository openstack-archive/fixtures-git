# Copyright (c) 2013-2016 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2018 Hewlett Packard Enterprise Development Company LP
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re


def _get_node_to_pick(node):
    m = re.search(r'(.*)(\d+)$', node)
    if m:
        # get copy of a another change
        node_number = int(m.group(2)) - 1
        node_name = m.group(1)
        if node_number > 0:
            node_name += str(node_number)
        return node_name
    return None


_NOT_VISITED = 0
_VISITED = 1
_FINISHED = 2


def _reverse_toposort(data):

    # convert to dict for linear lookup times when returning
    data = dict(data)

    # keep track of nodes visited and processed
    # by checking if a child has been visited before but not processed you
    # can detect a back edge and abort since the graph is not acyclic
    visited = dict()

    # DFS algorithm with customization to handle use of '=' notation for merge
    # commits and also the additional dependency for cherry-picking
    nodes_to_visit = []
    for i in data.keys():
        if i not in visited:
            nodes_to_visit.append(i)

        while nodes_to_visit:
            node = nodes_to_visit.pop()
            if visited.get(node) is _VISITED:
                # already visited so just return it with it's deps
                yield (node, data[node])
                visited[node] = _FINISHED
                continue
            elif visited.get(node) is _FINISHED:
                continue

            visited[node] = _VISITED
            nodes_to_visit.append(node)
            # special case for cherry-picking changes
            c_node = _get_node_to_pick(node)
            if c_node and c_node not in visited:
                nodes_to_visit.append(c_node)

            for d in data[node]:
                r_d = d.strip('=')
                if r_d not in visited:
                    nodes_to_visit.append(r_d)
                else:
                    # if we've already visited a dep but not processed it,
                    # then we have a back edge of some kind
                    if visited[r_d] is _VISITED:
                        message = ("Graph is not acyclic: %s is a dependency "
                                   "of %s, but has been visited without being "
                                   "processed before it." % (r_d, node))
                        raise RuntimeError(message)
