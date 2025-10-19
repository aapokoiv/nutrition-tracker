# Nutrition Tracker

## Application features

* Creating an account and logging in
* Adding ingredients and making meals from them
* Giving meals a class and a name
* Modifying and deleting foods and ingredients you have added
* Searching and sorting foods and ingredients based on name, classes or properities
* Searching what others have added and being able to like them
* Being able to eat (and uneat) liked and own foods
* Being able to set nutrient targets and writing down goals
* Tracking your nutrition intake daily
* Profile with profile picture, statistics and history

## Installation

Download `flask` -library:

```
$ pip install flask
```

Create the database:

```
$ sqlite3 database.db < schema.sql
```

You can run the server like this:

```
$ flask run
```

## App Performance with Large Data

Test dataset parameters:

- **Users:** 10,000  
- **Ingredients per user:** 200  
- **Foods per user:** 100  
- **Foods eaten daily per user:** 10  

**Total records:**

- Users: 10,000  
- Ingredients: 2,000,000  
- Foods: 1,000,000  
- Daily eaten records: up to 100,000  

---

### Query Performance

| Page / Query             | Typical Load Time |
|--------------------------|-----------------|
| Homepage                 | < 0.1 s         |
| Profile                  | < 0.1 s         |
| Foods page               | < 0.1 s         |
| Add/Edit/Delete pages    | < 0.05 s        |
| Search Public Foods      | ~1.2–1.5 s first load, < 0.1 s subsequent loads, searching with query ~0.1–3 s|


- Most queries are **fast** due to indexing and precomputed totals in `Foods`.
- The first load of search is slower because SQLite reads large table pages; subsequent loads are cached and fast.
- Current performance is acceptable and realistic for this application.
- Load time when searching with queries depends on how many results it finds and if it is first search

---