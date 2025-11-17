DROP DATABASE IF EXISTS canteen;
CREATE DATABASE IF NOT EXISTS canteen;
USE canteen;

-- Drop users if they exist
DROP USER IF EXISTS 'canteen_admin'@'localhost';
DROP USER IF EXISTS 'canteen_manager'@'localhost';
DROP USER IF EXISTS 'canteen_staff'@'localhost';
DROP USER IF EXISTS 'canteen_readonly'@'localhost';

-- Create Admin User (Full privileges)
CREATE USER 'canteen_admin'@'localhost' IDENTIFIED BY 'admin_pass_123';
GRANT ALL PRIVILEGES ON canteen.* TO 'canteen_admin'@'localhost';
GRANT CREATE USER ON *.* TO 'canteen_admin'@'localhost';

-- Create Manager User (Can manage data but not structure)
CREATE USER 'canteen_manager'@'localhost' IDENTIFIED BY 'manager_pass_123';
GRANT SELECT, INSERT, UPDATE, DELETE ON canteen.* TO 'canteen_manager'@'localhost';
GRANT EXECUTE ON canteen.* TO 'canteen_manager'@'localhost';

-- Create Staff User (Limited CRUD operations)
CREATE USER 'canteen_staff'@'localhost' IDENTIFIED BY 'staff_pass_123';
GRANT SELECT, INSERT, UPDATE ON canteen.Users TO 'canteen_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON canteen.Orders TO 'canteen_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON canteen.Order_Items TO 'canteen_staff'@'localhost';
GRANT SELECT ON canteen.Menu_Items TO 'canteen_staff'@'localhost';
GRANT SELECT ON canteen.Categories TO 'canteen_staff'@'localhost';
GRANT EXECUTE ON canteen.* TO 'canteen_staff'@'localhost';

-- Create Read-Only User (Reporting/Analytics only)
CREATE USER 'canteen_readonly'@'localhost' IDENTIFIED BY 'readonly_pass_123';
GRANT SELECT ON canteen.* TO 'canteen_readonly'@'localhost';

FLUSH PRIVILEGES;

-- Display created users
SELECT User, Host FROM mysql.user WHERE User LIKE 'canteen%';

CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    srn VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    user_type ENUM('student', 'faculty', 'staff') NOT NULL,
    wallet_balance DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_wallet_balance CHECK (wallet_balance >= 0),
    CONSTRAINT chk_email_format CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_phone_format CHECK (phone REGEXP '^[0-9]{10}$' OR phone IS NULL)
);

CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Menu_Items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT NOT NULL,
    item_name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(8,2) NOT NULL,
    stock INT DEFAULT 10,
    is_available BOOLEAN DEFAULT TRUE,
    preparation_time_minutes INT DEFAULT 10,
    image_url VARCHAR(255),
    nutritional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_menu_category FOREIGN KEY (category_id) REFERENCES Categories(category_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_price_positive CHECK (price > 0),
    CONSTRAINT chk_prep_time CHECK (preparation_time_minutes > 0)
);

CREATE TABLE Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10,2) NOT NULL,
    order_status ENUM('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled') DEFAULT 'pending',
    payment_method ENUM('wallet', 'cash', 'upi', 'card') NOT NULL,
    payment_status ENUM('pending', 'completed', 'failed', 'refunded') DEFAULT 'pending',
    estimated_ready_time TIMESTAMP NULL,
    special_instructions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_user FOREIGN KEY (user_id) REFERENCES Users(user_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_total_amount CHECK (total_amount > 0)
);

