from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from pathlib import Path
from werkzeug.utils import secure_filename
import json

from database import init_db, Item, RepairItem, get_db
from ai_service import AIService

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

CORS(app)

# Ensure upload directory exists
Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True, exist_ok=True)

# Initialize AI service
try:
    ai_service = AIService()
except ValueError as e:
    print(f"Warning: {e}")
    ai_service = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Routes

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items, optionally filtered by status"""
    status = request.args.get('status')
    items = Item.get_all(status)
    return jsonify(items)

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get a single item by ID"""
    item = Item.get_by_id(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Get repair items for this item
    repair_items = RepairItem.get_by_item(item_id)
    item['repair_items'] = repair_items

    return jsonify(item)

@app.route('/api/items', methods=['POST'])
def create_item():
    """Create a new item (without image analysis - that's separate)"""
    data = request.json
    item_id = Item.create(data)
    return jsonify({'id': item_id, 'message': 'Item created successfully'}), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """Update an existing item"""
    data = request.json
    success = Item.update(item_id, data)
    if success:
        return jsonify({'message': 'Item updated successfully'})
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete an item"""
    success = Item.delete(item_id)
    if success:
        return jsonify({'message': 'Item deleted successfully'})
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload an image file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid name conflicts
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        return jsonify({
            'message': 'File uploaded successfully',
            'filename': filename,
            'path': filepath
        }), 201

    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/analyze', methods=['POST'])
def analyze_item():
    """
    Analyze an uploaded image with AI
    Expects JSON with: { "image_path": "path/to/image", "description": "optional user description" }
    """
    if not ai_service:
        return jsonify({'error': 'AI service not configured. Please set ANTHROPIC_API_KEY'}), 500

    data = request.json
    image_path = data.get('image_path')
    user_description = data.get('description')

    if not image_path or not os.path.exists(image_path):
        return jsonify({'error': 'Invalid image path'}), 400

    # Perform AI analysis
    analysis = ai_service.analyze_item(image_path, user_description)

    return jsonify(analysis)

@app.route('/api/generate-bom/<int:item_id>', methods=['POST'])
def generate_bom(item_id):
    """Generate Bill of Materials for an item"""
    if not ai_service:
        return jsonify({'error': 'AI service not configured'}), 500

    item = Item.get_by_id(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Generate BOM
    bom = ai_service.generate_repair_bom(
        item['ai_identified_name'] or item['name'],
        item.get('repair_assessment', ''),
        item.get('description', '')
    )

    # Save BOM items to database
    for bom_item in bom:
        RepairItem.create(item_id, bom_item)

    # Update item with BOM JSON
    Item.update(item_id, {'repair_bom': json.dumps(bom)})

    return jsonify({
        'message': 'BOM generated successfully',
        'bom': bom
    })

@app.route('/api/generate-tutorial/<int:item_id>', methods=['POST'])
def generate_tutorial(item_id):
    """Generate repair tutorial for an item"""
    if not ai_service:
        return jsonify({'error': 'AI service not configured'}), 500

    item = Item.get_by_id(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Get BOM items
    repair_items = RepairItem.get_by_item(item_id)

    # Generate tutorial
    tutorial = ai_service.generate_repair_tutorial(
        item['ai_identified_name'] or item['name'],
        item.get('repair_assessment', ''),
        repair_items
    )

    # Save tutorial
    Item.update(item_id, {'repair_tutorial': tutorial})

    return jsonify({
        'message': 'Tutorial generated successfully',
        'tutorial': tutorial
    })

@app.route('/api/price-check/<int:item_id>', methods=['POST'])
def price_check(item_id):
    """Get updated price estimate for an item"""
    if not ai_service:
        return jsonify({'error': 'AI service not configured'}), 500

    item = Item.get_by_id(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Get price estimate
    price_info = ai_service.quick_price_check(
        item['ai_identified_name'] or item['name'],
        item.get('condition', 'used')
    )

    # Update item with new price estimate
    Item.update(item_id, {
        'retail_value': price_info.get('average_price', 0),
        'retail_value_source': f"{price_info.get('market_info', '')} (Sources: {', '.join(price_info.get('sources', []))})"
    })

    # Log price history
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO price_history (item_id, estimated_value, source)
            VALUES (?, ?, ?)
        ''', (item_id, price_info.get('average_price', 0), 'AI Price Check'))

    return jsonify(price_info)

@app.route('/api/items/<int:item_id>/move-to-sales', methods=['POST'])
def move_to_sales(item_id):
    """Move an item to sales status"""
    data = request.json or {}

    # Update item status
    success = Item.move_to_sales(item_id)

    if success and data.get('create_sale_record'):
        # Create sale record if requested
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sales (item_id, sale_price, buyer_info, platform, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item_id,
                data.get('sale_price'),
                data.get('buyer_info'),
                data.get('platform'),
                data.get('notes')
            ))

    if success:
        return jsonify({'message': 'Item moved to sales'})
    return jsonify({'error': 'Item not found'}), 404

@app.route('/api/repair-items/<int:item_id>', methods=['GET'])
def get_repair_items(item_id):
    """Get all repair items (BOM) for an item"""
    repair_items = RepairItem.get_by_item(item_id)
    return jsonify(repair_items)

@app.route('/api/repair-items/<int:item_id>', methods=['POST'])
def add_repair_item(item_id):
    """Add a repair item to an item's BOM"""
    data = request.json
    repair_item_id = RepairItem.create(item_id, data)
    return jsonify({'id': repair_item_id, 'message': 'Repair item added'}), 201

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get inventory statistics"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Total items
        cursor.execute('SELECT COUNT(*) as count FROM items')
        total_items = cursor.fetchone()['count']

        # Items by status
        cursor.execute('SELECT status, COUNT(*) as count FROM items GROUP BY status')
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

        # Total inventory value
        cursor.execute('SELECT SUM(retail_value) as total FROM items WHERE status = "inventory"')
        inventory_value = cursor.fetchone()['total'] or 0

        # Total potential profit
        cursor.execute('''
            SELECT SUM(asking_price - price_paid) as profit
            FROM items
            WHERE status = "inventory" AND asking_price IS NOT NULL AND price_paid IS NOT NULL
        ''')
        potential_profit = cursor.fetchone()['profit'] or 0

        return jsonify({
            'total_items': total_items,
            'status_counts': status_counts,
            'inventory_value': round(inventory_value, 2),
            'potential_profit': round(potential_profit, 2)
        })

if __name__ == '__main__':
    # Initialize database
    init_db()

    # Run the app
    print("Starting Home Inventory Sales App...")
    print("Access the app at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
