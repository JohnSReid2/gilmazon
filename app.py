from flask import Flask, render_template, send_file, redirect, url_for
import sqlite3
import io
import logging
import random

#filename='record.log', 
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
app = Flask(__name__)

rarity_map = {
        "C": "Common",
        "U": "Uncommon",
        "R": "Rare",
        "V": "Very Rare",
        "L": "Legendary",
        "A": "Artifact"
    }

# Route for the homepage
@app.route("/")
def index():
    app.logger.debug("STARTING LOGGING")
    # Connect to the SQLite database
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    
    # Query to fetch product data
    cursor.execute("SELECT id, name, random_price, type, extra_type, rarity FROM items")
    items = cursor.fetchall()

    #remove any items that are not in the shop
    cursor.execute("SELECT id FROM shop")
    shop_items = cursor.fetchall()
    shop_items = [item[0] for item in shop_items]
    items = [item for item in items if item[0] in shop_items]


    
    # Replace rarity code with full rarity name
    for i, item in enumerate(items):
        rarity_code = item[5]  # The rarity is at index 4
        items[i] = item[:5] + (rarity_map.get(rarity_code, rarity_code),)

        rarity_code = item[5]  # The rarity is at index 4
        items[i] = list(item)  # Convert tuple to list so we can modify it
        
        # Map rarity code to full rarity name
        items[i][5] = rarity_map.get(rarity_code, rarity_code)  # Update rarity
        
        # Combine type and extra_type
        if item[4]:  # If extra_type exists (not None or empty)
            items[i][3] = f"{item[3]} - {item[4]}"  # Type - Extra Type

    products = []

    for item in items:
        product = [
            item[0], # id 0
            item[1], # name 1
            item[2], # price 2
            item[3], # type 3
            item[5] # rarity 4
        ]
        products.append(product)
    # Map rarity code to full rarity
    

    conn.close()
    return render_template("index.html", products=products)

# Route to serve image from the database
@app.route("/image/<int:id>")
def get_image(id):

    # Connect to the SQLite database
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()
    # Fetch the image BLOB for the given product ID
    cursor.execute("SELECT image FROM items WHERE id = ?", (id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        # Convert BLOB to a file-like object
        image_blob = result[0]
        return send_file(io.BytesIO(image_blob), mimetype="image/jpeg")
    else:
        return "Image not found", 404
    
@app.route("/product/<int:item_id>")
def product_detail(item_id):
    # Connect to the SQLite database
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # Query to fetch detailed product data
    cursor.execute("SELECT name, random_price, type, extra_type, rarity, html FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    conn.close()

    if item:
        # Map rarity code to full rarity
        rarity = rarity_map.get(item[4], item[4])
        
        # Combine type and extra_type
        type_extra = f"{item[2]} - {item[3]}" if item[3] else item[2]

        description = item[5].decode('utf-8') if isinstance(item[5], bytes) else item[5]


        product = [
            item_id, # id 0
            item[0], # name 1
            item[1], # price 2
            type_extra, # type 3
            rarity, # rarity 4
            description, # html 5
        ]
        
        # Return the item details to the template
        return render_template("product_detail.html", product=product)
    else:
        return "Product not found", 404


def generate_store():
    # Define rarity categories and the number of items to include for each
    rarity_distribution = {
        "C": 5,  # Common: 5 items
        "U": 5,  # Uncommon: 3 items
        "R": 5,   # Rare: 2 items
        "V": 4,   # Very Rare: 1 item
        "L": 2,   # Legendary: 1 item
        "A": 1   # Artifact: 1 item
    }

    # Connect to the database
    conn = sqlite3.connect("inventory.db")
    cursor = conn.cursor()

    # List to store selected item IDs
    selected_items = []

    for rarity, count in rarity_distribution.items():
        # Query to fetch all item IDs for the given rarity
        cursor.execute("SELECT id FROM items WHERE rarity = ?", (rarity,))
        items = cursor.fetchall()  # List of tuples [(id1,), (id2,), ...]

        if len(items) <= count:
            # If fewer items are available than needed, select all
            selected_items.extend([item[0] for item in items])
        else:
            # Otherwise, randomly select the required number
            selected_items.extend([item[0] for item in random.sample(items, count)])

    # Clear the existing shop table
    cursor.execute("DELETE FROM shop")

    # Insert selected item IDs into the shop table
    cursor.executemany("INSERT INTO shop (id) VALUES (?)", [(item_id,) for item_id in selected_items])

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    return 

@app.route("/generate_store", methods=["POST"])
def generate_store_route():
    # Call the generate_store function
    generate_store()
    app.logger.info(f"Generated store with items")
    return redirect(url_for("index"))


if __name__ == "__main__":
    print("Starting server")
    #clear the log file
    open('record.log', 'w').close()

    app.run('0.0.0.0', debug=True)    