CREATE TABLE Order_Items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(8,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    special_requests TEXT,
    CONSTRAINT fk_orderitem_order FOREIGN KEY (order_id) REFERENCES Orders(order_id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_orderitem_item FOREIGN KEY (item_id) REFERENCES Menu_Items(item_id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_unit_price_positive CHECK (unit_price > 0),
    UNIQUE KEY uk_order_item (order_id, item_id)
);


CREATE INDEX idx_users_srn ON Users(srn);
CREATE INDEX idx_users_email ON Users(email);
CREATE INDEX idx_menu_category ON Menu_Items(category_id);
CREATE INDEX idx_menu_available ON Menu_Items(is_available);
CREATE INDEX idx_orders_user ON Orders(user_id);
CREATE INDEX idx_orders_status ON Orders(order_status);
CREATE INDEX idx_orders_date ON Orders(order_date);
CREATE INDEX idx_orderitems_order ON Order_Items(order_id);


INSERT INTO Categories (category_name, description) VALUES
('Breakfast', 'Morning breakfast items'),
('Lunch', 'Full meals and lunch items'),
('Snacks', 'Light snacks and finger foods'),
('Beverages', 'Hot and cold drinks'),
('Desserts', 'Sweet treats and desserts'),
('South Indian', 'Traditional South Indian dishes');

INSERT INTO Users (srn, name, email, phone, user_type, wallet_balance) VALUES
('PES2UG23CS001', 'Arjun Sharma', 'arjun.sharma@pes.edu', '9876543210', 'student', 500.00),
('PES2UG23CS002', 'Priya Nair', 'priya.nair@pes.edu', '9876543211', 'student', 750.50),
('PES2UG23CS003', 'Rohit Kumar', 'rohit.kumar@pes.edu', '9876543212', 'student', 300.25),
('PES1FAC001', 'Dr. Suresh Babu', 'suresh.babu@pes.edu', '9876543213', 'faculty', 1000.00),
('PES1STAFF001', 'Lakshmi Devi', 'lakshmi.devi@pes.edu', '9876543214', 'staff', 400.75),
('PES2UG23CS684', 'Meghana Veeramallu', 'meghana.v@pes.edu', '9876543215', 'student', 600.00),
('PES2UG23CS715', 'Yashmitha Shailesh', 'yashmitha.s@pes.edu', '9876543216', 'student', 550.00);

INSERT INTO Menu_Items (category_id, item_name, description, price, stock, preparation_time_minutes) VALUES
(1, 'Idli Sambar', 'Steamed rice cakes with sambar and chutney', 45.00, 20, 5),
(1, 'Masala Dosa', 'Crispy crepe with spiced potato filling', 65.00, 15, 8),
(1, 'Upma', 'Semolina dish with vegetables', 35.00, 25, 7),
(1, 'Poha', 'Flattened rice with onions and spices', 30.00, 30, 5),
(2, 'Veg Thali', 'Complete vegetarian meal with rice, dal, vegetables', 85.00, 12, 10),
(2, 'Chicken Biryani', 'Aromatic basmati rice with spiced chicken', 120.00, 8, 15),
(2, 'Paneer Butter Masala with Rice', 'Rich paneer curry with steamed rice', 95.00, 10, 12),
(2, 'Rajma Rice', 'Kidney bean curry with rice', 70.00, 15, 8),
(3, 'Samosa', 'Fried pastry with spiced potato filling', 15.00, 50, 3),
(3, 'Vada Pav', 'Spiced potato dumpling in bread bun', 25.00, 40, 5),
(3, 'Pani Puri', 'Hollow crispy shells with flavored water', 30.00, 35, 2),
(3, 'Bhel Puri', 'Puffed rice snack with chutneys', 35.00, 30, 3),
(4, 'Masala Chai', 'Spiced Indian tea', 15.00, 100, 3),
(4, 'Filter Coffee', 'South Indian style coffee', 20.00, 100, 3),
(4, 'Fresh Lime Soda', 'Refreshing lime drink', 25.00, 80, 2),
(4, 'Mango Lassi', 'Sweet yogurt drink with mango', 40.00, 50, 3),
(5, 'Gulab Jamun', 'Sweet milk dumplings in syrup', 35.00, 40, 2),
(5, 'Rasmalai', 'Sweet cottage cheese in milk', 45.00, 30, 5),
(6, 'Rava Kesari', 'Semolina sweet dish', 30.00, 25, 8),
(6, 'Coconut Rice', 'Rice with coconut and spices', 50.00, 20, 6);

INSERT INTO Orders (user_id, total_amount, order_status, payment_method, payment_status, special_instructions) VALUES
(1, 110.00, 'completed', 'wallet', 'completed', 'Extra spicy please'),
(2, 85.00, 'ready', 'upi', 'completed', NULL),
(3, 45.00, 'preparing', 'wallet', 'completed', 'Less oil'),
(6, 150.00, 'confirmed', 'wallet', 'completed', 'Pack separately'),
(7, 75.00, 'pending', 'cash', 'pending', NULL);

INSERT INTO Order_Items (order_id, item_id, quantity, unit_price, subtotal, special_requests) VALUES
(1, 2, 1, 65.00, 65.00, 'Extra crispy'),
(1, 14, 2, 20.00, 40.00, NULL),
(1, 9, 1, 15.00, 15.00, NULL),
(2, 5, 1, 85.00, 85.00, NULL),
(3, 1, 1, 45.00, 45.00, 'Extra sambar'),
(4, 6, 1, 120.00, 120.00, 'Medium spice'),
(4, 16, 1, 40.00, 40.00, NULL),
(5, 7, 1, 95.00, 95.00, NULL),
(5, 13, 1, 15.00, 15.00, NULL);


CREATE VIEW Order_Summary AS
SELECT 
    o.order_id,
    u.name as customer_name,
    u.srn,
    o.order_date,
    o.total_amount,
    o.order_status,
    o.payment_method,
    o.payment_status
FROM Orders o
JOIN Users u ON o.user_id = u.user_id;

CREATE VIEW Popular_Items AS
SELECT 
    mi.item_name,
    c.category_name,
    COUNT(oi.order_item_id) as order_count,
    SUM(oi.quantity) as total_quantity_sold,
    mi.price
FROM Menu_Items mi
JOIN Order_Items oi ON mi.item_id = oi.item_id
JOIN Categories c ON mi.category_id = c.category_id
GROUP BY mi.item_id, mi.item_name, c.category_name, mi.price
ORDER BY total_quantity_sold DESC;


DELIMITER //

-- Trigger 1: Auto-calculate subtotal before inserting order item
CREATE TRIGGER before_insert_order_item
BEFORE INSERT ON Order_Items
FOR EACH ROW
BEGIN
    SET NEW.subtotal = NEW.unit_price * NEW.quantity;
END//

-- Trigger 2: Deduct wallet balance after payment completion
CREATE TRIGGER deduct_wallet_after_payment
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.payment_status = 'completed' 
       AND OLD.payment_status <> 'completed'
       AND NEW.payment_method = 'wallet' THEN
        UPDATE Users
        SET wallet_balance = wallet_balance - NEW.total_amount
        WHERE user_id = NEW.user_id;
    END IF;
END//

-- Trigger 3: Auto-disable items when out of stock
CREATE TRIGGER disable_item_when_out_of_stock
BEFORE UPDATE ON Menu_Items
FOR EACH ROW
BEGIN
    IF NEW.stock <= 0 THEN
        SET NEW.is_available = FALSE;
    END IF;
END//

DELIMITER ;


DELIMITER //

-- Procedure 1: Add funds to wallet
CREATE PROCEDURE add_funds_to_wallet(
    IN p_user_id INT,
    IN p_amount DECIMAL(10,2)
)
BEGIN
    IF p_amount <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Amount must be positive';
    ELSE
        UPDATE Users
        SET wallet_balance = wallet_balance + p_amount
        WHERE user_id = p_user_id;
    END IF;
END//

-- Procedure 2: Place new order
CREATE PROCEDURE place_new_order(
    IN p_user_id INT,
    IN p_payment_method ENUM('wallet','cash','upi','card'),
    IN p_item_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_price DECIMAL(8,2);
    DECLARE v_subtotal DECIMAL(10,2);
    DECLARE v_order_id INT;

    SELECT price INTO v_price FROM Menu_Items WHERE item_id = p_item_id;
    SET v_subtotal = v_price * p_quantity;

    INSERT INTO Orders (user_id, total_amount, payment_method, payment_status)
    VALUES (p_user_id, 0, p_payment_method, 'pending');

    SET v_order_id = LAST_INSERT_ID();

    INSERT INTO Order_Items (order_id, item_id, quantity, unit_price)
    VALUES (v_order_id, p_item_id, p_quantity, v_price);

    UPDATE Orders
    SET total_amount = (SELECT SUM(subtotal) FROM Order_Items WHERE order_id = v_order_id)
    WHERE order_id = v_order_id;

    SELECT v_order_id AS order_id, 
           (SELECT total_amount FROM Orders WHERE order_id = v_order_id) AS total_amount;
END//

-- Procedure 3: Add item to existing order
CREATE PROCEDURE add_item_to_order(
    IN p_order_id INT,
    IN p_item_id INT,
    IN p_quantity INT
)
BEGIN
    DECLARE v_price DECIMAL(10,2);

    SELECT price INTO v_price FROM Menu_Items WHERE item_id = p_item_id;

    IF EXISTS (SELECT 1 FROM Order_Items WHERE order_id = p_order_id AND item_id = p_item_id) THEN
        UPDATE Order_Items
        SET quantity = quantity + p_quantity,
            subtotal = (quantity + p_quantity) * unit_price
        WHERE order_id = p_order_id AND item_id = p_item_id;
    ELSE
        INSERT INTO Order_Items (order_id, item_id, quantity, unit_price)
        VALUES (p_order_id, p_item_id, p_quantity, v_price);
    END IF;

    UPDATE Orders
    SET total_amount = (SELECT SUM(subtotal) FROM Order_Items WHERE order_id = p_order_id)
    WHERE order_id = p_order_id;
END//

-- Procedure 4: Update stock after order
CREATE PROCEDURE update_stock_after_order(IN p_order_id INT)
BEGIN
    UPDATE Menu_Items mi
    JOIN Order_Items oi ON mi.item_id = oi.item_id
    SET mi.stock = mi.stock - oi.quantity
    WHERE oi.order_id = p_order_id;

    UPDATE Menu_Items
    SET is_available = FALSE
    WHERE stock <= 0;
END//

-- Procedure 5: DELETE operation - Cancel order and restore stock
CREATE PROCEDURE delete_order(IN p_order_id INT)
BEGIN
    DECLARE v_order_status VARCHAR(20);
    DECLARE v_payment_status VARCHAR(20);
    DECLARE v_payment_method VARCHAR(20);
    DECLARE v_user_id INT;
    DECLARE v_total_amount DECIMAL(10,2);
    
    -- Get order details
    SELECT order_status, payment_status, payment_method, user_id, total_amount
    INTO v_order_status, v_payment_status, v_payment_method, v_user_id, v_total_amount
    FROM Orders
    WHERE order_id = p_order_id;
    
    -- Restore stock
    UPDATE Menu_Items mi
    JOIN Order_Items oi ON mi.item_id = oi.item_id
    SET mi.stock = mi.stock + oi.quantity,
        mi.is_available = TRUE
    WHERE oi.order_id = p_order_id;
    
    -- Refund wallet if payment was completed via wallet
    IF v_payment_status = 'completed' AND v_payment_method = 'wallet' THEN
        UPDATE Users
        SET wallet_balance = wallet_balance + v_total_amount
        WHERE user_id = v_user_id;
    END IF;
    
    -- Delete order items (cascade will handle this, but explicit for clarity)
    DELETE FROM Order_Items WHERE order_id = p_order_id;
    
    -- Delete order
    DELETE FROM Orders WHERE order_id = p_order_id;
    
    SELECT CONCAT('Order ', p_order_id, ' deleted successfully') AS message;
END//

-- Procedure 6: DELETE user (soft delete by deactivating)
CREATE PROCEDURE delete_user(IN p_user_id INT)
BEGIN
    DECLARE v_order_count INT;
    
    -- Check if user has orders
    SELECT COUNT(*) INTO v_order_count
    FROM Orders
    WHERE user_id = p_user_id;
    
    IF v_order_count > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Cannot delete user with existing orders. Cancel orders first.';
    ELSE
        DELETE FROM Users WHERE user_id = p_user_id;
        SELECT CONCAT('User ', p_user_id, ' deleted successfully') AS message;
    END IF;
END//

-- Procedure 7: DELETE menu item
CREATE PROCEDURE delete_menu_item(IN p_item_id INT)
BEGIN
    DECLARE v_order_count INT;
    
    -- Check if item has been ordered
    SELECT COUNT(*) INTO v_order_count
    FROM Order_Items
    WHERE item_id = p_item_id;
    
    IF v_order_count > 0 THEN
        -- Soft delete - mark as unavailable
        UPDATE Menu_Items
        SET is_available = FALSE, stock = 0
        WHERE item_id = p_item_id;
        SELECT CONCAT('Menu item ', p_item_id, ' marked as unavailable (has order history)') AS message;
    ELSE
        -- Hard delete if never ordered
        DELETE FROM Menu_Items WHERE item_id = p_item_id;
        SELECT CONCAT('Menu item ', p_item_id, ' deleted successfully') AS message;
    END IF;
END//

DELIMITER ;

-- =====================================================
-- 8. STORED FUNCTIONS
-- =====================================================

DELIMITER //

-- Function 1: Get wallet balance
CREATE FUNCTION get_wallet_balance(p_user_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE balance DECIMAL(10,2);
    SELECT wallet_balance INTO balance FROM Users WHERE user_id = p_user_id;
    RETURN IFNULL(balance, 0.00);
END//

-- Function 2: Get order total
CREATE FUNCTION get_order_total(p_order_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(subtotal) INTO total
    FROM Order_Items
    WHERE order_id = p_order_id;
    RETURN IFNULL(total, 0.00);
END//

-- Function 3: Get total sales for item
CREATE FUNCTION get_total_sales_for_item(p_item_id INT)
RETURNS DECIMAL(10,2)
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT SUM(subtotal) INTO total
    FROM Order_Items
    WHERE item_id = p_item_id;
    RETURN IFNULL(total, 0.00);
END//

DELIMITER ;

-- =====================================================
-- 9. VERIFICATION QUERIES
-- =====================================================

-- Show database users and privileges
SELECT '=== DATABASE USERS ===' as info;
SELECT User, Host FROM mysql.user WHERE User LIKE 'canteen%';

SELECT '=== USER PRIVILEGES ===' as info;
SHOW GRANTS FOR 'canteen_admin'@'localhost';
SHOW GRANTS FOR 'canteen_manager'@'localhost';
SHOW GRANTS FOR 'canteen_staff'@'localhost';
SHOW GRANTS FOR 'canteen_readonly'@'localhost';

-- Table statistics
SELECT '=== TABLE STATISTICS ===' as info;
SELECT 'Users' as table_name, COUNT(*) as record_count FROM Users
UNION ALL
SELECT 'Categories', COUNT(*) FROM Categories
UNION ALL
SELECT 'Menu_Items', COUNT(*) FROM Menu_Items
UNION ALL
SELECT 'Orders', COUNT(*) FROM Orders
UNION ALL
SELECT 'Order_Items', COUNT(*) FROM Order_Items;

-- Show triggers
SELECT '=== TRIGGERS ===' as info;
SHOW TRIGGERS;

-- Show procedures
SELECT '=== PROCEDURES ===' as info;
SHOW PROCEDURE STATUS WHERE Db = 'canteen';

-- Show functions
SELECT '=== FUNCTIONS ===' as info;
SHOW FUNCTION STATUS WHERE Db = 'canteen';

SELECT '=== SETUP COMPLETE ===' as info;