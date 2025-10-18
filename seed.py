import sqlite3
import random
import string
from datetime import datetime, timedelta

DB_PATH = 'database.db'         # "Realistic" values:
NUM_USERS = 1000                # 100000
INGREDIENTS_PER_USER = 500      # 100-500
FOODS_PER_USER = 500            # 100-500
FOODS_EATEN_DAILY = 10          # 5-15


FOOD_CLASSES = ['Breakfast/Supper', 'Lunch/Dinner', 'Snack', 'Drink']

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_users(conn):
    cursor = conn.cursor()
    for _ in range(NUM_USERS):
        username = random_string(12)
        password_hash = random_string(32)
        cursor.execute("INSERT INTO Users (username, password_hash) VALUES (?, ?)", (username, password_hash))
    conn.commit()


def create_ingredients(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users")
    user_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        for _ in range(INGREDIENTS_PER_USER):
            name = random_string(10)
            protein = round(random.uniform(0.1, 50.0), 2)
            calories = random.randint(10, 1000)
            cursor.execute(
                "INSERT INTO Ingredients (name, user_id, protein, calories) VALUES (?, ?, ?, ?)",
                (name, user_id, protein, calories)
            )
    conn.commit()


def create_foods(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users")
    user_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        cursor.execute("SELECT id, protein, calories FROM Ingredients WHERE user_id = ?", (user_id,))
        ingredients = cursor.fetchall()
        if not ingredients:
            continue

        for _ in range(FOODS_PER_USER):
            food_name = random_string(12)
            food_class = random.choice(FOOD_CLASSES)
            selected_ingredients = random.sample(ingredients, k=random.randint(1, min(10, len(ingredients))))

            total_protein = sum(i[1] for i in selected_ingredients)
            total_calories = sum(i[2] for i in selected_ingredients)

            cursor.execute(
                "INSERT INTO Foods (name, user_id, class, total_protein, total_calories) VALUES (?, ?, ?, ?, ?)",
                (food_name, user_id, food_class, total_protein, total_calories)
            )
            food_id = cursor.lastrowid

            for ing in selected_ingredients:
                quantity = round(random.uniform(0.5, 2.0), 2)
                cursor.execute(
                    "INSERT INTO FoodIngredients (food_id, ingredient_id, quantity) VALUES (?, ?, ?)",
                    (food_id, ing[0], quantity)
                )

    conn.commit()


def create_eaten_history(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Users")
    user_ids = [row[0] for row in cursor.fetchall()]

    for user_id in user_ids:
        cursor.execute("SELECT id, total_protein, total_calories FROM Foods WHERE user_id = ?", (user_id,))
        foods = cursor.fetchall()
        if not foods:
            continue

        for day_offset in range(30):
            date = datetime.now() - timedelta(days=day_offset)
            num_foods_today = random.randint(1, FOODS_EATEN_DAILY)
            eaten_today = random.choices(foods, k=num_foods_today)

            for food in eaten_today:
                quantity = round(random.uniform(0.5, 3.0), 2)
                eaten_protein = food[1] * quantity
                eaten_calories = food[2] * quantity
                cursor.execute(
                    """INSERT INTO Eaten (user_id, food_id, time, quantity, eaten_protein, eaten_calories) 
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, food[0], date.strftime('%Y-%m-%d %H:%M:%S'), quantity, eaten_protein, eaten_calories)
                )

    conn.commit()


def main():
    conn = sqlite3.connect(DB_PATH)
    create_users(conn)
    print("Users added")

    create_ingredients(conn)
    print("Ingredients added")

    create_foods(conn)
    print("Foods added")

    create_eaten_history(conn)
    print("Eaten history added")

    conn.close()

if __name__ == '__main__':
    main()
