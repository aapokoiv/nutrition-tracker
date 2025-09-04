from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def index():
    foods = ["peruna", "banaani", "kanapihvi"]
    return render_template("index.html", message="Welcome!", foods=foods)