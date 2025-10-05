from flask import Flask, render_template, session, request, redirect, flash, get_flashed_messages, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, timedelta
import secrets
import config, users, foods_repo
from foods import foods_bp
from auth import login_required, check_csrf

app = Flask(__name__)
app.secret_key = config.secret_key
app.register_blueprint(foods_bp)


@app.route("/")
@login_required
def index():
    messages = get_flashed_messages()
    user_id = session["user_id"]
    intake = foods_repo.get_user_daily_intake(user_id)
    eaten_today = foods_repo.get_user_eaten_today(user_id)

    user = users.get_user_by_id(user_id)
    if not user:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    return render_template("index.html", 
                           messages=messages, 
                           pt = user["protein_target"], 
                           ct = user["calorie_target"], 
                           pi = intake["total_protein"],
                           ci = intake["total_calories"],
                           user = user["username"],
                           user_id = user_id,
                           foods = eaten_today)

@app.template_filter("sum_values")
def sum_ingredient_values(items, attribute, quantity_attribute="quantity"):
    total = 0.0
    for i in items:
        total += i[attribute] * i.get(quantity_attribute, 1.0)
    return round(total, 2)


@app.route("/update-protein", methods=["POST"])
@login_required
def update_protein():
    check_csrf()
    protein_target = request.form.get("protein_target", type=int)

    if protein_target is None or protein_target < 0 or protein_target > 1000000:
        flash("Invalid protein target. Please enter a number between 0 and 1000000.")
        return redirect(url_for("index"))

    users.update_protein_target(session["user_id"], protein_target)
    flash("Protein target updated.")
    return redirect(url_for("index"))


@app.route("/update-calories", methods=["POST"])
@login_required
def update_calories():
    check_csrf()
    calorie_target = request.form.get("calorie_target", type=int)

    if calorie_target is None or calorie_target < 0 or calorie_target > 1000000:
        flash("Invalid calorie target. Please enter a number between 0 and 1000000.")
        return redirect(url_for("index"))

    users.update_calorie_target(session["user_id"], calorie_target)
    flash("Calorie target updated.")
    return redirect(url_for("index"))

@app.route("/image/<int:user_id>")
def show_profile_pic(user_id):
    image = users.get_profile_picture(user_id)
    if image:
        return Response(image, mimetype="image/jpeg")
    else:
        return redirect(url_for("static", filename="profile_pics/default.jpg"))

# --- helper to fill missing days ---
def fill_missing_days(summary_rows, days=7):
    lookup = {r["day"]: r for r in summary_rows}
    today = date.today()
    filled = []
    # oldest → newest
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        filled.append(lookup.get(d, {"day": d, "total_protein": 0.0, "total_calories": 0.0}))
    return filled

@app.route("/profile/<int:user_id>", methods=["GET", "POST"])
@login_required
def profile(user_id):
    messages = get_flashed_messages()
    user_id = session["user_id"]
    user = users.get_user_by_id(user_id)

    if request.method == "POST":
        if "profile_picture" in request.files: 
            file = request.files["profile_picture"] 
            if not file.filename.endswith(".jpg"): 
                flash("File type not allowed") 
                return redirect(url_for("profile", user_id=user_id)) 
            
            image = file.read() 
            if len(image) > 100 * 1024: 
                flash("File size too large") 
                return redirect(url_for("profile", user_id=user_id)) 
            
            users.update_profile_picture(user_id, image) 
            flash("Profile picture updated successfully.") 
            return redirect(url_for("profile", user_id=user_id))

    summary30 = user_30day_summary(user_id)

    # Get raw 7-day stats
    summary7_raw = users.user_nutrition_stats(user_id, 7)
    # Reverse, and fill missing days
    summary7_reversed = list(reversed(summary7_raw))
    summary7 = fill_missing_days(summary7_reversed, 7)

    return render_template(
        "profile.html",
        messages=messages,
        user=user,
        summary30=summary30,
        summary7=summary7
    )

def user_30day_summary(user_id):
    user = users.get_user_by_id(user_id)
    protein_target = user["protein_target"] if user else 0

    day_rows = users.user_nutrition_stats(user_id, 30)

    if not day_rows:
        return {
            "avg_calories": 0,
            "avg_protein": 0,
            "hit_days": 0,
            "total_days": 0
        }

    total_days = len(day_rows)
    total_cals = sum(r["total_calories"] for r in day_rows)
    total_prot = sum(r["total_protein"] for r in day_rows)
    hit_days = sum(1 for r in day_rows if r["total_protein"] >= protein_target)

    return {
        "avg_calories": round(total_cals / total_days, 2),
        "avg_protein": round(total_prot / total_days, 2),
        "hit_days": hit_days,
        "total_days": total_days
    }



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
    
    if len(password1) < 1 or len(password1) > 50:
        flash("Password must be between 1 and 50 characters long")
        return redirect(url_for("register"))

    password_hash = generate_password_hash(password1)

    try:
        users.create_user(username, password_hash)
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
        session["csrf_token"] = secrets.token_hex(16)
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