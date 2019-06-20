import sqlite3
 
                                   
db = sqlite3.connect('products.db')                                 # Create/open a file called mydb.
cursor = db.cursor()                                                # Get a cursor object

filename = "products.txt"
file = open(filename, "r")                                          # Read file products.txt
for line in file:
    cursor.execute(line)                                            # Execute each query in the file


# Table transactions 
cursor.execute("""CREATE TABLE IF NOT EXISTS transactions(
                                                        transactionid INTEGER PRIMARY KEY AUTOINCREMENT,
                                                        methodid INT,
                                                        timestamp DATETIME,
                                                        transactiontype TEXT,
                                                        status TEXT);""")

# Table items for each item in every transaction        
cursor.execute("""CREATE TABLE IF NOT EXISTS items(
                                                        itemid INTEGER PRIMARY KEY AUTOINCREMENT,
                                                        timestamp DATETIME,
                                                        transactionid INT NOT NULL,
                                                        productid INT NOT NULL,
                                                        deal INT,
                                                        discount INT);""")

print('POS database created successfully!')
  

db.commit()                                                         # Commit changes to database
db.close()                                                          # Close connection to database

