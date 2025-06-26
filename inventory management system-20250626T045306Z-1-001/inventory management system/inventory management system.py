import tkinter as tk
from tkinter import messagebox, ttk
import csv

inventory = {}

def add_item():
    name = name_var.get().strip()
    qty = qty_var.get()
    price = price_var.get()
    if name == "" or qty == "" or price == "":
        messagebox.showwarning("Input Error", "All fields are required!")
        return
    try:
        qty = int(qty)
        price = float(price)
    except ValueError:
        messagebox.showerror("Invalid Input", "Quantity must be integer, Price must be number.")
        return
        return

    if name in inventory:
        messagebox.showwarning("Duplicate", f"{name} already exists!")
    else:
        inventory[name] = {"quantity": qty, "price": price}
        messagebox.showinfo("Success", f"{name} added!")
        refresh_table()

def update_item():
    name = name_var.get().strip()
    if name not in inventory:
        messagebox.showerror("Not Found", f"{name} not found.")
        return
    try:
        qty = int(qty_var.get())
        price = float(price_var.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Quantity must be integer, Price must be number.")
        return
    inventory[name] = {"quantity": qty, "price": price}
    messagebox.showinfo("Updated", f"{name} updated!")
    refresh_table()

def delete_item():
    name = name_var.get().strip()
    if name in inventory:
        del inventory[name]
        messagebox.showinfo("Deleted", f"{name} deleted!")
        refresh_table()
    else:
        messagebox.showerror("Not Found", f"{name} not in inventory.")

def search_item():
    name = name_var.get().strip()
    if name in inventory:
        item = inventory[name]
        qty_var.set(item['quantity'])
        price_var.set(item['price'])
    else:
        messagebox.showinfo("Not Found", f"{name} not found.")

def export_to_csv():
    with open("inventory_export.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Item", "Quantity", "Price", "Total"])
        for item, detail in inventory.items():
            writer.writerow([item, detail['quantity'], detail['price'], detail['quantity'] * detail['price']])
    messagebox.showinfo("Exported", "Data exported to inventory_export.csv")

def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    for item, details in inventory.items():
        total = details['quantity'] * details['price']
        tree.insert("", "end", values=(item, details['quantity'], details['price'], total))

# UI Setup
root = tk.Tk()
root.title("Inventory Management System")

tk.Label(root, text="Item Name").grid(row=0, column=0, padx=10, pady=5)
tk.Label(root, text="Quantity").grid(row=1, column=0, padx=10, pady=5)
tk.Label(root, text="Price").grid(row=2, column=0, padx=10, pady=5)

name_var = tk.StringVar()
qty_var = tk.StringVar()
price_var = tk.StringVar()

tk.Entry(root, textvariable=name_var).grid(row=0, column=1)
tk.Entry(root, textvariable=qty_var).grid(row=1, column=1)
tk.Entry(root, textvariable=price_var).grid(row=2, column=1)

# Buttons
tk.Button(root, text="Add Item", command=add_item).grid(row=3, column=0, pady=10)
tk.Button(root, text="Update Item", command=update_item).grid(row=3, column=1)
tk.Button(root, text="Delete Item", command=delete_item).grid(row=3, column=2)
tk.Button(root, text="Search Item", command=search_item).grid(row=4, column=0)
tk.Button(root, text="Export CSV", command=export_to_csv).grid(row=4, column=1)

# Table
columns = ("Item", "Quantity", "Price", "Total")
tree = ttk.Treeview(root, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
tree.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
