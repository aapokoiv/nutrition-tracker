from flask import Blueprint, render_template, request, redirect, url_for, flash, get_flashed_messages, session
import foods_repo
from auth import login_required

foods_bp = Blueprint("foods", __name__, template_folder="templates")

@foods_bp.route("/foods", methods=["GET", "POST"])
@login_required
def all_foods():
    user_id = session["user_id"]
    messages = get_flashed_messages()
    ingredients = foods_repo.get_user_ingredients(user_id)

    if request.method == "POST":
        if "ingredient_submit" in request.form:
            name = request.form.get("ingredient_name")
            protein = float(request.form.get("ingredient_protein", 0) or 0)
            calories = float(request.form.get("ingredient_calories", 0) or 0)
            foods_repo.add_ingredient(user_id, name, protein, calories)
            flash(f"Ingredient '{name}' added.")
            return redirect(url_for("foods.all_foods"))

        if "food_submit" in request.form:
            food_name = request.form.get("food_name")
            food_class = request.form.get("food_class")
            is_public = 1 if request.form.get("is_public") == "on" else 0
            food_id = foods_repo.add_food(user_id, food_name, food_class, is_public)

            for ing in ingredients:
                raw_qty = request.form.get(f"ingredient_{ing['id']}", "")
                try:
                    qty = float(raw_qty) if raw_qty.strip() != "" else 0.0
                except ValueError:
                    qty = 0.0
                if qty > 0:
                    foods_repo.add_food_ingredient(food_id, ing["id"], qty)

            foods_repo.update_food_totals(food_id)
            flash(f"Food '{food_name}' added.")
            return redirect(url_for("foods.all_foods"))


    ing_sort_by = request.args.get("ing_sort_by", "name")
    ing_sort_dir = request.args.get("ing_sort_dir", "asc")
    food_sort_by = request.args.get("food_sort_by", "name")
    food_sort_dir = request.args.get("food_sort_dir", "asc")

    allowed_ing_sorts = {"name", "protein", "calories"}
    allowed_food_sorts = {"name", "class", "total_protein", "total_calories"}

    # Fetch flattened foods+ingredients for total calculations

    rows = foods_repo.get_all(user_id)

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
    foods_repo.delete_food(session["user_id"], food_id)
    flash("Food deleted.")
    return redirect(url_for("foods.all_foods"))

@foods_bp.route("/ingredients/<int:ingredient_id>/delete", methods=["POST"])
@login_required
def delete_ingredient(ingredient_id):
    user_id = session["user_id"]
    foods_repo.delete_ingredient(user_id, ingredient_id)
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
        foods_repo.update_ingredient(user_id, ingredient_id, name, protein, calories)
        flash("Ingredient updated.")
        return redirect(url_for("foods.all_foods"))

    # GET: fetch current values
    ingredient = foods_repo.get_ingredient(user_id, ingredient_id)
    if not ingredient:
        flash("Ingredient not found.")
        return redirect(url_for("foods.all_foods"))

    return render_template("edit_ingredient.html", ingredient=ingredient)

@foods_bp.route("/foods/<int:food_id>/edit", methods=["GET", "POST"])
@login_required
def edit_food(food_id):
    user_id = session["user_id"]

    if request.method == "POST":
        food_name = request.form.get("food_name")
        food_class = request.form.get("food_class")

        # Update the food itself
        foods_repo.update_food(user_id, food_id, food_name, food_class)

        # Reset food ingredients
        foods_repo.delete_food_ingredients(food_id)

        # Rebuild from form input (iterate over ALL user ingredients)
        user_ingredients = foods_repo.get_user_ingredients(user_id)

        for ing in user_ingredients:
            raw_val = request.form.get(f"ingredient_{ing['id']}", "")
            try:
                qty = float(raw_val) if raw_val.strip() != "" else 0
            except ValueError:
                qty = 0
            if qty > 0:
                foods_repo.add_food_ingredient(food_id, ing["id"], qty)

        # Update totals (protein & calories)
        foods_repo.update_food_totals(food_id)

        flash(f"Food '{food_name}' updated.")
        return redirect(url_for("foods.all_foods"))

    # GET: fetch current values
    food = foods_repo.get_food(user_id, food_id)
    if not food:
        flash("Food not found.")
        return redirect(url_for("foods.all_foods"))

    # dict of existing ingredient_id -> quantity
    existing_fi = {
        fi["ingredient_id"]: fi["quantity"]
        for fi in foods_repo.get_food_ingredients(food_id)
    }

    # all user ingredients
    user_ingredients = foods_repo.get_user_ingredients(user_id)

    return render_template(
        "edit_food.html",
        food=food,
        user_ingredients=user_ingredients,
        food_ingredients=existing_fi,
    )

@foods_bp.route("/foods/<int:food_id>/eat", methods=["POST"])
@login_required
def eat_food(food_id):
    user_id = session["user_id"]
    qty = float(request.form.get("quantity", 1.0))
    # Fetch food totals
    food = foods_repo.get_food_nutrientset(food_id)
    if not food:
        flash("Food not found.")
        return redirect(url_for("foods.all_foods"))
    f = food[0]
    eaten_protein = (f["total_protein"] or 0.0) * qty
    eaten_calories = (f["total_calories"] or 0.0) * qty
    foods_repo.record_eaten(user_id, food_id, qty, eaten_protein, eaten_calories)
    flash("Recorded as eaten.")
    return redirect(request.referrer or url_for("foods.all_foods"))

@foods_bp.route("/foods/<int:food_id>/like", methods=["POST"])
@login_required
def like_food(food_id):
    user_id = session["user_id"]
    # insert ignore style: try/except on unique constraint
    try:
        foods_repo.like_food(user_id, food_id)
        flash("Liked.")
    except Exception:
        # already liked or other error
        pass
    return redirect(request.referrer or url_for("foods.all_foods"))

@foods_bp.route("/foods/<int:food_id>/unlike", methods=["POST"])
@login_required
def unlike_food(food_id):
    user_id = session["user_id"]
    foods_repo.unlike_food(user_id, food_id)
    flash("Removed from liked foods.")
    return redirect(request.referrer or url_for("foods.all_foods"))

