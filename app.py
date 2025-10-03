from flask import Flask, render_template, session, request, redirect, flash, get_flashed_messages, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import db, config, users
from foods import foods_bp
from auth import login_required

app = Flask(__name__)
app.secret_key = config.secret_key
app.register_blueprint(foods_bp)


@app.route("/")
@login_required
def index():
    messages = get_flashed_messages()
    user_id = session.get("user_id")

    user = users.get_user_by_id(user_id)
    if not user:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    return render_template("index.html", 
                           messages=messages, 
                           pt=user["protein_target"], 
                           ct=user["calorie_target"], 
                           user=user["username"])

@app.template_filter("sum_values")
def sum_ingredient_values(items, attribute, quantity_attribute="quantity"):
    total = 0.0
    for i in items:
        total += i[attribute] * i.get(quantity_attribute, 1.0)
    return round(total, 2)


@app.route("/update-protein", methods=["POST"])
@login_required
def update_protein():
    protein_target = request.form.get("protein_target", type=int)

    if protein_target is None or protein_target < 0:
        flash("Invalid protein target. Please enter a positive number.")
        return redirect(url_for("index"))

    users.update_protein_target(session["user_id"], protein_target)
    flash("Protein target updated.")
    return redirect(url_for("index"))


@app.route("/update-calories", methods=["POST"])
@login_required
def update_calories():
    calorie_target = request.form.get("calorie_target", type=int)

    if calorie_target is None or calorie_target < 0:
        flash("Invalid calorie target. Please enter a positive number.")
        return redirect(url_for("index"))

    users.update_calorie_target(session["user_id"], calorie_target)
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

    if not username or not password1:
        flash("Username and password are required")
        return redirect(url_for("register"))

    if len(username) > 30:
        flash("Username too long (max 30 characters)")
        return redirect(url_for("register"))

    if password1 != password2:
        flash("Passwords don't match")
        return redirect(url_for("register"))
    
    if len(password1) < 1:
        flash("Password must be at least 1 characters long")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password1)

    try:
        users.create_user([username, password_hash])
    except:
        flash("Username already taken")
        return redirect(url_for("register"))
    
    flash("Account created successfully")
    return redirect(url_for("login"))

# Log in
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = users.get_user_by_username(username)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Wrong username or password")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        flash("Logged in successfully")
        return redirect(url_for("index"))

    messages = get_flashed_messages()
    return render_template("login.html", messages=messages)

@app.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    flash("Logged out")
    return redirect(url_for("index"))