CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT,
    protein_target INTEGER,
    calorie_target INTEGER
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
    class TEXT CHECK(class IN ('Breakfast/Supper', 'Lunch/Dinner', 'Snack', 'Drink'))
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
    food_id REFERENCES Foods,
    time TEXT
);