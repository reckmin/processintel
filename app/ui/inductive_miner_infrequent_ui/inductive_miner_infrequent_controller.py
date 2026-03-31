import streamlit as st

from app.mining_algorithms.inductive_mining_infrequent import InductiveMiningInfrequent
from app.ui.inductive_miner_infrequent_ui.inductive_miner_infrequent_view import (
    InductiveMinerInfrequentView,
)
from app.ui.inductive_miner_ui.inductive_miner_controller import (
    InductiveMinerController,
)


class InductiveMinerInfrequentController(InductiveMinerController):
    """Controller for the Inductive Miner Infrequent algorithm."""

    def __init__(
        self, views=None, mining_model_class=None, dataframe_transformations=None
    ):
        """Initializes the controller for the Inductive Miner Infrequent algorithm.

        Parameters
        ----------
        views : List[BaseAlgorithmView] | BaseAlgorithmView, optional
            The views for the IMf algorithm. If None is passed, the default view is used, by default None
        mining_model_class : MiningInterface Class, optional
            The mining model class for the algorithm. If None is passed, the default model class is used, by default None
        dataframe_transformations : DataframeTransformations, optional
            The class for the dataframe transformations. If None is passed, a new instance is created, by default None
        """
        self.noise_threshold = 0.2

        if views is None:
            views = [InductiveMinerInfrequentView()]

        if mining_model_class is None:
            mining_model_class = InductiveMiningInfrequent
        super().__init__(views, mining_model_class, dataframe_transformations)

    def get_page_title(self) -> str:
        """Returns the page title.

        Returns
        -------
        str
            The page title.
        """
        return "Inductive Mining Infrequent"

    def process_algorithm_parameters(self):
        """Processes the algorithm parameters from the session state. The parameters are set to the instance variables.
        If the parameters are not set in the session state, the default values are used.
        """
        super().process_algorithm_parameters()

        if "noise_threshold" not in st.session_state:
            st.session_state.noise_threshold = self.noise_threshold
        self.noise_threshold = st.session_state.noise_threshold

    def perform_mining(self):
        """Performs the mining of the algorithm."""

        super().perform_mining(
            noise_threshold=self.noise_threshold,
        )

    def have_parameters_changed(self) -> bool:
        """Checks if the algorithm parameters have changed.

        Returns
        -------
        bool
            True if the algorithm parameters have changed, False otherwise.
        """
        return (
            super().have_parameters_changed()
            or getattr(self.mining_model, "noise_threshold", 0.2)
            != self.noise_threshold
        )

    def get_sidebar_values(self) -> dict[str, tuple[int | float, int | float]]:
        """Returns the sidebar values for the mining algorithm.

        Returns
        -------
        dict[str, tuple[int | float, int | float]]
            A dictionary containing the minimum and maximum values for the sidebar sliders.
            The keys of the dictionary are equal to the keys of the sliders.
        """
        sidebar_values = super().get_sidebar_values()
        sidebar_values.update(
            {
                "noise_threshold": (0.0, 1.0),
            }
        )

        return sidebar_values
