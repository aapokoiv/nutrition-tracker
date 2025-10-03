from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages, session
import db
from auth import login_required

foods_bp = Blueprint("foods", __name__, template_folder="templates")

@foods_bp.route("/foods", methods=["GET", "POST"])
@login_required
def all_foods():
    user_id = session["user_id"]
    messages = get_flashed_messages()
    ingredients = db.query("SELECT * FROM Ingredients")

    if request.method == "POST":
        if "ingredient_submit" in request.form:
            name = request.form.get("ingredient_name")
            protein = float(request.form.get("ingredient_protein", 0))
            calories = float(request.form.get("ingredient_calories", 0))
            db.execute(
                "INSERT INTO Ingredients (name, protein, calories, user_id) VALUES (?, ?, ?, ?)",
                [name, protein, calories, session["user_id"]]
            )
            flash(f"Ingredient '{name}' added.")
            return redirect(url_for("foods.all_foods"))

        if "food_submit" in request.form:
            food_name = request.form.get("food_name")
            food_class = request.form.get("food_class")
            db.execute(
                "INSERT INTO Foods (name, class, user_id) VALUES (?, ?, ?)",
                [food_name, food_class, session["user_id"]]
            )
            food_id = db.last_insert_id()

            for ing in ingredients:
                raw_qty = request.form.get(f"ingredient_{ing['id']}", "")
                try:
                    qty = float(raw_qty) if raw_qty.strip() != "" else 0.0
                except ValueError:
                    qty = 0.0
                if qty > 0:
                    db.execute(
                        "INSERT INTO FoodIngredients (food_id, ingredient_id, quantity) VALUES (?, ?, ?)",
                        [food_id, ing["id"], qty]
                    )
            flash(f"Food '{food_name}' added.")
            return redirect(url_for("foods.all_foods"))

    ing_sort_by = request.args.get("ing_sort_by", "name")
    ing_sort_dir = request.args.get("ing_sort_dir", "asc")
    food_sort_by = request.args.get("food_sort_by", "name")
    food_sort_dir = request.args.get("food_sort_dir", "asc")

    allowed_ing_sorts = {"name", "protein", "calories"}
    allowed_food_sorts = {"name", "class", "total_protein", "total_calories"}

    # Fetch flattened foods+ingredients for total calculations

    ingredients = db.query("SELECT * FROM Ingredients WHERE user_id = ?", [user_id])

    rows = db.query("""
        SELECT f.id AS food_id, f.name AS food_name, f.class AS food_class,
            COALESCE(i.name, '') AS ingredient_name, COALESCE(i.protein, 0) AS protein,
            COALESCE(i.calories, 0) AS calories, COALESCE(fi.quantity, 0) AS quantity
        FROM Foods f
        LEFT JOIN FoodIngredients fi ON f.id = fi.food_id
        LEFT JOIN Ingredients i ON fi.ingredient_id = i.id
        WHERE f.user_id = ?
        ORDER BY f.id
    """, [user_id])

    # Reconstruct foods dict and calculate totals
    foods = {}
    for row in rows:
        fid = row["food_id"]
        if fid not in foods:
            foods[fid] = {
                "id": fid,
                "name": row["food_name"],
                "class": row["food_class"],
                "ingredients": []
            }
        if row["ingredient_name"]:
            foods[fid]["ingredients"].append({
                "name": row["ingredient_name"],
                "protein": row["protein"],
                "calories": row["calories"],
                "quantity": row["quantity"]
            })

    # Convert to list with totals
    foods_list = []
    for f in foods.values():
        total_prot = sum(ing["protein"] * ing.get("quantity", 0) for ing in f["ingredients"])
        total_cal = sum(ing["calories"] * ing.get("quantity", 0) for ing in f["ingredients"])
        f["total_protein"] = round(total_prot, 2)
        f["total_calories"] = round(total_cal, 2)
        foods_list.append(f)

    # ---------- Sorting ----------
    # Ingredients
    if ing_sort_by not in allowed_ing_sorts:
        ing_sort_by = "name"
    ing_reverse = (ing_sort_dir == "desc")
    if ing_sort_by == "name":
        ingredients = sorted(ingredients, key=lambda x: x["name"].lower(), reverse=ing_reverse)
    else:
        ingredients = sorted(ingredients, key=lambda x: float(x[ing_sort_by]), reverse=ing_reverse)

    # Foods
    if food_sort_by not in allowed_food_sorts:
        food_sort_by = "name"
    food_reverse = (food_sort_dir == "desc")
    if food_sort_by in ("name", "class"):
        foods_list = sorted(foods_list, key=lambda x: x[food_sort_by].lower(), reverse=food_reverse)
    else:
        foods_list = sorted(foods_list, key=lambda x: float(x[food_sort_by]), reverse=food_reverse)

    return render_template(
        "foods.html",
        ingredients=ingredients,
        foods_list=foods_list,
        foods=foods,
        messages=messages,
        ing_sort_by=ing_sort_by,
        ing_sort_dir=ing_sort_dir,
        food_sort_by=food_sort_by,
        food_sort_dir=food_sort_dir
    )

