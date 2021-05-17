import sqlite3

connection = sqlite3.connect('records.db')

cursor = connection.cursor()

cursor.execute("""CREATE TABLE history (
        date DATETIME,
        token_supply TEXT,
        price TEXT
    )""")

connection.commit()

connection.close()