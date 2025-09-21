python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
# Run CLI
python cli.py
# Run Web UI
streamlit run web/app.py
