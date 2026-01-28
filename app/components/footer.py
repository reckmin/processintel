import streamlit as st


def footer(html: str):

    st.html(
        f"""
        <style>
            .st-footer {{
                position: sticky;
                bottom: 0;
                width: 100%;
                padding: 10px 20px;
                text-align: center;
                border-top: 1px solid;
                font-size: 0.85rem;
                z-index: 100;
            }}

            html[data-theme="light"] .st-footer {{
                background-color: #f9f9f9;
                color: #444;
                border-top-color: #e0e0e0;
            }}

            html[data-theme="light"] .st-footer a {{
                color: #3366cc;
            }}

            html[data-theme="dark"] .st-footer {{
                background-color: #0e1117;
                color: #bbb;
                border-top-color: #30363d;
            }}

            html[data-theme="dark"] .st-footer a {{
                color: #58a6ff;
            }}

            .st-footer a {{
                text-decoration: none;
            }}

            .st-footer a:hover {{
                text-decoration: underline;
            }}
        </style>

        <div class="st-footer">
            {html}
        </div>
        """
    )
