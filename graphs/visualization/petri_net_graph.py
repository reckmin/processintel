from graphs.visualization.base_graph import BaseGraph


class PetriNetGraph(BaseGraph):
    """
    Graph representation for Petri net visualizations.
    """

    def __init__(self) -> None:
        super().__init__(rankdir="LR")
        self.adjacency = {}
        self.gateway_info: dict[str, dict] = {}

    def add_event(
            self,
            title: str,
            spm: float,
            normalized_frequency: float,
            absolute_frequency: int,
            **event_data,
    ) -> None:
        """Add an event to the graph.

        Parameters
        ----------
        title : str
            name of the event
        spm : float
            spm value of the event
        normalized_frequency : float
            normalized frequency of the event
        absolute_frequency : int
            absolute frequency of the event
        **event_data
            additional data for the event
        """
        event_data["SPM value"] = spm
        event_data["Frequency *(absolute)*"] = absolute_frequency
        event_data["Frequency *(normalized)*"] = normalized_frequency
        label = f'<{title}<br/><font color="red">{absolute_frequency}</font>>'
        super().add_node(
            id=title,
            label=label,
            data=event_data,
            shape="circle",
            style="filled",
            fillcolor="#FDFFF5",
        )

    def create_edge(self, source: str, destination: str, weight: int = None, **edge_data) -> None:
        """Create an edge between two nodes.

        Parameters
        ----------
        source : str
            source node id
        destination : str
            destination node id
        weight : int, optional
            weight of the edge
        **edge_data
            additional data for the edge
        """
        self.adjacency.setdefault(source, []).append(destination)
        edge_data = {key: str(value) if isinstance(value, (int, float)) else value for key, value in edge_data.items()}
        super().add_edge(source, destination, weight, data=edge_data)

    def add_place(self, place_id: str, label: str = " ", data: dict | None = None, **node_attributes) -> None:
        """Add a place node to the graph.

        Parameters
        ----------
        place_id : str
            ID for the place node
        """
        node_attributes.setdefault("shape", "circle")
        node_attributes.setdefault("style", "filled")
        node_attributes.setdefault("fillcolor", "#E1E1E1")
        super().add_node(
            id=place_id,
            label=label,
            data=data,
            **node_attributes,
        )

    def add_silent_transition(self, transition_id: str, label: str = "silent", data: dict | None = None,
                              **node_attributes) -> None:
        """Add a silent (tau) transition to the graph."""
        node_attributes.setdefault("shape", "box")
        node_attributes.setdefault("style", "filled")
        node_attributes.setdefault("fillcolor", "#EDEDED")
        super().add_node(
            id=transition_id,
            label=label,
            data=data,
            **node_attributes,
        )

    def node_to_string(self, id: str) -> tuple[str, str]:
        """Return a minimal description for nodes, simplifying gateway output."""
        gateway = self.gateway_info.get(id, {})
        if gateway:
            gateway_type = gateway.get("type", "").lower()
            title = ""
            description = ""
            role = gateway.get("role", "").lower()

            if gateway_type == "xor":
                title = "Exclusive Gateway"
                description = "**Exclusive Gateway**\nThe Exclusive Gateway represents a decision point in the process flow."
            elif gateway_type in ("and", "par", "parallel"):
                title = "Parallel Gateway"
                description = "**Parallel Gateway**\nThe Parallel Gateway represents synchronization in the process flow."
            else:
                return super().node_to_string(id)

            if role == "split":
                title = title.replace("Gateway", "Start Gate")
            elif role == "join":
                title = title.replace("Gateway", "End Gate")
            return title, description


        node = self.get_node(id)
        node_label = node.get_label().strip().lower() if node else ""
        node_id = str(id).lower()
        if node_id.startswith("tau") or node_label == "silent" or node_label.startswith("silent "):
            return "Silent Transition", "**Silent Transition**\nRepresents an invisible routing step in the Petri net."

        return super().node_to_string(id)
