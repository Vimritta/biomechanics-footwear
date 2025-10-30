# app_flask.py
from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def home():
    # Streamlit runs on http://localhost:8501 by default; iframe points there
    return render_template("index.html", streamlit_url="http://localhost:8501")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
