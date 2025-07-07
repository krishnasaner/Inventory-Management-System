import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import datetime
import os

class InventoryDatabase:
    def __init__(self, db_path="inventory.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def create_item(self, name, quantity, price, category, description=""):
        """Create a new inventory item"""
        if not name or not category:
            raise ValueError("Name and category are required")
        if quantity < 0 or price < 0:
            raise ValueError("Quantity and price must be non-negative")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO items (name, category, quantity, price, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, category, quantity, price, description))
            conn.commit()
    
    def get_all_items(self, category=None, search_term=None):
        """Retrieve all items with optional filtering"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM items WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if search_term:
                query += " AND (name LIKE ? OR description LIKE ?)"
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            query += " ORDER BY name"
            return [dict(row) for row in conn.execute(query, params).fetchall()]
    
    def get_item_by_id(self, item_id):
        """Get a specific item by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
            return dict(row) if row else None
    
    def update_item(self, item_id, name, quantity, price, category, description=""):
        """Update an existing item"""
        if not name or not category:
            raise ValueError("Name and category are required")
        if quantity < 0 or price < 0:
            raise ValueError("Quantity and price must be non-negative")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE items SET name=?, category=?, quantity=?, price=?, 
                description=?, updated_at=CURRENT_TIMESTAMP WHERE id=?
            ''', (name, category, quantity, price, description, item_id))
            conn.commit()
    
    def delete_item(self, item_id):
        """Delete an item"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()
    
    def get_categories(self):
        """Get all unique categories"""
        with sqlite3.connect(self.db_path) as conn:
            return [row[0] for row in conn.execute("SELECT DISTINCT category FROM items ORDER BY category").fetchall()]
    
    def get_summary_stats(self):
        """Get inventory summary statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = conn.execute('''
                SELECT 
                    COUNT(*) as total_items,
                    SUM(quantity) as total_quantity,
                    SUM(quantity * price) as total_value,
                    COUNT(DISTINCT category) as total_categories
                FROM items
            ''').fetchone()
            return dict(zip(['total_items', 'total_quantity', 'total_value', 'total_categories'], stats))

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Inventory Management System")
        self.root.geometry("1200x800")
        
        self.db = InventoryDatabase()
        self.selected_item_id = None
        
        self.setup_variables()
        self.setup_ui()
        self.load_data()
    
    def setup_variables(self):
        """Initialize tkinter variables"""
        self.name_var = tk.StringVar()
        self.qty_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.description_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.filter_category_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Input frame
        input_frame = ttk.LabelFrame(main_frame, text="Item Details", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Input fields
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.name_var, width=20).grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(input_frame, text="Category:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, width=18)
        self.category_combo.grid(row=0, column=3, padx=(0, 10))
        
        ttk.Label(input_frame, text="Quantity:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.qty_var, width=20).grid(row=1, column=1, padx=(0, 10))
        
        ttk.Label(input_frame, text="Price:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.price_var, width=18).grid(row=1, column=3, padx=(0, 10))
        
        ttk.Label(input_frame, text="Description:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(input_frame, textvariable=self.description_var, width=50).grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E))
        
        # Buttons frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Update Item", command=self.update_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Delete Item", command=self.delete_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear Fields", command=self.clear_fields).pack(side=tk.LEFT, padx=(0, 5))
        
        # Search and filter frame
        search_frame = ttk.LabelFrame(main_frame, text="Search & Filter", padding="10")
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=1, padx=(0, 10))
        search_entry.bind('<KeyRelease>', lambda e: self.refresh_table())
        
        ttk.Label(search_frame, text="Filter by Category:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.filter_combo = ttk.Combobox(search_frame, textvariable=self.filter_category_var, width=20)
        self.filter_combo.grid(row=0, column=3, padx=(0, 10))
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_table())
        
        # Import/Export buttons
        ttk.Button(search_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=4, padx=(0, 5))
        ttk.Button(search_frame, text="Import CSV", command=self.import_csv).grid(row=0, column=5, padx=(0, 5))
        ttk.Button(search_frame, text="Show Stats", command=self.show_stats).grid(row=0, column=6)
        
        # Table frame
        table_frame = ttk.LabelFrame(main_frame, text="Inventory Items", padding="10")
        table_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Treeview
        columns = ('ID', 'Name', 'Category', 'Quantity', 'Price', 'Total Value', 'Updated')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=120, anchor=tk.CENTER)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scroll.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_item_select)
        self.tree.bind('<Double-1>', self.on_item_double_click)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
    
    def load_data(self):
        """Load initial data"""
        self.refresh_table()
        self.update_categories()
    
    def validate_inputs(self):
        """Validate input fields"""
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Name is required!")
            return False
        if not self.category_var.get().strip():
            messagebox.showerror("Validation Error", "Category is required!")
            return False
        try:
            qty = int(self.qty_var.get())
            if qty < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Quantity must be a non-negative integer!")
            return False
        try:
            price = float(self.price_var.get())
            if price < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Validation Error", "Price must be a non-negative number!")
            return False
        return True
    
    def add_item(self):
        """Add a new item"""
        if not self.validate_inputs():
            return
        
        try:
            self.db.create_item(
                name=self.name_var.get().strip(),
                quantity=int(self.qty_var.get()),
                price=float(self.price_var.get()),
                category=self.category_var.get().strip(),
                description=self.description_var.get().strip()
            )
            messagebox.showinfo("Success", "Item added successfully!")
            self.clear_fields()
            self.refresh_table()
            self.update_categories()
            self.status_var.set("Item added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add item: {str(e)}")
    
    def update_item(self):
        """Update selected item"""
        if not self.selected_item_id:
            messagebox.showwarning("Selection Error", "Please select an item to update!")
            return
        
        if not self.validate_inputs():
            return
        
        try:
            self.db.update_item(
                item_id=self.selected_item_id,
                name=self.name_var.get().strip(),
                quantity=int(self.qty_var.get()),
                price=float(self.price_var.get()),
                category=self.category_var.get().strip(),
                description=self.description_var.get().strip()
            )
            messagebox.showinfo("Success", "Item updated successfully!")
            self.clear_fields()
            self.refresh_table()
            self.update_categories()
            self.status_var.set("Item updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update item: {str(e)}")
    
    def delete_item(self):
        """Delete selected item"""
        if not self.selected_item_id:
            messagebox.showwarning("Selection Error", "Please select an item to delete!")
            return
        
        try:
            item = self.db.get_item_by_id(self.selected_item_id)
            if not item:
                messagebox.showerror("Error", "Item not found!")
                return
            
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{item['name']}'?"):
                self.db.delete_item(self.selected_item_id)
                messagebox.showinfo("Success", f"Item '{item['name']}' deleted successfully!")
                self.clear_fields()
                self.refresh_table()
                self.update_categories()
                self.status_var.set(f"Deleted item: {item['name']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete item: {str(e)}")
    
    def clear_fields(self):
        """Clear all input fields"""
        self.name_var.set("")
        self.qty_var.set("")
        self.price_var.set("")
        self.category_var.set("")
        self.description_var.set("")
        self.selected_item_id = None
    
    def refresh_table(self):
        """Refresh the items table"""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            category_filter = self.filter_category_var.get() if self.filter_category_var.get() else None
            search_term = self.search_var.get().strip() if self.search_var.get().strip() else None
            
            items = self.db.get_all_items(category=category_filter, search_term=search_term)
            
            for item in items:
                total_value = item['quantity'] * item['price']
                updated_date = item['updated_at'][:16] if item['updated_at'] else ""
                
                self.tree.insert("", "end", values=(
                    item['id'],
                    item['name'],
                    item['category'],
                    item['quantity'],
                    f"${item['price']:.2f}",
                    f"${total_value:.2f}",
                    updated_date
                ))
            
            self.status_var.set(f"Showing {len(items)} items")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh table: {str(e)}")
    
    def update_categories(self):
        """Update category dropdown lists"""
        try:
            categories = self.db.get_categories()
            self.category_combo['values'] = categories
            self.filter_combo['values'] = [''] + categories
        except Exception as e:
            print(f"Error updating categories: {e}")
    
    def on_item_select(self, event):
        """Handle item selection in table"""
        selection = self.tree.selection()
        if selection:
            item_id = self.tree.item(selection[0])['values'][0]
            try:
                item = self.db.get_item_by_id(item_id)
                if item:
                    self.selected_item_id = item_id
                    self.name_var.set(item['name'])
                    self.qty_var.set(str(item['quantity']))
                    self.price_var.set(str(item['price']))
                    self.category_var.set(item['category'])
                    self.description_var.set(item['description'])
                    self.status_var.set(f"Selected: {item['name']}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load item details: {str(e)}")
    
    def on_item_double_click(self, event):
        """Handle double-click on item"""
        self.on_item_select(event)
    
    def sort_column(self, col):
        """Sort table by column"""
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        items.sort(key=lambda x: x[0])
        for index, (_, child) in enumerate(items):
            self.tree.move(child, '', index)
    
    def export_csv(self):
        """Export inventory to CSV file"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Inventory"
            )
            if filename:
                items = self.db.get_all_items()
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['ID', 'Name', 'Category', 'Quantity', 'Price',
                                   'Total Value', 'Description', 'Created', 'Updated'])
                    for item in items:
                        total_value = item['quantity'] * item['price']
                        writer.writerow([
                            item['id'], item['name'], item['category'], item['quantity'],
                            item['price'], total_value, item['description'],
                            item['created_at'], item['updated_at']
                        ])
                messagebox.showinfo("Success", f"Inventory exported to {filename}")
                self.status_var.set(f"Exported {len(items)} items to CSV")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")
    
    def import_csv(self):
        """Import inventory from CSV file"""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Import Inventory"
            )
            if filename:
                imported_count = 0
                error_count = 0
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        try:
                            self.db.create_item(
                                name=row.get('Name', '').strip(),
                                quantity=int(row.get('Quantity', 0)),
                                price=float(row.get('Price', 0)),
                                category=row.get('Category', '').strip(),
                                description=row.get('Description', '').strip()
                            )
                            imported_count += 1
                        except Exception as e:
                            error_count += 1
                            print(f"Error importing row {row}: {e}")
                
                self.refresh_table()
                self.update_categories()
                message = f"Import completed!\nSuccessfully imported: {imported_count} items"
                if error_count > 0:
                    message += f"\nErrors: {error_count} items"
                messagebox.showinfo("Import Complete", message)
                self.status_var.set(f"Imported {imported_count} items")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import CSV: {str(e)}")
    
    def show_stats(self):
        """Show inventory statistics"""
        try:
            stats = self.db.get_summary_stats()
            message = f"""Inventory Statistics:
            
Total Items: {stats['total_items']}
Total Quantity: {stats['total_quantity']}
Total Value: ${stats['total_value']:.2f}
Categories: {stats['total_categories']}"""
            messagebox.showinfo("Inventory Statistics", message)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get statistics: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()