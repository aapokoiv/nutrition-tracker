CREATE TABLE Users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE Incredients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    protein INTEGER,
    calories INTEGER
)

CREATE TABLE Foods (
    id INTEGER PRIMARY KEY,
    name TEXT,
    incredient_id REFERENCES Incredients,
    class_id REFERENCES Classes
)

CREATE TABLE Classes (
    id INTEGER PRIMARY KEY,
    name TEXT
)

CREATE TABLE Eaten (
    id INTEGER PRIMARY KEY,
    user_id REFERENCES Users,
    food_id REFERENCES Foods,
    time TEXT
)