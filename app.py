from flask import Flask, render_template, session, request, redirect, flash, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
import db, config, sqlite3


app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    messages=get_flashed_messages()
    return render_template("index.html", messages=messages)

# Registeration
@app.route("/register")
def register():
    messages=get_flashed_messages()
    return render_template("register.html", messages=messages)

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        flash("Passwords don't match")
        return redirect("/register")
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        flash("Username already taken")
        return redirect("/register")
    
    flash("Account created successfully")
    return redirect("/")

