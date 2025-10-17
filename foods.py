from flask import Blueprint, render_template, request, session
from flask import redirect, url_for, flash, get_flashed_messages
import foods_repo
from auth import login_required, check_csrf

foods_bp = Blueprint("foods", __name__, template_folder="templates")

@foods_bp.route("/foods", methods=["GET", "POST"])
@login_required
def all_foods():
    user_id = session["user_id"]
    messages = get_flashed_messages()
    ingredients = foods_repo.get_user_ingredients(user_id)

    search_query = request.args.get("search", "").strip().lower()

    ing_sort_by = request.args.get("ing_sort_by", "name")
    ing_sort_dir = request.args.get("ing_sort_dir", "asc")
    food_sort_by = request.args.get("food_sort_by", "name")
    food_sort_dir = request.args.get("food_sort_dir", "asc")

    allowed_ing_sorts = {"name", "protein", "calories"}
    allowed_food_sorts = {"name", "class", "total_protein", "total_calories"}

    rows = foods_repo.get_all(user_id)

    liked_foods = foods_repo.get_liked_foods(user_id)

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

    # --- 🔍 Search filter ---
    if search_query:
        ingredients = [i for i in ingredients if search_query in i["name"].lower()]
        foods_list = [
            f for f in foods_list
            if search_query in f["name"].lower()
            or search_query in f["class"].lower()
            or any(search_query in ing["name"].lower() for ing in f["ingredients"])
        ]
        liked_foods = [
            f for f in liked_foods
            if search_query in f["name"].lower()
            or search_query in f["class"].lower()
            or any(search_query in ing["name"].lower() for ing in f["ingredients"])
        ]

    # ---------- Sorting ----------
    # Ingredients
    if ing_sort_by not in allowed_ing_sorts:
        ing_sort_by = "name"
    ing_reverse = ing_sort_dir == "desc"
    if ing_sort_by == "name":
        ingredients = sorted(ingredients, key=lambda x: x["name"].lower(), reverse=ing_reverse)
    else:
        ingredients = sorted(ingredients, key=lambda x: float(x[ing_sort_by]), reverse=ing_reverse)

    # Foods
    if food_sort_by not in allowed_food_sorts:
        food_sort_by = "name"
    food_reverse = food_sort_dir == "desc"
    if food_sort_by in ("name", "class"):
        foods_list = sorted(foods_list, key=lambda x: x[food_sort_by].lower(), reverse=food_reverse)
    else:
        foods_list = sorted(foods_list, key=lambda x: float(x[food_sort_by]), reverse=food_reverse)

    return render_template(
        "foods.html",
        ingredients=ingredients,
        foods_list=foods_list,
        foods=foods,
        liked_foods=liked_foods,
        messages=messages,
        ing_sort_by=ing_sort_by,
        ing_sort_dir=ing_sort_dir,
        food_sort_by=food_sort_by,
        food_sort_dir=food_sort_dir
    )

@foods_bp.route("/search", methods=["GET"])
@login_required
def search_foods():
    search_query = request.args.get("search", "")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    results = foods_repo.search_public_foods(search_query, page, per_page)
    total = foods_repo.total_foods(search_query)
    total_pages = (total + per_page - 1) // per_page

    # Get liked foods of current user
    user_id = session["user_id"]
    liked_foods = foods_repo.get_liked_foods(user_id)
    liked_food_ids = {food['id'] for food in liked_foods}  # set of IDs for fast lookup

    messages = get_flashed_messages()

    return render_template(
        "search.html",
        results=results,
        liked_food_ids=liked_food_ids,
        search_query=search_query,
        page=page,
        total_pages=total_pages,
        messages=messages
    )

@foods_bp.route("/ingredients/add", methods=["POST"])
@login_required
def add_ingredient():
    check_csrf()
    user_id = session["user_id"]
    name = request.form.get("ingredient_name")
    protein = float(request.form.get("ingredient_protein", 0) or 0)
    calories = float(request.form.get("ingredient_calories", 0) or 0)

    if not name or len(name) > 100 or protein > 10000 or calories > 1000000:
        flash("Inputted values out of allowed range")
        return redirect(url_for("foods.all_foods"))

    foods_repo.add_ingredient(user_id, name, protein, calories)
    flash(f"Ingredient '{name}' added.")
    return redirect(url_for("foods.all_foods"))


