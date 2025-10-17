import db

def get_user_by_id(user_id):
    sql = """
        SELECT id, username, password_hash, profile_pic, protein_target, calorie_target
        FROM Users WHERE id = ?
    """
    result = db.query(sql, [user_id])
    if not result:
        raise ValueError(f"User with ID {user_id} not found")
    return result[0]

def get_user_by_username(username):
    # Used in login() – needs id, username, password_hash
    sql = "SELECT id, username, password_hash FROM Users WHERE username = ?"
    result = db.query(sql, [username])
    if not result:
        raise ValueError(f"User with username {username} not found")
    return result[0]

def create_user(username, password_hash):
    sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
    return db.execute(sql, [username, password_hash])

def update_protein_target(user_id, protein_target):
    sql = "UPDATE Users SET protein_target = ? WHERE id = ?"
    db.execute(sql, [protein_target, user_id])

def update_calorie_target(user_id, calorie_target):
    sql = "UPDATE Users SET calorie_target = ? WHERE id = ?"
    db.execute(sql, [calorie_target, user_id])

def update_profile_picture(user_id, image):
    sql = "UPDATE Users SET profile_pic = ? WHERE id = ?"
    db.execute(sql, [image, user_id])

def get_profile_picture(user_id):
    sql = "SELECT profile_pic FROM Users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0][0] if result else None

def user_nutrition_stats(user_id, days):
    return db.query("""
        SELECT 
            date(e.time) AS day,
            ROUND(SUM(e.eaten_protein), 2) AS total_protein,
            ROUND(SUM(e.eaten_calories), 2) AS total_calories
        FROM Eaten e
        WHERE e.user_id = ?
          AND date(e.time) >= date('now', '-' || ? || ' days', 'localtime')
        GROUP BY day
        ORDER BY day
    """, [user_id, days])
