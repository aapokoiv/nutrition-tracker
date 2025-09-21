from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages
import db
from auth import login_required

foods_bp = Blueprint("foods", __name__, template_folder="templates")

@foods_bp.route("/foods", methods=["GET", "POST"])
@login_required
def all_foods():
    messages = get_flashed_messages()
    ingredients = db.query("SELECT * FROM Ingredients")

    if request.method == "POST":
        if "ingredient_submit" in request.form:
            name = request.form.get("ingredient_name")
            protein = float(request.form.get("ingredient_protein", 0))
            calories = float(request.form.get("ingredient_calories", 0))
            db.execute(
                "INSERT INTO Ingredients (name, protein, calories) VALUES (?, ?, ?)",
                [name, protein, calories]
            )
            flash(f"Ingredient '{name}' added.")
            return redirect(url_for("foods.all_foods"))

        if "food_submit" in request.form:
            food_name = request.form.get("food_name")
            food_class = request.form.get("food_class")
            db.execute(
                "INSERT INTO Foods (name, class) VALUES (?, ?)",
                [food_name, food_class]
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

    rows = db.query("""
        SELECT f.id AS food_id, f.name AS food_name, f.class AS food_class,
        COALESCE(i.name, '') AS ingredient_name, COALESCE(i.protein, 0) AS protein, 
        COALESCE(i.calories, 0) AS calories, COALESCE(fi.quantity, 0) AS quantity
        FROM Foods f
        LEFT JOIN FoodIngredients fi ON f.id = fi.food_id
        LEFT JOIN Ingredients i ON fi.ingredient_id = i.id
        ORDER BY f.id
    """)

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

    return render_template(
        "foods.html",
        foods=foods,
        ingredients=ingredients,
        messages=messages
    )

@foods_bp.route("/foods/<int:food_id>/delete", methods=["POST"])
@login_required
def delete_food(food_id):
    db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])
    db.execute("DELETE FROM Foods WHERE id = ?", [food_id])
    flash("Food deleted.")
    return redirect(url_for("foods.all_foods"))

@foods_bp.route("/ingredients/<int:ingredient_id>/delete", methods=["POST"])
@login_required
def delete_ingredient(ingredient_id):
    db.execute("DELETE FROM FoodIngredients WHERE ingredient_id = ?", [ingredient_id])
    db.execute("DELETE FROM Ingredients WHERE id = ?", [ingredient_id])
    flash("Ingredient deleted.")
    return redirect(url_for("foods.all_foods"))


@foods_bp.route("/ingredients/<int:ingredient_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ingredient(ingredient_id):
    if request.method == "POST":
        name = request.form.get("name")
        protein = float(request.form.get("protein", 0))
        calories = float(request.form.get("calories", 0))
        db.execute(
            "UPDATE Ingredients SET name = ?, protein = ?, calories = ? WHERE id = ?",
            [name, protein, calories, ingredient_id]
        )
        flash("Ingredient updated.")
        return redirect(url_for("foods.all_foods"))

    # GET: fetch current values
    ingredient = db.query("SELECT * FROM Ingredients WHERE id = ?", [ingredient_id])[0]
    return render_template("edit_ingredient.html", ingredient=ingredient)

@foods_bp.route("/foods/<int:food_id>/edit", methods=["GET", "POST"])
@login_required
def edit_food(food_id):
    if request.method == "POST":
        food_name = request.form.get("food_name")
        food_class = request.form.get("food_class")

        db.execute(
            "UPDATE Foods SET name = ?, class = ? WHERE id = ?",
            [food_name, food_class, food_id]
        )

        # Update the FoodIngredients
        # First, delete existing entries
        db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])

        # Then, insert new entries
        ingredients = db.query("SELECT * FROM Ingredients")
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
    food = db.query("SELECT * FROM Foods WHERE id = ?", [food_id])[0]
    food_ingredients = db.query("""
        SELECT fi.quantity, i.id, i.name, i.protein, i.calories
        FROM FoodIngredients fi
        JOIN Ingredients i ON fi.ingredient_id = i.id
        WHERE fi.food_id = ?
    """, [food_id])

    return render_template("edit_food.html", food=food, food_ingredients=food_ingredients)