import itertools
from dataclasses import dataclass
from typing import Any, Callable

from graphs.petri_net import PetriNetToolkit, add_petri_net_to_graph
from graphs.visualization import PetriNetGraph


@dataclass
class InductivePetriNetData:
    process_tree: Any
    filtered_events: set[str]
    filtered_appearance_freqs: dict[str, int]
    node_stats_map: dict[str, dict]


@dataclass
class AlphaPetriNetData:
    nodes_to_draw: set[str]
    start_nodes: set[str]
    end_nodes: set[str]
    yl_set: set[tuple]
    filtered_events: set[str]
    filtered_appearance_freqs: dict[str, int]
    node_stats_map: dict[str, dict]
    edge_filter: Callable[[str, str], bool] | None = None


@dataclass
class GeneticPetriNetData:
    individual: dict
    filtered_events: set[str]
    filtered_appearance_freqs: dict[str, int]
    node_stats_map: dict[str, dict]
    start_nodes: set[str]


class PetriNetConverter:
    """Converter that contains the Petri net graph creation logic for different mining algorithms."""

    def __init__(self, toolkit: PetriNetToolkit | None = None):
        self.toolkit = toolkit or PetriNetToolkit()

    def build_empty_graph(self) -> PetriNetGraph:
        """Return an empty Petri net graph with just start and end connected."""
        graph = PetriNetGraph()
        graph.add_start_node()
        graph.add_end_node()
        graph.create_edge("Start", "End")
        return graph

    def build_inductive_graph(self, data: InductivePetriNetData, logger=None) -> tuple[PetriNetGraph, dict]:
        """Create a Petri net graph from an inductive mining process tree."""
        toolkit = self.toolkit
        net, start_place, end_place = toolkit.create_base_net()
        place_counter = itertools.count()
        tau_counter = itertools.count()

        def new_place(prefix: str) -> str:
            place_id = f"p_im_{prefix}_{next(place_counter)}"
            toolkit.register_place(place_id)
            return place_id

        def new_tau(prefix: str) -> str:
            return f"tau_im_{prefix}_{next(tau_counter)}"

        def connect_places(source_place: str, target_place: str, prefix: str) -> None:
            # Connect two places by inserting a silent between
            tau_id = new_tau(prefix)
            toolkit.register_transition(tau_id, visible=False)
            toolkit.add_arc(source_place, tau_id)
            toolkit.add_arc(tau_id, target_place)

        def register_visible_transition(label: str) -> str:
            base = str(label)
            trans_id = base
            suffix = 1
            while trans_id in net["transitions"]:
                suffix += 1
                trans_id = f"{base}__{suffix}"
            toolkit.register_transition(trans_id, visible=True, label=base)
            return trans_id

        def build_fragment(tree, entry_override=None, exit_override=None):
            if isinstance(tree, (str, int)):
                label = str(tree)
                entry = entry_override or new_place("leaf_in")
                exit_place = exit_override or new_place("leaf_out")
                if label == "tau":
                    trans_id = new_tau("silent")
                    toolkit.register_transition(trans_id, visible=False)
                else:
                    trans_id = register_visible_transition(label)
                toolkit.add_arc(entry, trans_id)
                toolkit.add_arc(trans_id, exit_place)
                return entry, exit_place

            if not isinstance(tree, tuple) or not tree:
                raise ValueError("Invalid process tree node")

            op = tree[0]
            children = tree[1:]

            if op == "seq":
                if not children:
                    raise ValueError("Requires at least one child")

                entry = None
                previous_exit = None

                for idx, child in enumerate(children):
                    forced_entry = entry_override if idx == 0 else previous_exit
                    forced_exit = exit_override if idx == len(children) - 1 else None
                    child_entry, child_exit = build_fragment(child, forced_entry, forced_exit)
                    if entry is None:
                        entry = child_entry
                    previous_exit = child_exit
                return entry, previous_exit

            if op == "xor":
                entry = entry_override or new_place("xor_in")
                exit_place = exit_override or new_place("xor_out")
                join_id = new_tau("xor_join")
                toolkit.register_transition(join_id, visible=False)

                toolkit.register_gateway(entry, "xor", "split")
                toolkit.register_gateway(exit_place, "xor", "join")

                for child in children:
                    child_entry, child_exit = build_fragment(child)
                    branch_id = new_tau("xor_branch")
                    toolkit.register_transition(branch_id, visible=False)
                    toolkit.add_arc(entry, branch_id)
                    toolkit.add_arc(branch_id, child_entry)
                    toolkit.add_arc(child_exit, join_id)
                toolkit.add_arc(join_id, exit_place)
                return entry, exit_place

            if op == "par":
                entry = entry_override or new_place("par_in")
                exit_place = exit_override or new_place("par_out")
                split_id = new_tau("par_split")
                join_id = new_tau("par_join")

                toolkit.register_transition(split_id, visible=False)
                toolkit.register_transition(join_id, visible=False)
                toolkit.add_arc(entry, split_id)
                toolkit.add_arc(join_id, exit_place)

                for child in children:
                    child_entry, child_exit = build_fragment(child)
                    toolkit.register_gateway(child_entry, "and", "split")
                    toolkit.add_arc(split_id, child_entry)
                    toolkit.add_arc(child_exit, join_id)
                    toolkit.register_gateway(child_exit, "and", "join")
                return entry, exit_place

            if op == "loop":
                if not children:
                    raise ValueError("Requires at least one child")
                entry = entry_override or new_place("loop_in")
                exit_place = exit_override or new_place("loop_out")

                body_entry, body_exit = build_fragment(children[0], entry_override=entry)

                connect_places(body_exit, exit_place, "loop_exit")

                if len(children) == 2 and children[1] == "tau":
                    back_id = new_tau("loop_back")
                    toolkit.register_transition(back_id, visible=False)
                    toolkit.add_arc(body_exit, back_id)
                    toolkit.add_arc(back_id, body_entry)
                    return entry, exit_place

                for redo in children[1:]:
                    redo_entry, redo_exit = build_fragment(redo)
                    connect_places(body_exit, redo_entry, "loop_redo_in")
                    connect_places(redo_exit, body_entry, "loop_redo_back")
                return entry, exit_place

            raise ValueError(f"Unsupported process tree operator: {op}")

        if data.process_tree:
            build_fragment(data.process_tree, entry_override=start_place, exit_override=end_place)
        else:
            toolkit.add_arc(start_place, end_place)

        toolkit.finalize_net(net)
        graph = PetriNetGraph()
        graph.add_start_node()
        graph.add_end_node()
        add_petri_net_to_graph(
            graph,
            net,
            data.filtered_events,
            data.node_stats_map,
            data.filtered_appearance_freqs,
            logger=logger,
        )
        return graph, net

    def build_alpha_graph(self, data: AlphaPetriNetData, logger=None) -> tuple[PetriNetGraph, dict, set[str], set[str]]:
        """Create the Petri net graph for Alpha mining."""
        graph = PetriNetGraph()
        graph.add_start_node()
        graph.add_end_node()

        net, start_place, end_place = self.toolkit.create_base_net()
        place_counter = itertools.count()

        has_incoming = {str(node): False for node in data.nodes_to_draw}
        has_outgoing = {str(node): False for node in data.nodes_to_draw}
        edge_filter = data.edge_filter or (lambda a, b: True)

        for node in data.nodes_to_draw:
            node_id = str(node)
            self.toolkit.register_transition(node_id, visible=True, label=node_id)

        for node in data.start_nodes.intersection(data.nodes_to_draw):
            node_id = str(node)
            self.toolkit.add_arc(start_place, node_id)
            has_incoming[node_id] = True

        for node in data.end_nodes.intersection(data.nodes_to_draw):
            node_id = str(node)
            self.toolkit.add_arc(node_id, end_place)
            has_outgoing[node_id] = True

        for pair in data.yl_set:
            if len(pair) != 2:
                continue

            A, B = pair
            valid_sources = [a for a in A if a in data.nodes_to_draw and any(edge_filter(a, b) for b in B)]
            valid_targets = [b for b in B if b in data.nodes_to_draw and any(edge_filter(a, b) for a in A)]

            if not valid_sources or not valid_targets:
                continue

            place_id = f"p_alpha_{next(place_counter)}"
            self.toolkit.register_place(place_id)

            for source in valid_sources:
                source_id = str(source)
                self.toolkit.add_arc(source_id, place_id)
                has_outgoing[source_id] = True

            for target in valid_targets:
                target_id = str(target)
                self.toolkit.add_arc(place_id, target_id)
                has_incoming[target_id] = True

        extra_start_nodes = set()
        extra_end_nodes = set()
        for node in data.nodes_to_draw:
            node_id = str(node)
            if not has_incoming.get(node_id):
                self.toolkit.add_arc(start_place, node_id)
                extra_start_nodes.add(node)
            if not has_outgoing.get(node_id):
                self.toolkit.add_arc(node_id, end_place)
                extra_end_nodes.add(node)

        self.toolkit.finalize_net(net)

        add_petri_net_to_graph(
            graph,
            net,
            data.nodes_to_draw,
            data.node_stats_map,
            data.filtered_appearance_freqs,
            logger=logger,
        )

        return graph, net, extra_start_nodes, extra_end_nodes

    def build_genetic_graph(self, data: GeneticPetriNetData, logger=None) -> tuple[PetriNetGraph, dict]:
        graph = PetriNetGraph()
        graph.add_start_node()
        graph.add_end_node()

        petri_net = self._build_from_genetic_individual(data.individual, data.start_nodes)
        data.individual["_petri_net"] = petri_net

        visible_labels = [act for act in data.individual.get("activities", []) if act in data.filtered_events]

        add_petri_net_to_graph(
            graph,
            petri_net,
            visible_labels,
            data.node_stats_map,
            data.filtered_appearance_freqs,
            logger=logger,
        )

        return graph, petri_net

    def build_petri_net_for_individual(self, individual: dict, start_nodes: set[str]) -> dict:
        """Net creation for the simulation step without building a graph."""
        return self._build_from_genetic_individual(individual, start_nodes)

    def _build_from_genetic_individual(self, individual: dict, start_nodes: set[str]) -> dict:

        net, start_place, end_place = self.toolkit.create_base_net()

        # Register all visible activities as transitions
        for act in individual['activities']:
            self.toolkit.register_transition(act, visible=True, label=str(act))

        # Initialize helper structures for mapping input/output connections
        pred_to_input_place: dict[tuple[str, str], str] = {}
        activity_input_places: dict[str, set[str]] = {}

        inputs = individual.get('I', {})
        outputs = individual.get('O', {})

        # Create input places for each input subset
        for act in individual['activities']:
            subsets = inputs.get(act) or []

            # Case 1: No input subsets
            if not subsets:
                net['empty_input_activities'].add(act)
                self.toolkit.ensure_input_place(
                    act,
                    "Start",
                    pred_to_input_place,
                    activity_input_places,
                    subset=set(),
                )
                continue
            
            # Case 2: Iterate over each input subset
            for idx, subset in enumerate(subsets):
                if not subset:
                    # Empty input subset (start candidate)
                    net['empty_input_activities'].add(act)
                    self.toolkit.ensure_input_place(
                        act,
                        "Start",
                        pred_to_input_place,
                        activity_input_places,
                        subset=set(),
                    )
                    continue

                # Normal input subset: create corresponding input place
                place_id = f"pi_{act}_{idx}_{'-'.join(sorted(subset))}"
                if place_id not in net['places']:
                    self.toolkit.register_place(place_id)
                    self.toolkit.add_arc(place_id, act)
                    activity_input_places.setdefault(act, set()).add(place_id)

                # Store mapping for later lookups
                net['input_subset_map'][place_id] = {'activity': act, 'subset': set(subset)}
                # Remember which input place connects a predecessor and successor
                for pred in subset:
                    pred_to_input_place[(pred, act)] = place_id
                    
        # Initialize counter for invisible transitions (τ)
        tau_counter = itertools.count()

        # Build output places and connect via silent transitions
        for act in individual['activities']:
            out_sets = outputs.get(act) or []

            # Case 1: No output sets -> connect to end place
            if not out_sets:
                place_id = f"po_{act}_sink"
                self.toolkit.register_place(place_id)
                self.toolkit.add_arc(act, place_id)

                tau_id = f"tau_{next(tau_counter)}"
                self.toolkit.register_transition(tau_id, visible=False)
                self.toolkit.add_arc(place_id, tau_id)
                self.toolkit.add_arc(tau_id, end_place)
                continue

            # Case 2: Iterate over each output subset
            for idx, out_set in enumerate(out_sets):
                if not out_set:
                    # Empty output set -> sink transition to end
                    place_id = f"po_{act}_sink_{idx}"
                    self.toolkit.register_place(place_id)
                    self.toolkit.add_arc(act, place_id)

                    tau_id = f"tau_{next(tau_counter)}"
                    self.toolkit.register_transition(tau_id, visible=False)
                    self.toolkit.add_arc(place_id, tau_id)
                    self.toolkit.add_arc(tau_id, end_place)
                    continue
                
                # Normal output subset -> connect to successor input places
                place_id = f"po_{act}_{idx}_{'-'.join(sorted(out_set))}"
                if place_id not in net['places']:
                    self.toolkit.register_place(place_id)
                self.toolkit.add_arc(act, place_id)

                for succ in out_set:
                    # Find the input place for successor or create it if needed
                    target_place = pred_to_input_place.get((act, succ))
                    if target_place is None:
                        target_place = self.toolkit.ensure_input_place(
                            succ,
                            act,
                            pred_to_input_place,
                            activity_input_places,
                            subset={act},
                        )
                        
                    # Create invisible τ-transition between po_place and pi_place
                    tau_id = f"tau_{next(tau_counter)}"
                    self.toolkit.register_transition(tau_id, visible=False)
                    self.toolkit.add_arc(place_id, tau_id)
                    self.toolkit.add_arc(tau_id, target_place)

        # Connect Start place to true start activities
        for act in individual['activities']:
            if act not in start_nodes:
                continue

            # Ensure a valid input place for the starting activity
            target_place = self.toolkit.ensure_input_place(
                act,
                "Start",
                pred_to_input_place,
                activity_input_places,
            )

            net['start_buffer_places'].add(target_place)

            for place_id, meta in net['input_subset_map'].items():
                if meta.get('activity') == act:
                    subset = meta.get('subset') or set()
                    if subset == {act}:
                        net['initial_marking'][place_id] = net['initial_marking'].get(place_id, 0) + 1
                        net['start_buffer_places'].add(place_id)

            # Create silent from start_place → activity input place
            tau_id = f"tau_{next(tau_counter)}"
            self.toolkit.register_transition(tau_id, visible=False)
            self.toolkit.add_arc(start_place, tau_id)
            self.toolkit.add_arc(tau_id, target_place)

        self.toolkit.finalize_net(net)
        return net
