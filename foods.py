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
                qty = float(request.form.get(f"ingredient_{ing["id"]}", 0))
                if qty > 0:
                    db.execute(
                        "INSERT INTO FoodIngredients (food_id, ingredient_id, quantity) VALUES (?, ?, ?)",
                        [food_id, ing["id"], qty]
                    )
            flash(f"Food '{food_name}' added.")
            return redirect(url_for("foods.all_foods"))

    rows = db.query("""
        SELECT f.id AS food_id, f.name AS food_name, f.class AS food_class,
               i.name AS ingredient_name, i.protein, i.calories, fi.quantity
        FROM Foods f
        JOIN FoodIngredients fi ON f.id = fi.food_id
        JOIN Ingredients i ON fi.ingredient_id = i.id
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