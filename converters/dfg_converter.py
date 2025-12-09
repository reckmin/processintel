from dataclasses import dataclass
from typing import Any, Callable

from graphs.visualization import DirectlyFollowsGraph

@dataclass
class HeuristicDFGData:
    dependency_graph: Any
    dependency_matrix: Any
    filtered_events: list[str]
    filtered_appearance_freqs: dict[str, int]
    node_sizes: dict[str, tuple[float, float]]
    start_nodes: set[str]
    end_nodes: set[str]
    node_stats_map: dict[str, dict]
    edge_stats_map: dict[tuple[str, str], dict]
    min_edge_thickness: float
    edge_scale_factor: Callable[[int, int], float]
    get_sources: Callable[[Any], set[str]]
    get_sinks: Callable[[Any], set[str]]
    
@dataclass
class FuzzyDFGData:
    nodes_after_first_rule: set[str]
    clustered_nodes_after_sec_rule: Any
    list_of_filtered_edges_as_node: list[tuple[str, str]]
    
class DFGConverter:

    @staticmethod
    def build_empty_graph(rankdir: str = "TB") -> DirectlyFollowsGraph:
        graph = DirectlyFollowsGraph(rankdir=rankdir)
        graph.add_start_node()
        graph.add_end_node()
        graph.create_edge("Start", "End")
        return graph

    @staticmethod
    def build_heuristic_graph(data: HeuristicDFGData) -> tuple[DirectlyFollowsGraph, set[str], set[str]]:
        graph = DirectlyFollowsGraph(rankdir="TB")
        graph.add_start_node()
        graph.add_end_node()

        start_nodes = set(data.start_nodes)
        end_nodes = set(data.end_nodes)

        for node in data.filtered_events:
            stats = data.node_stats_map.get(node, {})
            norm_freq = stats.get("frequency", 0.0)
            abs_freq = data.filtered_appearance_freqs.get(node, 0)
            graph.add_event(
                title=node,
                spm=stats.get("spm", 0.0),
                normalized_frequency=norm_freq,
                absolute_frequency=abs_freq,
                size=data.node_sizes.get(node),
            )

        for i in range(len(data.filtered_events)):
            column_total = 0.0
            row_total = 0.0
            for j in range(len(data.filtered_events)):
                column_total = column_total + data.dependency_graph[i][j]
                row_total = row_total + data.dependency_graph[j][i]
                source = data.filtered_events[i]
                target = data.filtered_events[j]

                if data.dependency_graph[i][j] == 1.0:
                    edge_stats = data.edge_stats_map.get((source, target), {})
                    norm_frequency = edge_stats.get("normalized_frequency", 0.0)
                    abs_frequency = edge_stats.get("absolute_frequency", 0)
                    edge_thickness = (data.edge_scale_factor(i, j) + data.min_edge_thickness)
                    dependency_score = float(data.dependency_matrix[i][j])

                    graph.create_edge(
                        source=source,
                        destination=target,
                        size=edge_thickness,
                        normalized_frequency=norm_frequency,
                        absolute_frequency=abs_frequency,
                        dependency_score=dependency_score
                    )

                if j == len(data.filtered_events) - 1 and column_total == 0 and data.filtered_events[i] not in end_nodes:
                    end_nodes.add(data.filtered_events[i])
                if j == len(data.filtered_events) - 1 and row_total == 0 and data.filtered_events[i] not in start_nodes:
                    start_nodes.add(data.filtered_events[i])

        graph.add_starting_edges(start_nodes.intersection(set(data.filtered_events)))
        graph.add_ending_edges(end_nodes.intersection(set(data.filtered_events)))

        source_nodes = data.get_sources(data.dependency_graph).intersection(set(data.filtered_events))
        sink_nodes = data.get_sinks(data.dependency_graph).intersection(set(data.filtered_events))

        graph.add_starting_edges(source_nodes - start_nodes)
        graph.add_ending_edges(sink_nodes - end_nodes)

        return graph, start_nodes, end_nodes
    
    @staticmethod
    def build_fuzzy_graph(miner, data: FuzzyDFGData) -> DirectlyFollowsGraph:
        graph = DirectlyFollowsGraph(rankdir="TB")
        miner.graph = graph  # make sure helper methods write to the same graph

        add_clustered_nodes = getattr(miner, "_FuzzyMining__add_clustered_nodes_to_graph")
        add_normal_nodes = getattr(miner, "_FuzzyMining__add_normal_nodes_to_graph")
        add_edges = getattr(miner, "_FuzzyMining__add_edges_to_graph")

        add_clustered_nodes(data.clustered_nodes_after_sec_rule, miner.sign_dict)
        add_normal_nodes(data.nodes_after_first_rule, miner.list_of_clustered_nodes)

        add_edges(data.clustered_nodes_after_sec_rule, data.list_of_filtered_edges_as_node)

        graph.add_start_node()
        graph.add_end_node()

        start_nodes = set(
            map(
                lambda node: miner.get_node_id(node),
                miner.start_nodes.intersection(data.nodes_after_first_rule),
            )
        )
        end_nodes = set(
            map(
                lambda node: miner.get_node_id(node),
                miner.end_nodes.intersection(data.nodes_after_first_rule),
            )
        )

        graph.add_starting_edges(start_nodes)
        graph.add_ending_edges(end_nodes)

        nodes = graph.get_node_ids()
        nodes = set(nodes) - {"Start", "End"}

        for target in nodes:
            if graph.contains_edge("Start", target):
                continue
            is_start_node = True
            for source in nodes:
                if target == source:
                    continue
                if graph.contains_edge(source, target):
                    is_start_node = False
                    break
            if is_start_node:
                graph.add_starting_edges([target])

        for source in nodes:
            if graph.contains_edge(source, "End"):
                continue
            is_end_node = True
            for target in nodes:
                if target == source:
                    continue
                if graph.contains_edge(source, target):
                    is_end_node = False
                    break
            if is_end_node:
                graph.add_ending_edges([source])

        return graph
    
