import streamlit as st

from app.components.buttons import navigation_button
from app.config import algorithm_mappings
from app.ui.base_ui.base_view import BaseView
from app.components.footer import footer


class HomeView(BaseView):
    """View for the Home page."""

    def create_layout(self):
        """Creates the layout for the Home page."""
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 3, 1])

    def display_intro(self):
        """Displays the introduction text for the Home page."""
        with self.content_column:
            st.title("ProcessIntel")
            st.write(
                "Welcome to ProcessIntel the transparent open-source application for process mining, event log visualization, and interactive exploration of process models."
            )
            st.write(
                """ProcessIntel enables you to:
- import and transform event logs
- discover process models 
  - by using state-of-the-art process mining algorithms 
  - by setting many parameters
  - and getting transparent explanations how the process models were discovered
- to explore results through an interactive graph-based interface
- export
  - process models
  - your workspace
  """
            )

    def display_file_upload(self, file_types: list[str]):
        """Displays the file upload component.

        Parameters
        ----------
        file_types : list[str]
            The allowed file types.
        """
        with self.content_column:
            st.file_uploader(
                "Upload a file",
                type=file_types,
                accept_multiple_files=False,
                key="uploaded_file",
            )

    def display_model_import(self, model):
        """Displays the model import component. A dropdown is displayed to select the mining algorithm.

        Parameters
        ----------
        model : MiningInterface
            The mining model to be imported.
        """
        with self.content_column:
            algorithm_col, _, button_column = st.columns([2, 2, 1])
            with algorithm_col:
                selection = st.selectbox(
                    "Mining Algorthm", list(algorithm_mappings.keys())
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Import Model",
                    route="Algorithm",
                    width="stretch",
                    beforeNavigate=self.controller.set_model_and_algorithm,
                    args=(model, algorithm_mappings[selection]),
                )

    def display_df_import(self, detected_delimiter):
        """Displays the dataframe import component. A text input is displayed to enter the delimiter.

        Parameters
        ----------
        detected_delimiter : str
            The detected delimiter of the CSV file.
        """
        with self.content_column:
            delimiter_col, _, button_column = st.columns([1, 3, 1])

            with delimiter_col:
                delimiter = st.text_input(
                    "Delimiter", value=detected_delimiter, key="delimiter", max_chars=1
                )

            with button_column:
                st.write("")
                navigation_button(
                    label="Mine from File",
                    route="ColumnSelection",
                    width="stretch",
                    beforeNavigate=self.controller.set_df,
                    args=(delimiter,),
                )

    def display_disclaimer(self):
        if False:
            with self.content_column:
                st.write(
                    """  
**Disclaimer**  
ProcessIntel is hosted and operated as a service by SWISDATA <https://swisdata.eu>  
The application was developed by several authors, including developers from SWISDATA, but mainly as part of bachelor's theses at the University of Vienna under the supervision of Dr. Marian LUX.

The source code for self hosting and further development is available at the following Link: <https://code.swisdata.eu/SWISDATA/ProcessIntel>
    """
                )

        footer(
            """<div>
                <strong>Disclaimer</strong><br>
                ProcessIntel is hosted and operated as a service by
                <a href="https://swisdata.eu" target="_blank">SWISDATA</a>.<br>
                The application was developed by several authors, including developers from SWISDATA,
                but mainly as part of bachelor's theses at the University of Vienna under the supervision
                of Dr. Marian Lux.<br>
                Source code for self-hosting and further development:
                <a href="https://code.swisdata.eu/SWISDATA/ProcessIntel" target="_blank">
                    https://code.swisdata.eu/SWISDATA/ProcessIntel
                </a>
            </div>"""
        )
