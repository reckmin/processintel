import streamlit as st
import os
from app.config import ASSETS_DIR

st.set_page_config(
    page_title="ProcessIntel",
    page_icon=os.path.join(ASSETS_DIR, "process_intel_logo.svg"),
    layout="wide",
)

home = st.Page(
    "pages/main_app.py",
    title="ProcessIntel",
    default=True,
)
imprint = st.Page("pages/imprint.py", title="Imprint", url_path="imprint")
privacy = st.Page("pages/privacy.py", title="Privacy Policy", url_path="privacy")


pg = st.navigation([home, imprint, privacy], position="top")

st.html(
    """
    <style>
    html, body, [class*="st-"]:not([data-testid="stIconMaterial"]) {
        font-family: "Montserrat", sans-serif;
    }
    </style>
    """
)

if st.context.theme.type == "light":
    logo = "logo.svg"
else:
    logo = "logo_bright.svg"

st.logo(
    os.path.join(ASSETS_DIR, logo),
    size="large",
    link="https://www.swisdata.eu/",
)

pg.run()
