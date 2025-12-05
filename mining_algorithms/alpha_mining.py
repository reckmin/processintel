import itertools

from graphs.visualization import PetriNetGraph
from graphs.petri_net import PetriNetToolkit, add_petri_net_to_graph
from logger import get_logger
from mining_algorithms.base_mining import BaseMining


class AlphaMining(BaseMining):
    def __init__(self, log):
        super().__init__(log)
        self.logger = get_logger("AlphaMining")
        self.petri_toolkit = PetriNetToolkit()
        self.petri_net = None

        self._calculate_filtered_model_state()

    # This implementation follows the steps outlined in the lecture by Professor Wil van der Aalst on process mining.
    # The lecture video can be found at: https://www.youtube.com/watch?v=ATBEEEDxHTQ
    # Credit for the algorithm and methodology goes to Professor Wil van der Aalst.

    ####################################################################################################################
    # ALPHA MINER ALGORITHM IMPLEMENTATION BEGIN

    # step 1
    # each activity in cases corresponds to a transition in sigma(cases)
    # returns list converted to set to avoid duplicates
    # -> moved to BaseMining

    # step 2
    # the set of start activities - that is, the first element of each trace
    # returns list converted to set to avoid duplicates
    # -> moved to BaseMining

    # step 3
    # the set of end activities - that is, elements that appear last in trace
    # returns list converted to set to avoid duplicates
    # -> moved to BaseMining

    # step 4
    # Find pairs (A,B) of sets of activities such that every element a∈B and every element b∈B are causally related,
    # (i.e., a->L b), all  elements in A are independent (a1#La2), and all elements in B are independent (b1#Lb2)
    # returns set

    def generate_set_xl(self, unique_events, choice, causality):
        xl_set = []

        subsets = itertools.chain.from_iterable(
            itertools.combinations(unique_events, r) for r in range(1, len(unique_events) + 1))
        subsets_in_choice = [_set for _set in subsets if self.__is_set_in_choice(_set, choice)]
        for a, b in itertools.product(subsets_in_choice, subsets_in_choice):
            if self.__is_set_in_causality((a, b), causality):
                xl_set.append((a, b))

        return set(xl_set)

    # step 5
    # Delete from set XL all pairs (A,B) that are not maximal
    # returns set

    def generate_set_yl(self, xl_set, parallel):
        # create a yl set the superior of xl_set, containing the maximum
        yl_set = xl_set
        s_all = itertools.combinations(yl_set, 2)

        # generate maximum set
        for pair in s_all:
            if self.__is_subset(pair[0], pair[1]):
                yl_set.discard(pair[0])
            elif self.__is_subset(pair[1], pair[0]):
                yl_set.discard(pair[1])

        # remove self-loops
        # e.g. if (a,b),(b,c) in YL, and (b,b) in Parallel, then we need to remove (a,b),(b,c)
        # (a,b) is equal to (a,bb), also b||b, thus a and bb cannot make a pair, only "#" relations can.
        self_loop = set()
        for pair in parallel:
            if pair == pair[::-1]:  # if we found pairs like (b,b), add b into self-loop sets
                self_loop.add(pair[0])

        # define a set of to be deleted sets and remove them from yl_set
        to_be_deleted = set()
        for pair in yl_set:
            if self.__contains(pair, self_loop):
                to_be_deleted.add(pair)
        for pair in to_be_deleted:
            yl_set.discard(pair)
        return yl_set

    # Step 6
    def generate_graph(self, spm_threshold, node_freq_threshold_normalized, node_freq_threshold_absolute):
        self.graph = PetriNetGraph()
        self.graph.add_start_node()
        self.graph.add_end_node()

        self.spm_threshold = spm_threshold
        self.node_freq_threshold_normalized = node_freq_threshold_normalized
        self.node_freq_threshold_absolute = node_freq_threshold_absolute

        self.recalculate_model_filters()

        if not self.filtered_events:
            self.graph.create_edge("Start", "End")
            self.petri_net = None
            return

        self._calculate_filtered_model_state()

        node_stats_map = {stat["node"]: stat for stat in self.get_node_statistics()}

        nodes_to_draw = self.__events_to_draw().union(
            self.start_nodes.intersection(self.filtered_events),
            self.end_nodes.intersection(self.filtered_events)
        )
        if not nodes_to_draw:
            nodes_to_draw = set(self.filtered_events)

        petri_net, start_place, end_place = self.petri_toolkit.create_base_net()
        place_counter = itertools.count()

        for node in nodes_to_draw:
            node_id = str(node)
            self.petri_toolkit.register_transition(node_id, visible=True, label=node_id)

        has_incoming = {str(node): False for node in nodes_to_draw}
        has_outgoing = {str(node): False for node in nodes_to_draw}

        for node in self.start_nodes.intersection(nodes_to_draw):
            node_id = str(node)
            self.petri_toolkit.add_arc(start_place, node_id)
            has_incoming[node_id] = True

        for node in self.end_nodes.intersection(nodes_to_draw):
            node_id = str(node)
            self.petri_toolkit.add_arc(node_id, end_place)
            has_outgoing[node_id] = True

        for _set in self.yl_set:
            if len(_set) != 2:
                continue

            A, B = _set
            valid_sources = [a for a in A if a in nodes_to_draw and any(self.filter_edge(a, b) for b in B)]
            valid_targets = [b for b in B if b in nodes_to_draw and any(self.filter_edge(a, b) for a in A)]

            if not valid_sources or not valid_targets:
                continue

            place_id = f"p_alpha_{next(place_counter)}"
            self.petri_toolkit.register_place(place_id)

            for source in valid_sources:
                source_id = str(source)
                self.petri_toolkit.add_arc(source_id, place_id)
                has_outgoing[source_id] = True

            for target in valid_targets:
                target_id = str(target)
                self.petri_toolkit.add_arc(place_id, target_id)
                has_incoming[target_id] = True

        extra_start_nodes = set()
        extra_end_nodes = set()
        for node in nodes_to_draw:
            node_id = str(node)
            if not has_incoming.get(node_id):
                self.petri_toolkit.add_arc(start_place, node_id)
                extra_start_nodes.add(node)
            if not has_outgoing.get(node_id):
                self.petri_toolkit.add_arc(node_id, end_place)
                extra_end_nodes.add(node)

        self.start_nodes.update(extra_start_nodes)
        self.end_nodes.update(extra_end_nodes)

        self.petri_toolkit.finalize_net(petri_net)
        self.petri_net = petri_net

        add_petri_net_to_graph(
            self.graph,
            petri_net,
            nodes_to_draw,
            node_stats_map,
            self.filtered_appearance_freqs,
            logger=self.logger,
        )

    # ALPHA MINER ALGORITHM IMPLEMENTATION END
    ####################################################################################################################

    ####################################################################################################################
    # ALPHA MINER ALGORITHM ESSENTIALS BEGIN

    # essential for alpha algorithm: finding direct succession, together with causality, parallel and choice
    # noted with >, for example a > b, b > c, c > e in a process ['a', 'b', 'c', 'e']
    # returns list converted to set to avoid duplicates
    def _calculate_direct_succession(self):
        direct_succession = []
        for case in self.node_frequency_filtered_log:
            for i in range(len(case) - 1):
                x = case[i]
                y = case[i + 1]
                direct_succession.append((x, y))
        return set(direct_succession)

    # essential for alpha algorithm: finding causality, together with direct succession, parallel and choice
    # noted with ->, for example a -> b, b -> c, but not b -> b in a process ['a', 'b', 'b', 'c']
    # returns list converted to set to avoid duplicates
    @staticmethod
    def _calculate_causality(direct_succession):
        causality = []
        for pair in direct_succession:
            pair_reversed = (pair[1], pair[0])
            if pair_reversed not in direct_succession:
                pair_not_reversed = (pair[0], pair[1])
                causality.append(pair_not_reversed)
        return set(causality)

    # essential for alpha algorithm: finding parallels, together with direct succession, causality and choice
    # noted with ||, for example b || b in a process ['a', 'b', 'b', 'c']
    # returns list converted to set to avoid duplicates
    @staticmethod
    def _calculate_parallel(direct_succession):
        parallel = []
        for pair in direct_succession:
            pair_reversed = (pair[1], pair[0])
            if pair_reversed in direct_succession:
                pair_not_reversed = (pair[0], pair[1])
                parallel.append(pair_not_reversed)
        return set(parallel)

    # essential for alpha algorithm: finding choice, together with direct succession, causality and parallel
    # noted with #, for example 'a # c', 'c # a' in a process ['a', 'b', 'b', 'c']
    # returns list converted to set to avoid duplicates
    @staticmethod
    def _calculate_choice(unique_events, causality, parallel):
        choice = []
        for event1 in unique_events:
            for event2 in unique_events:
                if (event1 != event2) and ((event1, event2) not in causality) and (
                        (event2, event1) not in causality) and ((event1, event2) not in parallel):
                    choice.append((event1, event2))
        return set(choice)

    def generate_footprint(self):
        footprint = ["All transitions: {}".format(self.events),
                     "Direct succession: {}".format(self.direct_succession_set),
                     "Causality: {}".format(self.causality_set),
                     "Parallel: {}".format(self.parallel_set), "Choice: {}".format(self.choice_set)]
        return '\n'.join(footprint)

    # ALPHA MINER ALGORITHM ESSENTIALS END
    ####################################################################################################################

    ####################################################################################################################
    # ALPHA MINER ALGORITHM HELPER METHODS BEGIN

    def create_safe_ingoing_edge(self, from_node, to_connector):
        if not self.graph.contains_edge(from_node, to_connector):
            self.graph.create_edge(from_node, to_connector)

    def create_safe_outgoing_edge(self, from_connector, to_node, real_source):
        if not self.graph.contains_edge(from_connector, to_node):
            self.graph.create_edge(from_connector, to_node)

    def create_safe_node(self, node_id):
        if not self.graph.contains_node(node_id):
            self.graph.add_empty_circle(node_id)

    # searches for a given set if the given set is found in choice set
    # returns boolean
    @staticmethod
    def __is_set_in_choice(_set, choice):
        if len(_set) == 1:
            return True
        else:
            for i in range(len(_set)):
                for j in range(i + 1, len(_set)):
                    if (_set[i], _set[j]) not in choice:
                        return False
            return True

    # searches for a given set if the given set is found in causality set
    # returns boolean
    @staticmethod
    def __is_set_in_causality(_set, causality):
        a, b = _set[0], _set[1]
        all_possibilities = itertools.product(a, b)
        for pair in all_possibilities:
            if pair not in causality:
                return False
        return True

    # searches for a given set if the given set is found in parallel set
    # returns boolean
    @staticmethod
    def __is_set_in_parallel(_set, parallel):
        a, b = _set[0], _set[1]
        all_possibilities = itertools.product(a, b)
        for pair in all_possibilities:
            if pair not in parallel:
                return False
        return True

    # check if the first set in 'a' is a subset of the first set in 'b'
    # and if the second set in 'a' is a subset of the second set in 'b'
    # Return True if both conditions are True, otherwise return False
    @staticmethod
    def __is_subset(a, b):
        first_subset = set(a[0]).issubset(b[0])
        second_subset = set(a[1]).issubset(b[1])
        return first_subset and second_subset

    # check if a set in b equals to a set in a
    @staticmethod
    def __contains(a, b):
        for i in a:
            for j in b:
                if j == i[0]:
                    return True
        return False

    # defines unique events that are not self loop which are needed to be drawn
    def __events_to_draw(self):
        events_to_draw = []
        for _set in self.yl_set:
            for event in _set:
                for node in event:
                    events_to_draw.append(node)
        return set(events_to_draw)
    def _calculate_filtered_model_state(self):
        self.direct_succession_set = self._calculate_direct_succession()
        self.causality_set = self._calculate_causality(self.direct_succession_set)
        self.parallel_set = self._calculate_parallel(self.direct_succession_set)
        self.choice_set = self._calculate_choice(self.filtered_events, self.causality_set, self.parallel_set)
        self.xl_set = self.generate_set_xl(self.filtered_events, self.choice_set, self.causality_set)
        self.yl_set = self.generate_set_yl(self.xl_set, self.parallel_set)
        self.footprint = self.generate_footprint()

    # ALPHA MINER ALGORITHM HELPER METHODS END
    ####################################################################################################################
