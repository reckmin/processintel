import streamlit as st

from app.components.number_input_slider import number_input_slider
from app.ui.inductive_miner_ui.inductive_miner_view import InductiveMinerView


class InductiveMinerInfrequentView(InductiveMinerView):
    """View for the Inductive Miner Infrequent algorithm."""

    def render_log_filter_extensions(
        self, sidebar_values: dict[str, tuple[int | float, int | float]]
    ) -> None:
        """Renders the sidebar for the mining algorithm.

        Parameters
        ----------
        sidebar_values : dict[str, tuple[int  |  float, int  |  float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        super().render_log_filter_extensions(sidebar_values)

        st.write("### Noise Filtering")

        number_input_slider(
            label="Noise Threshold",
            min_value=sidebar_values["noise_threshold"][0],
            max_value=sidebar_values["noise_threshold"][1],
            key="noise_threshold",
            help="""Determines which directly-follows relations are considered noise and filtered out.
            Relations with frequency < threshold × max_relation_frequency will be ignored.""",
        )
        with st.expander("Guidance"):
            st.markdown(
                """
                        - **[0.0]**: No noise filtering 
                        - **[0.1-0.2]**: Light noise filtering 
                        - **[0.2-0.4]**: Moderate noise filtering
                        - **[above 0.5]**: Aggressive noise filtering """
            )
