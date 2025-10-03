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
