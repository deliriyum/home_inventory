import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DATABASE_PATH = 'home_inventory.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                condition TEXT,
                image_path TEXT,
                ai_identified_name TEXT,
                ai_confidence REAL,
                retail_value REAL,
                retail_value_source TEXT,
                price_paid REAL,
                asking_price REAL,
                repair_assessment TEXT,
                repair_bom TEXT,
                repair_tutorial TEXT,
                status TEXT DEFAULT 'inventory',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Repair items table (BOM breakdown)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repair_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                part_name TEXT NOT NULL,
                part_description TEXT,
                estimated_cost REAL,
                quantity INTEGER DEFAULT 1,
                purchase_url TEXT,
                purchased BOOLEAN DEFAULT 0,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        # Sales history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                sale_price REAL,
                sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                buyer_info TEXT,
                platform TEXT,
                notes TEXT,
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        ''')

        # Price history table (track value estimates over time)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                estimated_value REAL,
                source TEXT,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        print("Database initialized successfully!")

class Item:
    """Helper class for item operations"""

    @staticmethod
    def create(data):
        """Create a new item"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO items (
                    name, description, category, condition, image_path,
                    ai_identified_name, ai_confidence, retail_value,
                    retail_value_source, price_paid, asking_price,
                    repair_assessment, repair_bom, repair_tutorial, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('name'),
                data.get('description'),
                data.get('category'),
                data.get('condition'),
                data.get('image_path'),
                data.get('ai_identified_name'),
                data.get('ai_confidence'),
                data.get('retail_value'),
                data.get('retail_value_source'),
                data.get('price_paid'),
                data.get('asking_price'),
                data.get('repair_assessment'),
                data.get('repair_bom'),
                data.get('repair_tutorial'),
                data.get('status', 'inventory')
            ))
            return cursor.lastrowid

    @staticmethod
    def get_all(status=None):
        """Get all items, optionally filtered by status"""
        with get_db() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute('SELECT * FROM items WHERE status = ? ORDER BY created_at DESC', (status,))
            else:
                cursor.execute('SELECT * FROM items ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_by_id(item_id):
        """Get a single item by ID"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update(item_id, data):
        """Update an item"""
        with get_db() as conn:
            cursor = conn.cursor()
            fields = []
            values = []

            for key, value in data.items():
                if key != 'id':
                    fields.append(f"{key} = ?")
                    values.append(value)

            fields.append("updated_at = ?")
            values.append(datetime.now())
            values.append(item_id)

            query = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(query, values)
            return cursor.rowcount > 0

    @staticmethod
    def delete(item_id):
        """Delete an item"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
            return cursor.rowcount > 0

    @staticmethod
    def move_to_sales(item_id):
        """Change item status to 'sold'"""
        return Item.update(item_id, {'status': 'sold'})

class RepairItem:
    """Helper class for repair BOM operations"""

    @staticmethod
    def create(item_id, data):
        """Add a repair item to an item's BOM"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO repair_items (
                    item_id, part_name, part_description,
                    estimated_cost, quantity, purchase_url, purchased
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                data.get('part_name'),
                data.get('part_description'),
                data.get('estimated_cost'),
                data.get('quantity', 1),
                data.get('purchase_url'),
                data.get('purchased', False)
            ))
            return cursor.lastrowid

    @staticmethod
    def get_by_item(item_id):
        """Get all repair items for a specific item"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM repair_items WHERE item_id = ?', (item_id,))
            return [dict(row) for row in cursor.fetchall()]

if __name__ == '__main__':
    init_db()
