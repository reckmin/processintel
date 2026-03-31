from app.graphs.cuts import exclusive_cut, parallel_cut, sequence_cut, loop_cut
from app.graphs.dfg import DFG
from app.logger import get_logger

from app.logs.splits_imf import (
    exclusive_split_imf,
    is_empty_trace_frequent,
    parallel_split_imf,
    is_single_activity_frequent,
    loop_split_imf,
    sequence_split_imf,
)
from app.mining_algorithms.inductive_mining import InductiveMining


class InductiveMiningInfrequent(InductiveMining):
    """Generate a graph from a log using the Inductive Mining Infrequent algorithm (IMf)."""

    def __init__(self, log):
        """Constructor for the InductiveMiningInfrequent class.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log represented as a dictionary that maps traces to their frequencies.
        """

        super().__init__(log)
        self.logger = get_logger("InductiveMiningInfrequent")

        self.noise_threshold: float = 0.2
        self._last_noise_threshold: float = -1.0
        self._use_imf_filters: bool = False
        self.logger.info(
            "Initialized IMf (Inductive Miner - Infrequent) with paper-based algorithm"
        )

    def generate_graph(
        self,
        spm_threshold: float,
        node_freq_threshold_normalized: float,
        node_freq_threshold_absolute: int,
        traces_threshold: float = 0.0,
        use_petri_net: bool = False,
        noise_threshold: float = 0.2,
    ):
        """Generate a graph from the log using the Inductive Mining Infrequent algorithm.

        Parameters
        ----------
        spm_threshold : float
            The threshold for the SPM (Search Process Model) score.
        node_freq_threshold_normalized : float
            The threshold for the normalized frequency of nodes (events).
        node_freq_threshold_absolute : int
            The threshold for the absolute frequency of nodes (events).
        traces_threshold : float, optional
            The traces threshold for the filtering of the log., by default 0.0
        use_petri_net : bool, optional
            If True, renders a Petri net representation instead of the process tree view, by default False
        noise_threshold : float, optional
            Noise threshold for edge filtering (0.0 - 1.0)
            Recommended: 0.2 (20%), by default 0.2
        """
        self.noise_threshold = max(0.0, min(1.0, noise_threshold))

        return super().generate_graph(
            spm_threshold,
            node_freq_threshold_normalized,
            node_freq_threshold_absolute,
            traces_threshold,
            use_petri_net,
        )

    def inductive_mining(self, log):
        """Apply the IMf discovery procedure to the log.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        str or tuple
            Process tree node discovered from the log.
        """
        return self._inductive_mining_imf(log)

    def _inductive_mining_imf(self, log):
        """Discover a process tree from a log using the recursive IMf procedure.

        The method applies the Inductive Miner Infrequent in two phases.
        First, it tries the standard inductive mining steps without IMf filters.
        If no valid model can be found, it tries using IMf-specific filtering for
        base cases, cut detection, log splitting.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        str or tuple
            Process tree representation discovered from the log. Returns ``"tau"``,
            a single activity label, or a tuple representing an operator and its
            child nodes.

        Notes
        -----
        Algorithm:

        1. Check base cases without IMf filters.
        2. Try standard cut detection on the full DFG.
        3. If no valid result is found, enable IMf filters.
        4. Handle empty traces or retry cut detection on the filtered DFG.
        5. If no cut is found, return an IMf fall-through model.
        """
        if not log:
            return "tau"

        self._use_imf_filters = False

        tree = self._base_cases_imf(log)
        if tree:
            return tree

        if tuple() not in log:
            result = super().calculate_cut(log)

            if result:
                operator = result[0]
                sublogs = list(result[1:])
                return (
                    operator,
                    *[self._inductive_mining_imf(sublog) for sublog in sublogs],
                )

        self.logger.debug("Phase 1 failed - applying IMf filters")
        self._use_imf_filters = True

        if tuple() in log:
            return self._handle_empty_trace_imf(log)

        if self.noise_threshold > 0.0:
            if result := self._try_cuts_filtered(log):
                operator, sublogs = result
                self.logger.debug(
                    f"Phase 2 SUCCESS: {operator} cut found with filtering"
                )
                return (
                    operator,
                    *[self._inductive_mining_imf(sublog) for sublog in sublogs],
                )

        return self._fallthrough_imf(log)

    def _base_cases_imf(self, log):
        """Check whether the log matches an IMf base case.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        str or None
            ``"tau"`` for empty log or single empty trace, ``None`` if no base
            case applies and further recursive processing is required.
        """
        if not log:
            return "tau"

        if len(log) == 1:
            trace = list(log.keys())[0]

            # Empty trace
            if len(trace) == 0:
                return "tau"

            # Single activity in single trace
            if len(trace) == 1:
                return trace[0]

        # Check for single-activity log (may have multiple traces)
        log_alphabet = self.get_log_alphabet(log)

        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]

            # IMPORTANT: If empty traces exist, this is NOT a base case!
            # The empty traces need to be handled via XOR(tau, activity)
            # This is done in _handle_empty_trace_imf, not here
            if tuple() in log:
                return None  # Let the main algorithm handle empty traces

            # Apply IMf filter: check if single activity is appropriate
            if self._use_imf_filters:
                if is_single_activity_frequent(log, self.noise_threshold):
                    self.logger.debug(
                        f"Base case (IMf filter): single activity '{activity}'"
                    )
                    return activity
                else:
                    # Average occurrences too high - need loop model
                    self.logger.debug(
                        f"Base case (IMf filter): '{activity}' needs loop (avg > threshold)"
                    )
                    return None
            else:
                # Check if activity only occurs once per trace
                all_single = all(
                    trace.count(activity) == 1 for trace in log.keys() if trace
                )
                if all_single:
                    return activity

        return None

    def _handle_empty_trace_imf(self, log):
        """Handle empty trace with IMf filter.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        tuple or str or None
            Process tree node after handling empty traces. Returns either an
            XOR structure including ``"tau"``, a recursively discovered subtree,
            or ``None`` if no empty trace is present.
        """
        if tuple() not in log:
            return None

        if self._use_imf_filters and self.noise_threshold > 0.0:
            if is_empty_trace_frequent(log, self.noise_threshold):
                # Empty trace is frequent - model with XOR(tau, ...)
                self.logger.debug("Empty trace is frequent - using XOR(tau, ...)")
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return ("xor", "tau", self._inductive_mining_imf(log_without_empty))
            else:
                # Empty trace is infrequent - filter it out
                self.logger.debug(
                    "Empty trace is infrequent - filtering and continuing"
                )
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return self._inductive_mining_imf(log_without_empty)
        else:
            # Standard handling (no filter)
            log_without_empty = {k: v for k, v in log.items() if k != tuple()}
            return ("xor", "tau", self._inductive_mining_imf(log_without_empty))

    def _try_cuts_filtered(self, log):
        """Find a valid cut on a filtered DFG with IMf filtering.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        tuple or None
            A tuple containing the detected operator (``"xor"``, ``"seq"``,
            ``"par"``, or ``"loop"``) and the corresponding sublogs, or
            ``None`` if no valid cut is found.
        """
        self.logger.debug("ENTERED _try_cuts_filtered")
        if not log:
            return None

        try:
            filtered_dfg = self._create_filtered_dfg(log)

            if not filtered_dfg.get_nodes():
                self.logger.debug("Filtered DFG has no nodes")
                return None

            # Try cuts with IMf log splitting
            if partitions := exclusive_cut(filtered_dfg):
                sublogs = exclusive_split_imf(log, partitions)
                return ("xor", sublogs)

            if partitions := sequence_cut(filtered_dfg):
                sublogs = sequence_split_imf(log, partitions)
                return ("seq", sublogs)

            if partitions := parallel_cut(filtered_dfg):
                sublogs = parallel_split_imf(log, partitions)
                return ("par", sublogs)

            if partitions := loop_cut(filtered_dfg):
                sublogs = loop_split_imf(log, partitions)
                return ("loop", sublogs)

        except Exception as e:
            self.logger.error(f"Error in filtered cut detection: {e}")

        return None

    def _fallthrough_imf(self, log):
        """Create a flower model if no valid cut is found.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        tuple or str
            Process tree node representing the fall-through model. Returns
            either a loop structure (flower model) or a single activity.
        """
        log_alphabet = self.get_log_alphabet(log)
        # Handle empty trace
        if tuple() in log:
            if self._use_imf_filters:
                return self._handle_empty_trace_imf(log)
            else:
                log_without_empty = {k: v for k, v in log.items() if k != tuple()}
                return ("xor", "tau", self._inductive_mining_imf(log_without_empty))

        # Single activity with repetition -> loop
        if len(log_alphabet) == 1:
            activity = list(log_alphabet)[0]
            # Check if activity repeats in traces
            has_repetition = any(
                trace.count(activity) > 1 for trace in log.keys() if trace
            )
            if has_repetition:
                return ("loop", activity, "tau")
            else:
                return activity

        # Filter infrequent activities from flower model if IMf filters enabled
        if self._use_imf_filters and self.noise_threshold > 0.0:
            # Compute activity frequencies
            activity_freq: dict[str, int] = {}
            for trace, freq in log.items():
                for activity in trace:
                    activity_freq[activity] = activity_freq.get(activity, 0) + freq

            if activity_freq:
                max_freq = max(activity_freq.values())
                cutoff = max_freq * self.noise_threshold

                # Keep only frequent activities
                frequent_activities = {
                    act for act, freq in activity_freq.items() if freq >= cutoff
                }

                if frequent_activities and len(frequent_activities) < len(log_alphabet):
                    self.logger.debug(
                        f"IMf fallthrough: filtering {len(log_alphabet) - len(frequent_activities)} "
                        f"infrequent activities from flower model"
                    )
                    log_alphabet = frequent_activities

        # Flower model
        if len(log_alphabet) == 1:
            return ("loop", list(log_alphabet)[0], "tau")

        return ("loop", "tau", *sorted(log_alphabet))

    def _create_filtered_dfg(self, log) -> DFG:
        """Create filtered DFG by removing infrequent edges.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        DFG
           Directly-follows graph containing edges that satisfy
           the current noise threshold.
        """

        self.logger.debug("ENTERED _create_filtered_dfg")

        if not log:
            return DFG()

        # Compute edge frequencies
        edge_freq = self._compute_edge_frequencies(log)

        if not edge_freq:
            return DFG()

        # Calculate threshold
        max_freq = max(edge_freq.values())
        threshold = max_freq * self.noise_threshold

        self.logger.debug(f"Edge filtering: max={max_freq}, threshold={threshold:.2f}")

        # Identify frequent edges and connected nodes
        frequent_edges = []
        connected_nodes: set[str] = set()

        for (src, tgt), freq in edge_freq.items():
            if freq >= threshold:
                frequent_edges.append((src, tgt))
                connected_nodes.add(src)
                connected_nodes.add(tgt)

        filtered_dfg = DFG()

        for node in connected_nodes:
            filtered_dfg.add_node(node)

        for src, tgt in frequent_edges:
            filtered_dfg.add_edge(src, tgt)

        # Preserve start/end information
        self._preserve_start_end_nodes(filtered_dfg, log)

        self.logger.debug(
            f"Filtered DFG: {len(connected_nodes)} nodes, {len(frequent_edges)} edges "
            f"(filtered {len(edge_freq) - len(frequent_edges)} edges)"
        )

        return filtered_dfg

    def _compute_edge_frequencies(self, log) -> dict[tuple[str, str], int]:
        """Compute frequencies of directly-follows edges.

        Parameters
        ----------
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.

        Returns
        -------
        dict[tuple[str, str], int]
            Mapping of directly-follows edges to their frequencies.
        """
        edge_freq: dict[tuple[str, str], int] = {}

        for trace, freq in log.items():
            if len(trace) < 2:
                continue

            for i in range(len(trace) - 1):
                edge = (trace[i], trace[i + 1])
                edge_freq[edge] = edge_freq.get(edge, 0) + freq

        return edge_freq

    def _preserve_start_end_nodes(self, dfg: DFG, log: dict[tuple[str, ...], int]):
        """Preserve start and end node information in a filtered DFG.

        Parameters
        ----------
        dfg : DFG
            Directly-follows graph to update.
        log : dict[tuple[str, ...], int]
            Event log mapping traces to their frequencies.
        """
        try:
            if hasattr(dfg, "start_nodes") and hasattr(dfg, "end_nodes"):
                start_nodes = {trace[0] for trace in log.keys() if trace}
                end_nodes = {trace[-1] for trace in log.keys() if trace}

                # Only include nodes that are in the DFG
                dfg_nodes = set(dfg.get_nodes())
                dfg.start_nodes = start_nodes & dfg_nodes  # type: ignore
                dfg.end_nodes = end_nodes & dfg_nodes  # type: ignore

        except Exception as e:
            self.logger.debug(f"Could not preserve start/end nodes: {e}")
