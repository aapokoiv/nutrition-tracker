from flask import Flask, render_template, session, request, redirect, flash, get_flashed_messages, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import db, config, sqlite3, users
from foods import foods_bp
from auth import login_required

app = Flask(__name__)
app.secret_key = config.secret_key
app.register_blueprint(foods_bp)


@app.route("/")
@login_required
def index():
    messages=get_flashed_messages()
    user = session.get("username")

    sql = "SELECT protein_target, calorie_target FROM users WHERE username = ?"
    result = db.query(sql, [user])
    if not result:
        session.pop("username", None)
        return redirect(url_for("login"))
    pt = result[0]["protein_target"]
    ct = result[0]["calorie_target"]
    return render_template("index.html", messages=messages, pt=pt, ct=ct, user=user)

@app.template_filter("sum")
def sum_ingredient_values(items, attribute, quantity_attribute="quantity"):
    total = 0.0
    for i in items:
        total += i[attribute] * i.get(quantity_attribute, 1.0)
    return round(total, 2)


@app.route("/update-protein", methods=["POST"])
@login_required
def update_protein():
    protein_target = request.form.get("protein_target", type=int)
    users.update_protein_target(session["username"], protein_target)
    flash("Protein target updated.")
    return redirect(url_for("index"))

@app.route("/update-calories", methods=["POST"])
@login_required
def update_calories():
    calorie_target = request.form.get("calorie_target", type=int)
    users.update_calorie_target(session["username"], calorie_target)
    flash("Calorie target updated.")
    return redirect(url_for("index"))


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
        return redirect(url_for("register"))
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except:
        flash("Username already taken")
        return redirect(url_for("register"))
    
    flash("Account created successfully")
    return redirect(url_for("index"))

# Log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        sql = "SELECT password_hash FROM users WHERE username = ?"
        user = db.query(sql, [username])
        if not user:
            flash("Wrong username or password")
            return redirect("/login")
        password_hash = user[0]["password_hash"]

        if check_password_hash(password_hash, password):
            session["username"] = username
            flash("Logged in successfully")
            return redirect("/")
        
        flash("Wrong username or password")
        return redirect(url_for("login"))
        
    messages = get_flashed_messages()
    return render_template("login.html", messages=messages)

@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    flash("Logged out")
    return redirect(url_for("index"))