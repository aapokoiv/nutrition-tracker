CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    profile_pic BLOB,
    goals TEXT DEFAULT '';
    protein_target INTEGER DEFAULT 1,
    calorie_target INTEGER DEFAULT 1
);

CREATE TABLE Ingredients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    user_id REFERENCES Users,
    protein REAL,
    calories INTEGER
);

CREATE TABLE Foods (
    id INTEGER PRIMARY KEY,
    name TEXT,
    user_id REFERENCES Users,
    class TEXT CHECK(class IN ('Breakfast/Supper', 'Lunch/Dinner', 'Snack', 'Drink')),
    is_public INTEGER DEFAULT 1,
    total_protein REAL DEFAULT 0.0,
    total_calories REAL DEFAULT 0.0
);

CREATE TABLE FoodIngredients (
    id INTEGER PRIMARY KEY,
    food_id INTEGER REFERENCES Foods(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES Ingredients(id),
    quantity REAL DEFAULT 1.0
);

CREATE TABLE Eaten (
    id INTEGER PRIMARY KEY,
    user_id REFERENCES Users,
    food_id REFERENCES Foods ON DELETE CASCADE,
    time TEXT DEFAULT (datetime('now')),
    quantity REAL DEFAULT 1.0,
    eaten_protein REAL DEFAULT 0.0,
    eaten_calories REAL DEFAULT 0.0
);

CREATE TABLE Likes (
    user_id INTEGER REFERENCES Users(id) ON DELETE CASCADE,
    food_id INTEGER REFERENCES Foods(id) ON DELETE CASCADE,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, food_id)
);

CREATE INDEX idx_foods_ispublic_name ON Foods(is_public, name);
CREATE INDEX idx_foods_user_ispublic ON Foods(user_id, is_public);
CREATE INDEX idx_foods_public_order ON Foods(is_public, id);
CREATE INDEX idx_foods_user_order ON Foods(user_id, id);
CREATE INDEX idx_foods_class_user ON Foods(class, user_id);
CREATE INDEX idx_ingredients_user_name ON Ingredients(user_id, name);
CREATE INDEX idx_foodingredients_food_ingredient ON FoodIngredients(food_id, ingredient_id);
CREATE INDEX idx_eaten_user_date ON Eaten(user_id, date(time));
CREATE INDEX idx_foods_id ON Foods(id);
CREATE INDEX idx_eaten_user_time ON Eaten(user_id, time);