@foods_bp.route("/foods/add", methods=["POST"])
@login_required
def add_food():
    check_csrf()
    user_id = session["user_id"]
    ingredients = foods_repo.get_user_ingredients(user_id)
    food_name = request.form.get("food_name")
    food_class = request.form.get("food_class")
    is_public = 1 if request.form.get("is_public") == "on" else 0

    if not food_name or len(food_name) > 100:
        flash("Input a name with max 100 letters")
        return redirect(url_for("foods.all_foods"))

    food_id = foods_repo.add_food(user_id, food_name, food_class, is_public)

    for ing in ingredients:
        raw_qty = request.form.get(f"ingredient_{ing['id']}", "")
        try:
            qty = float(raw_qty) if raw_qty.strip() != "" else 0.0
        except ValueError:
            qty = 0.0
        if qty > 0 and qty <= 10000:
            foods_repo.add_food_ingredient(food_id, ing["id"], qty)

    foods_repo.update_food_totals(food_id)
    flash(f"Food '{food_name}' added.")
    return redirect(url_for("foods.all_foods"))


@foods_bp.route("/foods/<int:food_id>/delete", methods=["POST"])
@login_required
def delete_food(food_id):
    check_csrf()
    foods_repo.delete_food(session["user_id"], food_id)
    flash("Food deleted.")
    return redirect(url_for("foods.all_foods"))

@foods_bp.route("/ingredients/<int:ingredient_id>/delete", methods=["POST"])
@login_required
def delete_ingredient(ingredient_id):
    check_csrf()
    user_id = session["user_id"]
    foods_repo.delete_ingredient(user_id, ingredient_id)
    flash("Ingredient deleted.")
    return redirect(url_for("foods.all_foods"))


@foods_bp.route("/ingredients/<int:ingredient_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ingredient(ingredient_id):
    user_id = session["user_id"]
    if request.method == "POST":
        check_csrf()
        name = request.form.get("name")
        protein = float(request.form.get("protein", 0))
        calories = float(request.form.get("calories", 0))

        if not name or len(name) > 100 or protein > 10000 or calories > 1000000:
            flash("Inputted values out of allowed range")
            return redirect(url_for("foods.all_foods"))

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
        check_csrf()
        food_name = request.form.get("food_name")
        food_class = request.form.get("food_class")

        if not food_name or len(food_name) > 100:
            flash("Input a name with max 100 letters")
            return redirect(url_for("foods.all_foods"))

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
            if qty > 0 and qty <= 10000:
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
    check_csrf()
    user_id = session["user_id"]
    qty = float(request.form.get("quantity", 1.0))
    # Fetch food totals
    food = foods_repo.get_food_nutrients(food_id)
    if not food:
        flash("Food not found.")
        return redirect(url_for("foods.all_foods"))
    f = food[0]
    eaten_protein = (f["total_protein"] or 0.0) * qty
    eaten_calories = (f["total_calories"] or 0.0) * qty
    foods_repo.record_eaten(user_id, food_id, qty, eaten_protein, eaten_calories)
    flash("Recorded as eaten.")
    return redirect(request.referrer or url_for("foods.all_foods"))

@foods_bp.route("/uneat/<int:eaten_id>", methods=["POST"])
@login_required
def uneat_food(eaten_id):
    check_csrf()
    user_id = session["user_id"]
    foods_repo.delete_eaten(user_id, eaten_id)
    flash("Food removed from today's eaten list.")
    return redirect(url_for("index"))

@foods_bp.route("/foods/<int:food_id>/like", methods=["POST"])
@login_required
def like_food(food_id):
    check_csrf()
    user_id = session["user_id"]

    result = foods_repo.like_food(user_id, food_id)

    if result is not None:
        flash("Liked.")

    return redirect(url_for("foods.search_foods"))

@foods_bp.route("/foods/<int:food_id>/unlike", methods=["POST"])
@login_required
def unlike_food(food_id):
    check_csrf()
    user_id = session["user_id"]
    foods_repo.unlike_food(user_id, food_id)
    flash("Removed from liked foods.")
    return redirect(request.referrer or url_for("foods.all_foods"))
