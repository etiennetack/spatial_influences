# coding: utf-8
# from typing import TYPE_CHECKING
import networkx as nx

# if TYPE_CHECKING:
#     from agents import Agent


class Relationship:
    def __init__(self, name: str, directed: bool = True):
        self.name = name
        self.graph = nx.DiGraph() if directed else nx.Graph()

    def add_agent(self, agent_id):
        self.graph.add_node(agent_id)

    def add_relation(self, agent_a, agent_b, relation_type: str | None = None):
        if relation_type:
            self.graph.add_edge(agent_a, agent_b, type=relation_type)
        else:
            self.graph.add_edge(agent_a, agent_b)

    def remove_agent(self, agent_id):
        self.graph.remove_node(agent_id)

    def remove_relation(self, agent_a, agent_b):
        self.graph.remove_edge(agent_a, agent_b)

    def get_relations(self, agent_id, level=1):
        res = {}
        for relative_agent, relation in self.graph[agent_id].items():
            relations = res.get(relation["type"], set())
            relations.add(relative_agent)
            res[relation["type"]] = relations
            if level > 1:
                print(self.get_relations(relative_agent, level - 1))
        return res

    def get_relation(self, agent_id, relation_type, level=1):
        res = set()
        for relative_agent, relation in self.graph[agent_id].items():
            if relation["type"] == relation_type:
                res.add(relative_agent)
        return res

    def dot(self):
        # TODO not working
        # nx.drawing.nx_pydot.write_dot(self.graph)
        return nx.drawing.nx_pydot.to_pydot(self.graph)
