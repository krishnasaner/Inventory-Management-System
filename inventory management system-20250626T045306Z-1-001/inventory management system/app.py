from flask import Flask, render_template, request, redirect, url_for
import os

from inventory_management_system import InventoryDatabase

app = Flask(__name__)
db = InventoryDatabase()

DATA_CSV = os.path.join(os.path.dirname(__file__), "..", "dataset.csv")
if os.path.exists(DATA_CSV):
    db.seed_from_csv(DATA_CSV)


@app.route("/")
def index():
    items = db.get_all_items()
    return render_template("index.html", items=items)


@app.route("/add", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])
        description = request.form.get("description", "")
        db.create_item(name, quantity, price, category, description)
        return redirect(url_for("index"))
    return render_template("add_item.html")


if __name__ == "__main__":
    app.run(debug=True)

