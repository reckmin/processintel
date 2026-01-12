![alt text](PMInsight.jpg?raw=true)

# PM-Insight

**PM-Insight** is an open-source application for **process mining, visualization, and interactive exploration** of process models. It enables users to import event logs, mine process models using multiple algorithms, and explore results through an **interactive graph-based interface**.

---

## Features

- **Event log & model input**
  - Import **CSV event logs**
  - Load **PM-Insight native process models**
- **Process mining algorithms**
  - Alpha Miner  
  - Heuristic Miner  
  - Inductive Miner  
  - Fuzzy Miner  
  - Genetic Miner
- **Interactive process model visualization**
  - Fully interactive graphs
  - Click on **nodes and edges** to inspect detailed metrics and properties directly in the app
  - Filter nodes and edges using configurable metrics
- **Export capabilities**
  - Export visualizations as **SVG**, **PNG**, and **DOT** files
  - Export mined **process models** in native format
- **Flexible deployment**
  - Run locally via Streamlit
  - Can also be deployed and run as a **Nix service**

---

## Project Status

- **Current version:** `1.0.0`
- **Stability:** Ready for productive use

---

## Requirements

- **Python:** 3.10 or newer  
- **Graphviz (required)** for process model rendering

Install Graphviz from:  
<https://graphviz.org/>

Verify installation:
```bash
dot -V
```

Ensure the Graphviz bin directory is available in your system PATH.

All Python dependencies are listed in requirements.txt.

---

## Running the Application

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application from the project root:

```bash
streamlit run app/streamlit_app.py
```

The application will open automatically in your default web browser.

---

## Running Tests

Test dependencies are listed in:

`tests/test_requirements.txt`

Install them with:

```bash
pip install -r tests/test_requirements.txt
```
Run all tests:
```bash
python -m unittest tests
```

---

## Nix Support

PM-Insight can also be run as a Nix service, enabling reproducible builds and seamless deployment in Nix-based environments.
See the Nix-related configuration files in the repository for details.

---

## Contributing

Contributions are very welcome!
Please refer to [CONTRIBUTING.md](Contributing.md) for guidelines on reporting issues, submitting pull requests, and contributing code or documentation.

---

## License

This project is licensed under the terms described in the LICENSE file included in the repository.

---

## Feedback

If you encounter bugs or have feature requests, please open an issue on GitHub.
Your feedback helps improve PM-Insight for everyone.