@foods_bp.route("/foods/<int:food_id>/delete", methods=["POST"])
@login_required
def delete_food(food_id):
    user_id = session["user_id"]
    db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])
    db.execute("DELETE FROM Foods WHERE id = ? AND user_id = ?", [food_id, user_id])
    flash("Food deleted.")
    return redirect(url_for("foods.all_foods"))

@foods_bp.route("/ingredients/<int:ingredient_id>/delete", methods=["POST"])
@login_required
def delete_ingredient(ingredient_id):
    user_id = session["user_id"]
    db.execute("DELETE FROM FoodIngredients WHERE ingredient_id = ?", [ingredient_id])
    db.execute("DELETE FROM Ingredients WHERE id = ? AND user_id = ?", [ingredient_id, user_id])
    flash("Ingredient deleted.")
    return redirect(url_for("foods.all_foods"))


@foods_bp.route("/ingredients/<int:ingredient_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ingredient(ingredient_id):
    user_id = session["user_id"]
    if request.method == "POST":
        name = request.form.get("name")
        protein = float(request.form.get("protein", 0))
        calories = float(request.form.get("calories", 0))
        db.execute(
            "UPDATE Ingredients SET name = ?, protein = ?, calories = ? WHERE id = ? AND user_id = ?",
            [name, protein, calories, ingredient_id, user_id]
        )
        flash("Ingredient updated.")
        return redirect(url_for("foods.all_foods"))

    # GET: fetch current values
    ingredient = db.query("SELECT * FROM Ingredients WHERE id = ? AND user_id = ?", [ingredient_id, user_id])
    if not ingredient:
        flash("Ingredient not found.")
        return redirect(url_for("foods.all_foods"))

    return render_template("edit_ingredient.html", ingredient=ingredient[0])

@foods_bp.route("/foods/<int:food_id>/edit", methods=["GET", "POST"])
@login_required
def edit_food(food_id):
    user_id = session["user_id"]
    if request.method == "POST":
        food_name = request.form.get("food_name")
        food_class = request.form.get("food_class")

        db.execute(
            "UPDATE Foods SET name = ?, class = ? WHERE id = ? AND user_id = ?",
            [food_name, food_class, food_id, user_id]
        )

        # Update the FoodIngredients
        # First, delete existing entries
        db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])

        # Then, insert new entries
        ingredients = db.query("SELECT * FROM Ingredients WHERE user_id = ?", [user_id])
        for ing in ingredients:
            qty = float(request.form.get(f"ingredient_{ing['id']}", 0))
            if qty > 0:
                db.execute(
                    "INSERT INTO FoodIngredients (food_id, ingredient_id, quantity) VALUES (?, ?, ?)",
                    [food_id, ing["id"], qty]
                )

        flash(f"Food '{food_name}' updated.")
        return redirect(url_for("foods.all_foods"))

    # GET: fetch current values
    food = db.query("SELECT * FROM Foods WHERE id = ? AND user_id = ?", [food_id, user_id])
    if not food:
        flash("Food not found.")
        return redirect(url_for("foods.all_foods"))

    food_ingredients = db.query(""" ... """, [food_id])
    return render_template("edit_food.html", food=food[0], food_ingredients=food_ingredients)