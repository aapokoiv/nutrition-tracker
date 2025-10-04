import db

# ---------------- Ingredients ----------------
def get_user_ingredients(user_id):
    return db.query("SELECT * FROM Ingredients WHERE user_id = ?", [user_id])

def get_ingredient(user_id, ingredient_id):
    result = db.query("SELECT * FROM Ingredients WHERE id = ? AND user_id = ?", [ingredient_id, user_id])
    return result[0] if result else None

def add_ingredient(user_id, name, protein, calories):
    return db.execute(
        "INSERT INTO Ingredients (name, protein, calories, user_id) VALUES (?, ?, ?, ?)",
        [name, protein, calories, user_id]
    )

def update_ingredient(user_id, ingredient_id, name, protein, calories):
    db.execute(
        "UPDATE Ingredients SET name = ?, protein = ?, calories = ? WHERE id = ? AND user_id = ?",
        [name, protein, calories, ingredient_id, user_id]
    )

def delete_ingredient(user_id, ingredient_id):
    db.execute("DELETE FROM FoodIngredients WHERE ingredient_id = ?", [ingredient_id])
    db.execute("DELETE FROM Ingredients WHERE id = ? AND user_id = ?", [ingredient_id, user_id])

# ---------------- Foods ----------------
def add_food(user_id, name, category, is_public=1):
    return db.execute(
        "INSERT INTO Foods (name, class, user_id, is_public) VALUES (?, ?, ?, ?)",
        [name, category, user_id, is_public]
    )

def update_food(user_id, food_id, name, category):
    db.execute(
        "UPDATE Foods SET name = ?, class = ? WHERE id = ? AND user_id = ?",
        [name, category, food_id, user_id]
    )

def delete_food(user_id, food_id):
    db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])
    db.execute("DELETE FROM Foods WHERE id = ? AND user_id = ?", [food_id, user_id])

def get_food(user_id, food_id):
    result = db.query("SELECT * FROM Foods WHERE id = ? AND user_id = ?", [food_id, user_id])
    return result[0] if result else None

def get_food_ingredients(food_id):
    return db.query("""
        SELECT fi.quantity, i.id AS ingredient_id, i.name, i.protein, i.calories
        FROM FoodIngredients fi
        JOIN Ingredients i ON fi.ingredient_id = i.id
        WHERE fi.food_id = ?
    """, [food_id])

def get_food_nutrients(food_id):
    return db.query("SELECT id, total_protein, total_calories FROM Foods WHERE id = ?", [food_id])

def add_food_ingredient(food_id, ingredient_id, quantity):
    db.execute(
        "INSERT INTO FoodIngredients (food_id, ingredient_id, quantity) VALUES (?, ?, ?)",
        [food_id, ingredient_id, quantity]
    )

def delete_food_ingredients(food_id):
    db.execute("DELETE FROM FoodIngredients WHERE food_id = ?", [food_id])

# ---------------- Likes ----------------
def like_food(user_id, food_id):
    return db.execute("INSERT INTO Likes (user_id, food_id) VALUES (?, ?)", [user_id, food_id])

def unlike_food(user_id, food_id):
    db.execute("DELETE FROM Likes WHERE user_id = ? AND food_id = ?", [user_id, food_id])

def get_liked_foods(user_id):
    return db.query("""
        SELECT f.* FROM Foods f
        JOIN Likes l ON f.id = l.food_id
        WHERE l.user_id = ?
    """, [user_id])

# ---------------- Eaten ----------------
def record_eaten(user_id, food_id, quantity, protein, calories):
    db.execute("""
        INSERT INTO Eaten (user_id, food_id, time, quantity, eaten_protein, eaten_calories)
        VALUES (?, ?, datetime('now'), ?, ?, ?)
    """, [user_id, food_id, quantity, protein, calories])

def get_user_eaten(user_id, limit=50):
    return db.query("SELECT * FROM Eaten WHERE user_id = ? ORDER BY time DESC LIMIT ?", [user_id, limit])

def get_user_daily_intake(user_id):
    return db.query("""
        SELECT
            ROUND(SUM(e.eaten_protein), 2) AS total_protein,
            ROUND(SUM(e.eaten_calories), 2) AS total_calories
        FROM Eaten e
        WHERE e.user_id = ?
          AND date(e.time) = date('now', 'localtime')
    """, [user_id])[0]

# ---------------- Update totals ----------------
def update_food_totals(food_id):
    rows = db.query("""
        SELECT COALESCE(i.protein,0) AS protein, COALESCE(i.calories,0) AS calories, COALESCE(fi.quantity,1) AS qty
        FROM FoodIngredients fi
        JOIN Ingredients i ON fi.ingredient_id = i.id
        WHERE fi.food_id = ?
    """, [food_id])
    total_prot = sum(r["protein"] * r["qty"] for r in rows)
    total_cal = sum(r["calories"] * r["qty"] for r in rows)
    db.execute("UPDATE Foods SET total_protein = ?, total_calories = ? WHERE id = ?", [round(total_prot,2), round(total_cal,2), food_id])

# ---------------- Get all ----------------
def get_all(user_id):
    return db.query("""
        SELECT f.id AS food_id, f.name AS food_name, f.class AS food_class,
            COALESCE(i.name, '') AS ingredient_name, COALESCE(i.protein, 0) AS protein,
            COALESCE(i.calories, 0) AS calories, COALESCE(fi.quantity, 0) AS quantity
        FROM Foods f
        LEFT JOIN FoodIngredients fi ON f.id = fi.food_id
        LEFT JOIN Ingredients i ON fi.ingredient_id = i.id
        WHERE f.user_id = ?
        ORDER BY f.id
    """, [user_id])