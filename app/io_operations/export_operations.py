import os
import pickle
import tempfile
import pandas as pd
import streamlit as st
import xml.etree.ElementTree as ET

from app.graphs.visualization.base_graph import BaseGraph
from app.exceptions.io_exceptions import (
    UnsupportedFileTypeException,
    NotImplementedFileTypeException,
)
from app.exceptions.type_exceptions import InvalidTypeException


class ExportOperations:

    def __init__(self, supported_graph_export_formats=None):
        """Initializes the ExportOperations class.

        Parameters
        ----------
        supported_graph_export_formats : List[str], optional
            The supported graph export formats, by default None
        """
        if supported_graph_export_formats is None:
            from app.config import graph_export_formats

            supported_graph_export_formats = graph_export_formats

        self.graph_export_formats = supported_graph_export_formats

    def export_graph(
        self, graph: BaseGraph, filename: str, format: str = "png", dpi=96
    ) -> None:
        """Export a graph to a file.

        Parameters
        ----------
        graph : BaseGraph
            The graph to export
        filename : str
            The name of the file to export the graph to
        format : str, optional
            The format of the exported file, by default "png"
        dpi : int, optional
            The DPI of the exported file. Only considered if the format is png, by default 96

        Raises
        ------
        InvalidTypeException
            If graph is not an instance of BaseGraph
        UnsupportedFileTypeException
            If the export format is not supported
        NotImplementedFileTypeException
            If the export format is not implemented
        """

        if not isinstance(graph, BaseGraph):
            raise InvalidTypeException(BaseGraph, type(graph))

        if format not in self.graph_export_formats:
            raise UnsupportedFileTypeException(format)

        graphviz_graph = graph.get_graphviz_graph()
        export_format = format.lower()

        if export_format == "png":
            graphviz_graph.attr(dpi=str(dpi))
            graphviz_graph.render(filename, format=export_format, cleanup=True)
            graphviz_graph.attr(dpi="0")
        elif export_format in ["svg", "dot"]:
            graphviz_graph.render(filename, format=export_format, cleanup=True)
        else:
            raise NotImplementedFileTypeException(export_format)

    def export_model_to_file(self, model, filename: str) -> None:
        """Export a model to a file.

        Parameters
        ----------
        model : object
            The model to export
        filename : str
            The name of the file to export the model to
        """
        if not filename.endswith(".pickle"):
            filename += ".pickle"

        with open(filename, "wb") as file:
            pickle.dump(model, file)

    def export_model_to_bytes(self, model) -> bytes:
        """Export a model to bytes.

        Parameters
        ----------
        model : object
            The model to export

        Returns
        -------
        bytes
            The model as bytes
        """
        return pickle.dumps(model)

    def export_to_xes_bytes(self, xes_tree: ET.ElementTree) -> bytes:
        """Export xes_tree to XES format and return as bytes.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            The XES XML tree to export.

        Returns
        -------
        bytes
            The XES file as bytes.

        Raises
        ------
        InvalidTypeException
            If xes_tree is not an ElementTree
        """
        if not isinstance(xes_tree, ET.ElementTree):
            raise InvalidTypeException("ElementTree", type(xes_tree))

        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xes",
                dir=st.session_state.session_tmp_dir,
            ) as temp_file:
                temp_path = temp_file.name

            xes_tree.write(temp_path, encoding="utf-8", xml_declaration=True)

            with open(temp_path, "rb") as file:
                xes_bytes = file.read()

            os.unlink(temp_path)

            return xes_bytes
        except Exception as e:
            raise Exception(f"Failed to export to XES bytes: {str(e)}")

    def export_to_csv_data(self, df: pd.DataFrame, delimiter: str) -> str:
        """Export from dataframe to CSV text.

        Parameters
        ----------
        df : pd.DataFrame
            The dataframe to export.
        delimiter : str
            The parsed delimiter used in CSV file.

        Returns
        -------
        str
            The CSV file content as text.

        Raises
        ------
        InvalidTypeException
            If df is not a pandas DataFrame.
        """
        if not isinstance(df, pd.DataFrame):
            raise InvalidTypeException("pandas DataFrame", type(df))

        return df.to_csv(sep=delimiter, index=False)
