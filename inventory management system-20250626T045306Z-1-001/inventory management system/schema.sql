-- Inventory Management System Database Schema
-- Created for comprehensive product inventory tracking

-- Enable foreign key constraints (for SQLite)
PRAGMA foreign_keys = ON;

-- ====================================
-- REFERENCE TABLES
-- ====================================

-- Categories table for product categorization
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Brands table for manufacturer information
CREATE TABLE brands (
    brand_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_name VARCHAR(100) NOT NULL UNIQUE,
    country_of_origin VARCHAR(100),
    website VARCHAR(255),
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table for warehouse/storage locations
CREATE TABLE locations (
    location_id VARCHAR(20) PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL,
    warehouse_section VARCHAR(50),
    aisle VARCHAR(10),
    shelf VARCHAR(10),
    zone VARCHAR(50),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table for tracking who created/modified records
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Units of measurement
CREATE TABLE units (
    unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_code VARCHAR(10) NOT NULL UNIQUE,
    unit_name VARCHAR(50) NOT NULL,
    unit_type VARCHAR(20) -- 'quantity', 'weight', 'volume', etc.
);

-- ====================================
-- MAIN PRODUCTS TABLE
-- ====================================

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL,
    brand_id INTEGER,
    model VARCHAR(100),
    description TEXT,
    
    -- Pricing information
    cost_price DECIMAL(10,2) NOT NULL CHECK (cost_price >= 0),
    selling_price DECIMAL(10,2) NOT NULL CHECK (selling_price >= 0),
    markup_percentage DECIMAL(5,2) GENERATED ALWAYS AS (
        CASE 
            WHEN cost_price > 0 THEN ((selling_price - cost_price) / cost_price * 100)
            ELSE 0 
        END
    ) STORED,
    
    -- Inventory tracking
    unit_id INTEGER NOT NULL,
    quantity_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (quantity_in_stock >= 0),
    minimum_stock_level INTEGER NOT NULL DEFAULT 0 CHECK (minimum_stock_level >= 0),
    maximum_stock_level INTEGER NOT NULL CHECK (maximum_stock_level > minimum_stock_level),
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
    reorder_quantity INTEGER NOT NULL CHECK (reorder_quantity > 0),
    
    -- Physical location
    location_id VARCHAR(20),
    
    -- Product attributes
    warranty_period INTEGER DEFAULT 0, -- in months
    is_serialized BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id),
    CONSTRAINT fk_products_brand FOREIGN KEY (brand_id) REFERENCES brands(brand_id),
    CONSTRAINT fk_products_unit FOREIGN KEY (unit_id) REFERENCES units(unit_id),
    CONSTRAINT fk_products_location FOREIGN KEY (location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_products_creator FOREIGN KEY (created_by) REFERENCES users(user_id),
    
    -- Business rules
    CONSTRAINT chk_pricing CHECK (selling_price >= cost_price),
    CONSTRAINT chk_stock_levels CHECK (maximum_stock_level > minimum_stock_level),
    CONSTRAINT chk_reorder_logic CHECK (reorder_point >= minimum_stock_level)
);

-- ====================================
-- INVENTORY MOVEMENT TRACKING
-- ====================================

-- Stock movements table for tracking all inventory changes
CREATE TABLE stock_movements (
    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    movement_type VARCHAR(20) NOT NULL CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT', 'TRANSFER')),
    quantity_change INTEGER NOT NULL, -- positive for IN, negative for OUT
    previous_quantity INTEGER NOT NULL,
    new_quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    total_value DECIMAL(10,2) GENERATED ALWAYS AS (ABS(quantity_change) * COALESCE(unit_cost, 0)) STORED,
    
    -- Movement details
    reference_number VARCHAR(100),
    reason VARCHAR(255),
    notes TEXT,
    
    -- Location tracking
    from_location_id VARCHAR(20),
    to_location_id VARCHAR(20),
    
    -- Audit fields
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_movements_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_movements_from_location FOREIGN KEY (from_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_movements_to_location FOREIGN KEY (to_location_id) REFERENCES locations(location_id),
    CONSTRAINT fk_movements_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- ====================================
-- SERIAL NUMBER TRACKING
-- ====================================

-- Serial numbers table for serialized products
CREATE TABLE serial_numbers (
    serial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'IN_STOCK' CHECK (status IN ('IN_STOCK', 'SOLD', 'DAMAGED', 'RETURNED')),
    purchase_date DATE,
    warranty_start_date DATE,
    warranty_end_date DATE,
    notes TEXT,
    
    -- Audit fields
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_serial_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_serial_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- ====================================
-- SUPPLIER MANAGEMENT
-- ====================================

CREATE TABLE suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product supplier relationships
CREATE TABLE product_suppliers (
    product_supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    supplier_sku VARCHAR(100),
    lead_time_days INTEGER DEFAULT 0,
    minimum_order_quantity INTEGER DEFAULT 1,
    unit_cost DECIMAL(10,2),
    is_preferred BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ps_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_ps_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    CONSTRAINT uk_product_supplier UNIQUE (product_id, supplier_id)
);

-- ====================================
-- PRICE HISTORY TRACKING
-- ====================================

CREATE TABLE price_history (
    price_history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    old_cost_price DECIMAL(10,2),
    new_cost_price DECIMAL(10,2),
    old_selling_price DECIMAL(10,2),
    new_selling_price DECIMAL(10,2),
    change_reason VARCHAR(255),
    effective_date DATE NOT NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_price_product FOREIGN KEY (product_id) REFERENCES products(product_id),
    CONSTRAINT fk_price_creator FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- ====================================
-- INDEXES FOR PERFORMANCE
-- ====================================

-- Product indexes
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_location ON products(location_id);
CREATE INDEX idx_products_stock_level ON products(quantity_in_stock);
CREATE INDEX idx_products_reorder ON products(reorder_point, quantity_in_stock);
CREATE INDEX idx_products_active ON products(is_active);

-- Stock movement indexes
CREATE INDEX idx_movements_product ON stock_movements(product_id);
CREATE INDEX idx_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_movements_date ON stock_movements(created_at);
CREATE INDEX idx_movements_reference ON stock_movements(reference_number);

-- Serial number indexes
CREATE INDEX idx_serial_product ON serial_numbers(product_id);
CREATE INDEX idx_serial_status ON serial_numbers(status);
CREATE INDEX idx_serial_warranty ON serial_numbers(warranty_end_date);

-- Other useful indexes
CREATE INDEX idx_brands_name ON brands(brand_name);
CREATE INDEX idx_categories_name ON categories(category_name);
CREATE INDEX idx_suppliers_name ON suppliers(supplier_name);
CREATE INDEX idx_users_username ON users(username);

-- ====================================
-- VIEWS FOR COMMON QUERIES
-- ====================================

-- Complete product information view
CREATE VIEW v_product_details AS
SELECT 
    p.product_id,
    p.sku,
    p.product_name,
    c.category_name,
    b.brand_name,
    p.model,
    p.description,
    u.unit_name,
    p.cost_price,
    p.selling_price,
    p.markup_percentage,
    p.quantity_in_stock,
    p.minimum_stock_level,
    p.maximum_stock_level,
    p.reorder_point,
    p.reorder_quantity,
    l.location_name,
    l.warehouse_section,
    p.warranty_period,
    p.is_serialized,
    p.is_active,
    CASE 
        WHEN p.quantity_in_stock <= p.reorder_point THEN 'REORDER_NEEDED'
        WHEN p.quantity_in_stock <= p.minimum_stock_level THEN 'LOW_STOCK'
        WHEN p.quantity_in_stock >= p.maximum_stock_level THEN 'OVERSTOCK'
        ELSE 'NORMAL'
    END as stock_status,
    p.created_at,
    usr.username as created_by_user
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN brands b ON p.brand_id = b.brand_id
LEFT JOIN units u ON p.unit_id = u.unit_id
LEFT JOIN locations l ON p.location_id = l.location_id
LEFT JOIN users usr ON p.created_by = usr.user_id;

-- Low stock alert view
CREATE VIEW v_low_stock_alerts AS
SELECT 
    p.sku,
    p.product_name,
    p.quantity_in_stock,
    p.minimum_stock_level,
    p.reorder_point,
    p.reorder_quantity,
    c.category_name,
    b.brand_name,
    l.location_name
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN brands b ON p.brand_id = b.brand_id
LEFT JOIN locations l ON p.location_id = l.location_id
WHERE p.is_active = TRUE 
AND p.quantity_in_stock <= p.reorder_point;

-- Inventory value summary view
CREATE VIEW v_inventory_value AS
SELECT 
    c.category_name,
    b.brand_name,
    COUNT(p.product_id) as product_count,
    SUM(p.quantity_in_stock) as total_quantity,
    SUM(p.quantity_in_stock * p.cost_price) as total_cost_value,
    SUM(p.quantity_in_stock * p.selling_price) as total_selling_value,
    AVG(p.markup_percentage) as avg_markup_percentage
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN brands b ON p.brand_id = b.brand_id
WHERE p.is_active = TRUE
GROUP BY c.category_id, b.brand_id
ORDER BY total_cost_value DESC;

-- ====================================
-- TRIGGERS FOR DATA INTEGRITY
-- ====================================

-- Trigger to update the updated_at timestamp
CREATE TRIGGER tr_products_updated_at
    AFTER UPDATE ON products
    FOR EACH ROW
BEGIN
    UPDATE products 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE product_id = NEW.product_id;
END;

-- Trigger to log stock movements when quantity changes
CREATE TRIGGER tr_products_stock_movement
    AFTER UPDATE OF quantity_in_stock ON products
    FOR EACH ROW
    WHEN OLD.quantity_in_stock != NEW.quantity_in_stock
BEGIN
    INSERT INTO stock_movements (
        product_id, 
        movement_type, 
        quantity_change, 
        previous_quantity, 
        new_quantity,
        reason,
        created_by
    )
    VALUES (
        NEW.product_id,
        CASE 
            WHEN NEW.quantity_in_stock > OLD.quantity_in_stock THEN 'IN'
            ELSE 'OUT'
        END,
        NEW.quantity_in_stock - OLD.quantity_in_stock,
        OLD.quantity_in_stock,
        NEW.quantity_in_stock,
        'Automatic stock adjustment',
        NEW.created_by
    );
END;

-- ====================================
-- INITIAL DATA SETUP
-- ====================================

-- Insert default units
INSERT INTO units (unit_code, unit_name, unit_type) VALUES 
('PCS', 'Pieces', 'quantity'),
('KG', 'Kilograms', 'weight'),
('LTR', 'Liters', 'volume'),
('MTR', 'Meters', 'length'),
('BOX', 'Boxes', 'quantity'),
('SET', 'Sets', 'quantity');

-- Insert initial categories based on your data
INSERT INTO categories (category_id, category_name, description) VALUES
(1, 'Electronics', 'Electronic devices and computer equipment'),
(2, 'Monitors & Displays', 'Computer monitors and display devices'),
(3, 'Audio Equipment', 'Speakers, headphones, microphones and audio devices'),
(4, 'Input Devices', 'Keyboards, mice, webcams and input peripherals'),
(5, 'Printers', 'Printing devices and related equipment'),
(6, 'Networking', 'Network equipment and connectivity devices'),
(7, 'Cameras', 'Digital cameras and photography equipment'),
(8, 'Storage', 'Storage devices and memory solutions'),
(9, 'Gaming', 'Gaming consoles, accessories and equipment'),
(10, 'Office Equipment', 'General office equipment and supplies'),
(11, 'Tools', 'Hand tools and power tools'),
(12, 'Sports Equipment', 'Sports and fitness equipment'),
(13, 'Musical Instruments', 'Musical instruments and audio equipment'),
(14, 'Pet Supplies', 'Pet food, toys and accessories'),
(15, 'Toys', 'Children toys and games');

-- Insert a default admin user
INSERT INTO users (user_id, username, email, full_name, role) VALUES
(1, 'admin', 'admin@company.com', 'System Administrator', 'admin');

-- Insert sample brands from your data
INSERT INTO brands (brand_name) VALUES 
('Apple'), ('Dell'), ('HP'), ('Samsung'), ('LG'), ('ASUS'), ('Sony'), ('Bose'),
('JBL'), ('Logitech'), ('Microsoft'), ('Canon'), ('Epson'), ('Brother'),
('TP-Link'), ('Netgear'), ('Nikon'), ('Seagate'), ('WD'), ('Kingston'),
('PlayStation'), ('Xbox'), ('Nintendo'), ('Razer'), ('Corsair'), ('SteelSeries'),
('Fender'), ('Yamaha'), ('Gibson'), ('Nike'), ('Adidas'), ('LEGO'), ('Mattel');

-- ====================================
-- USEFUL STORED PROCEDURES (if supported)
-- ====================================

-- Note: The following procedures are for databases that support them (like PostgreSQL, MySQL)
-- SQLite doesn't support stored procedures, but these can be implemented as application functions

/*
-- Procedure to update stock levels
CREATE PROCEDURE UpdateStock(
    IN p_product_id INT,
    IN p_quantity_change INT,
    IN p_movement_type VARCHAR(20),
    IN p_reference VARCHAR(100),
    IN p_user_id INT
)
BEGIN
    DECLARE current_stock INT;
    
    SELECT quantity_in_stock INTO current_stock 
    FROM products 
    WHERE product_id = p_product_id;
    
    UPDATE products 
    SET quantity_in_stock = current_stock + p_quantity_change 
    WHERE product_id = p_product_id;
    
    INSERT INTO stock_movements (
        product_id, movement_type, quantity_change, 
        previous_quantity, new_quantity, reference_number, created_by
    ) VALUES (
        p_product_id, p_movement_type, p_quantity_change,
        current_stock, current_stock + p_quantity_change, p_reference, p_user_id
    );
END;
*/