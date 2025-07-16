CREATE TABLE IF NOT EXISTS published_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_name TEXT NOT NULL,
    year_from INTEGER NOT NULL,
    month_from INTEGER NOT NULL,
    year_to INTEGER NOT NULL,
    month_to INTEGER NOT NULL,
    price INTEGER NOT NULL,
    reason TEXT NULL
);