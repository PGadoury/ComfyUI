import json
import random

# The GraphBuilder is just a utility class that outputs graphs in the form expected by the ComfyUI back-end
class GraphBuilder:
    def __init__(self, prefix = True):
        if isinstance(prefix, str):
            self.prefix = prefix
        elif prefix:
            self.prefix = "%d.%d." % (random.randint(0, 0xffffffffffffffff), random.randint(0, 0xffffffffffffffff))
        else:
            self.prefix = ""
        self.nodes = {}
        self.id_gen = 1

    def node(self, class_type, id=None, **kwargs):
        if id is None:
            id = str(self.id_gen)
            self.id_gen += 1
        id = self.prefix + id
        if id in self.nodes:
            return self.nodes[id]

        node = Node(id, class_type, kwargs)
        self.nodes[id] = node
        return node

    def lookup_node(self, id):
        id = self.prefix + id
        return self.nodes.get(id)

    def finalize(self):
        output = {}
        for node_id, node in self.nodes.items():
            output[node_id] = node.serialize()
        return output

    def replace_node_output(self, node_id, index, new_value):
        to_remove = []
        for node in self.nodes.values():
            for key, value in node.inputs.items():
                if isinstance(value, list) and value[0] == node_id and value[1] == index:
                    if new_value is None:
                        to_remove.append((node, key))
                    else:
                        node.inputs[key] = new_value
        for node, key in to_remove:
            del node.inputs[key]

    def remove_node(self, id):
        del self.nodes[id]

class Node:
    def __init__(self, id, class_type, inputs):
        self.id = id
        self.class_type = class_type
        self.inputs = inputs

    def out(self, index):
        return [self.id, index]

    def set_input(self, key, value):
        if value is None:
            if key in self.inputs:
                del self.inputs[key]
        else:
            self.inputs[key] = value

    def get_input(self, key):
        return self.inputs.get(key)

    def serialize(self):
        return {
            "class_type": self.class_type,
            "inputs": self.inputs
        }

def add_graph_prefix(graph, outputs, prefix):
    # Change the node IDs and any internal links
    new_graph = {}
    for node_id, node_info in graph.items():
        # Make sure the added nodes have unique IDs
        new_node_id = prefix + node_id
        new_node = { "class_type": node_info["class_type"], "inputs": {} }
        for input_name, input_value in node_info.get("inputs", {}).items():
            if isinstance(input_value, list):
                new_node["inputs"][input_name] = [prefix + input_value[0], input_value[1]]
            else:
                new_node["inputs"][input_name] = input_value
        new_graph[new_node_id] = new_node

    # Change the node IDs in the outputs
    new_outputs = []
    for n in range(len(outputs)):
        output = outputs[n]
        if isinstance(output, list): # This is a node link
            new_outputs.append([prefix + output[0], output[1]])
        else:
            new_outputs.append(output)

    return new_graph, tuple(new_outputs)

