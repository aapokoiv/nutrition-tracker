import db

def get_user_by_id(user_id):
    sql = "SELECT * FROM Users WHERE id = ?"
    result = db.query(sql, [user_id])
    return result[0] if result else None

def get_user_by_username(username):
    sql = "SELECT * FROM Users WHERE username = ?"
    result = db.query(sql, [username])
    return result[0] if result else None

def create_user(username, password_hash):
    sql = "INSERT INTO Users (username, password_hash) VALUES (?, ?)"
    return db.execute(sql, [username, password_hash])   # returns new id

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

def user_7day_stats(user_id):
    data = db.query("""
        SELECT 
            date(e.time) AS day,
            ROUND(SUM(e.eaten_protein), 2) AS total_protein,
            ROUND(SUM(e.eaten_calories), 2) AS total_calories
        FROM Eaten e
        WHERE e.user_id = ?
          AND date(e.time) >= date('now', '-7 days', 'localtime')
        GROUP BY day
        ORDER BY day
    """, [user_id])
    return data