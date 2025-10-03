import db

def get_user_by_username(username):
    sql = "SELECT * FROM users WHERE username = ?"
    result = db.query(sql, [username])
    return result[0] if result else None

def update_protein_target(username, protein_target):
    sql = "UPDATE users SET protein_target = ? WHERE username = ?"
    db.execute(sql, [protein_target, username])

def update_calorie_target(username, calorie_target):
    sql = "UPDATE users SET calorie_target = ? WHERE username = ?"
    db.execute(sql, [calorie_target, username])
