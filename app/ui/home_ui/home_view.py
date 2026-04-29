import base64
import os
import streamlit as st


from app.components.buttons import navigation_button
from app.config import algorithm_mappings, ASSETS_DIR
from app.ui.base_ui.base_view import BaseView
from app.components.footer import footer


@st.cache_data
def load_svg_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class HomeView(BaseView):
    """View for the Home page."""

    def create_layout(self):
        """Creates the layout for the Home page."""
        super().create_layout()
        _, self.content_column, _ = st.columns([1, 3, 1])

    def display_intro(self):
        """Displays the introduction text for the Home page."""
        with self.content_column:
            svg_base64 = load_svg_base64(
                os.path.join(ASSETS_DIR, "process_intel_logo.svg")
            )
            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:10px;">
                    <h1 style="margin:0;">ProcessIntel</h1>
                    <img
                        src="data:image/svg+xml;base64,{svg_base64}"
                        width="60"
                        style="height:auto;"
                    />
                </div>
            """,
                unsafe_allow_html=True,
            )

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

    def display_df_import(self, detected_delimiter: str, show_delimiter: bool = True):
        """Displays the dataframe import component. A text input is displayed to enter
        the delimiter.

        Parameters
        ----------
        detected_delimiter : str
            The detected delimiter of the CSV file. For file types that do not use a delimeter,
            an emtpy string is passed.
        show_delimiter : bool, optional
            Whether to display the delimiter input field, by default True.
        """
        with self.content_column:
            delimiter_col, _, button_column = st.columns([1, 3, 1])
            delimiter = ""

            if show_delimiter:
                with delimiter_col:
                    delimiter = st.text_input(
                        "Delimiter",
                        value=detected_delimiter,
                        key="delimiter",
                        max_chars=1,
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
                </a> <br>
                ProcessIntel is provided "as is" and under the MIT License.<br>
                No liability is assumed for the correctness, completeness, or reliability of the software or the results it produces.<br>
                For questions or feedback, please contact us via:
                <a href="https://www.swisdata.eu/contact/" target="_blank">
                    https://www.swisdata.eu/contact/
                </a>
            </div>"""
        )
