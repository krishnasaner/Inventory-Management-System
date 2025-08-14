from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
import os
from inventory_management_system import InventoryDatabase

app = Flask(__name__)
db = InventoryDatabase()

# Path to CSV dataset
DATA_CSV = os.path.join(os.path.dirname(__file__), "dataset.csv")
if os.path.exists(DATA_CSV):
    db.seed_from_csv(DATA_CSV)

# --------- Helper to serialize DB items ---------
def serialize_item(item):
    """Convert DB result to JSON-friendly dict."""
    if isinstance(item, dict):
        return item  # Already a dict

    # If object or tuple, map attributes/positions
    return {
        "id": getattr(item, "id", None) if hasattr(item, "id") else item[0],
        "name": getattr(item, "name", None) if hasattr(item, "name") else item[1],
        "category": getattr(item, "category", None) if hasattr(item, "category") else item[2],
        "quantity": getattr(item, "quantity_in_stock", None) if hasattr(item, "quantity_in_stock") else item[3],
        "price": getattr(item, "selling_price", None) if hasattr(item, "selling_price") else item[4],
        "description": getattr(item, "description", "") if hasattr(item, "description") else (item[5] if len(item) > 5 else "")
    }

# --------- FRONTEND ROUTE ---------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# --------- API ROUTES ---------
@app.route("/api/items", methods=["GET"])
def get_items():
    items = db.get_all_items()
    return jsonify([serialize_item(i) for i in items])

@app.route("/api/items", methods=["POST"])
def add_item():
    if not request.is_json:
        abort(400, description="Expected JSON body")
    data = request.get_json()
    try:
        name = data["name"].strip()
        category = data["category"].strip()
        quantity = int(data["quantity"])
        price = float(data["price"])
        description = data.get("description", "").strip()

        if not name or not category:
            abort(400, description="Name and category are required.")

        new_id = db.create_item(name, quantity, price, category, description)
        created_item = db.get_item_by_id(new_id) if hasattr(db, "get_item_by_id") else None

        return jsonify({
            "success": True,
            "item": serialize_item(created_item) if created_item else {
                "id": new_id, "name": name, "category": category,
                "quantity": quantity, "price": price, "description": description
            }
        }), 201
    except (KeyError, ValueError) as e:
        abort(400, description=f"Invalid data: {e}")

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    existing = db.get_item_by_id(item_id) if hasattr(db, "get_item_by_id") else None
    if not existing:
        return jsonify({"success": False, "error": "Item not found"}), 404

    ok = db.delete_item(item_id)
    if not ok:
        return jsonify({"success": False, "error": "Delete failed"}), 500

    return jsonify({"success": True})

# --------- ERROR HANDLERS ---------
@app.errorhandler(400)
def bad_request(err):
    return jsonify({"success": False, "error": "bad_request", "message": err.description}), 400

@app.errorhandler(404)
def not_found(err):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "not_found"}), 404
    return err, 404

@app.errorhandler(500)
def server_error(err):
    return jsonify({"success": False, "error": "server_error"}), 500

if __name__ == "__main__":
    app.run(debug=True)

