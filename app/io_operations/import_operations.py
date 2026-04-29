import base64
import xml.etree.ElementTree as ET
import pandas as pd
import pickle
from streamlit.runtime.uploaded_file_manager import UploadedFile


class ImportOperations:

    def read_csv(
        self, file_path: str | UploadedFile, delimiter: str = ","
    ) -> pd.DataFrame:
        """Reads a csv file and returns a pandas DataFrame

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the csv file or the uploaded file object
        delimiter : str, optional
            The delimiter used in the csv file, by default ","

        Returns
        -------
        pd.DataFrame
            The csv file as a pandas DataFrame
        """
        df = pd.read_csv(file_path, delimiter=delimiter, low_memory=False)
        return df

    def read_img(self, file_path: str) -> str:
        """Reads an image file and returns it as a base64 string. This is used to display the image in the HTML

        Parameters
        ----------
        file_path : str
            Path to the image file

        Returns
        -------
        str
            The image file as a base64 string
        """
        with open(file_path, "rb") as file:
            png = file.read()
        # https://pmbaumgartner.github.io/streamlitopedia/sizing-and-images.html
        # https://discuss.streamlit.io/t/how-to-show-local-gif-image/3408/2
        # Convert the image to a base64 string to be able to display it in the HTML
        png_base64 = base64.b64encode(png).decode("utf-8")
        return png_base64

    def read_model(self, file_path: str | UploadedFile) -> object:
        """Reads a model from a pickle file and returns the model object

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the pickle file or the uploaded file object

        Returns
        -------
        object
            The model object
        """
        if isinstance(file_path, UploadedFile):
            model = pickle.load(file_path)
        else:
            with open(file_path, "rb") as file:
                model = pickle.load(file)
        return model

    def read_file(self, file_path: str | UploadedFile) -> str:
        """Reads a file and returns the content as a string. This is used to display the content of the file in the UI

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the file or the uploaded file object

        Returns
        -------
        str
            The content of the file as a string
        """
        if isinstance(file_path, UploadedFile):
            return file_path.read().decode("utf-8")

        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            return file.read()

    def read_file_binary(self, file_path: str) -> bytes:
        """Reads a file and returns the content as bytes. This is used to download the file

        Parameters
        ----------
        file_path : str
            Path to the file.

        Returns
        -------
        bytes
            The content of the file as bytes.
        """
        with open(file_path, "rb") as file:
            return file.read()

    def read_line(self, file_path: str | UploadedFile) -> str:
        """Reads the first line of a file and returns it as a string. This is used to detect the delimiter of a csv file

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the file or the uploaded file object

        Returns
        -------
        str
            The first line of the file as a string
        """
        if isinstance(file_path, UploadedFile):
            line = file_path.readline().decode("utf-8")
            # reset the file pointer to the beginning of the file
            file_path.seek(0)
            return line

        with open(file_path, "r") as file:
            return file.readline()

    def read_xes(self, file_path: str | UploadedFile) -> ET.ElementTree:
        """Reads an XES file and returns an ElementTree.

        Parameters
        ----------
        file_path : str | UploadedFile
            Path to the XES file or the uploaded file object.

        Returns
        -------
        ET.ElementTree
            The parsed XES XML tree.
        """

        if isinstance(file_path, UploadedFile):
            file_path.seek(0)
            return ET.parse(file_path)

        return ET.parse(file_path)
