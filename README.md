# Home Inventory Sales App

A comprehensive web application for managing items that need repair or sale. Uses AI (Claude) to identify items, assess repair needs, generate Bills of Materials, create repair tutorials, and estimate market values.

## Features

- **📷 Photo Upload** - Capture or upload photos of items
- **🤖 AI Item Identification** - Automatically identify items using Claude's vision capabilities
- **💰 Price Estimation** - Get current market value estimates with sources
- **🔧 Repair Assessment** - AI-powered analysis of needed repairs
- **📋 BOM Generation** - Automatic Bill of Materials for repairs
- **📝 Repair Tutorials** - Step-by-step repair instructions
- **📊 Inventory Tracking** - Track price paid, asking price, and potential profit
- **✅ Sales Management** - Mark items as sold and track sales history
- **📈 Statistics Dashboard** - View total inventory value and potential profits

## Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Database**: SQLite
- **AI**: Anthropic Claude API (Claude 3.5 Sonnet)
- **Image Processing**: Pillow

## Prerequisites

- Python 3.8 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

## Installation

### 1. Clone the repository

```bash
cd /home/user/home_inventory
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit the `.env` file and add your Anthropic API key:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
FLASK_SECRET_KEY=your_random_secret_key_here
```

To generate a secure secret key, you can run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Initialize the database

```bash
python database.py
```

### 6. Run the application

```bash
python app.py
```

The application will be available at: **http://localhost:5000**

## Usage Guide

### Adding a New Item

1. Click the **"+ Add New Item"** button
2. **Upload a photo** of the item
3. (Optional) Add a description to help AI identification
4. Click **"Analyze with AI"** to automatically identify the item and get:
   - Item name and category
   - Condition assessment
   - Estimated retail value
   - Repair needs
5. Review and adjust the AI-generated information
6. Add your **price paid** and **asking price**
7. Click **"Save Item"**

### Viewing Item Details

Click on any item card to view full details including:
- Complete item information
- Pricing breakdown and potential profit
- Repair assessment
- Bill of Materials (if generated)
- Repair tutorial (if generated)

### Generating Repair Information

From the item detail view:

1. **Generate BOM**: Click "Generate BOM" to create a detailed parts list with estimated costs
2. **Generate Tutorial**: Click "Generate Tutorial" for step-by-step repair instructions
3. **Recheck Price**: Update the market value estimate at any time

### Managing Sales

1. When you're ready to sell an item, open its details
2. Click **"Mark as Sold"**
3. The item will be moved to the "Sold" status
4. Filter by "Sold" to view your sales history

## Database Schema

### Items Table
- Basic item information (name, category, condition)
- Image path
- AI analysis results (identified name, confidence)
- Pricing (paid, retail value, asking price)
- Repair information (assessment, BOM, tutorial)
- Status (inventory/sold)

### Repair Items Table
- Bill of Materials breakdown
- Part name, description, quantity
- Estimated cost per part
- Purchase URLs/notes

### Sales Table
- Sale records when items are sold
- Sale price, date, buyer info, platform

### Price History Table
- Historical price estimates
- Track value changes over time

## API Endpoints

### Items
- `GET /api/items` - Get all items (optional ?status filter)
- `GET /api/items/<id>` - Get single item
- `POST /api/items` - Create new item
- `PUT /api/items/<id>` - Update item
- `DELETE /api/items/<id>` - Delete item

### AI Operations
- `POST /api/upload` - Upload image
- `POST /api/analyze` - Analyze item with AI
- `POST /api/generate-bom/<id>` - Generate Bill of Materials
- `POST /api/generate-tutorial/<id>` - Generate repair tutorial
- `POST /api/price-check/<id>` - Get updated price estimate

### Sales
- `POST /api/items/<id>/move-to-sales` - Mark item as sold

### Statistics
- `GET /api/stats` - Get inventory statistics

## File Structure

```
home_inventory/
├── app.py                  # Flask application and API routes
├── database.py            # Database models and initialization
├── ai_service.py          # Claude AI integration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── home_inventory.db     # SQLite database (auto-created)
└── static/
    ├── index.html        # Main application page
    ├── css/
    │   └── styles.css    # Application styles
    ├── js/
    │   └── app.js        # Frontend JavaScript
    └── uploads/          # Uploaded images (auto-created)
```

## Configuration

### Changing the Port

Edit `app.py` and modify the last line:
```python
app.run(debug=True, host='0.0.0.0', port=5000)  # Change port here
```

### Maximum Upload Size

Edit `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB default
```

### Allowed Image Types

Edit `app.py`:
```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
```

## Troubleshooting

### "AI service not configured" error
- Make sure you've set `ANTHROPIC_API_KEY` in your `.env` file
- Verify the API key is valid at https://console.anthropic.com/

### Images not displaying
- Check that the `static/uploads` directory exists and is writable
- Verify the image path in the database matches the actual file location

### Database errors
- Delete `home_inventory.db` and run `python database.py` to recreate it
- Make sure you have write permissions in the project directory

### Port already in use
- Change the port in `app.py` or stop the other application using port 5000

## Future Enhancements

Potential features to add:
- [ ] Bulk import from CSV
- [ ] Export to various marketplaces (eBay, Facebook Marketplace)
- [ ] Barcode/QR code scanning
- [ ] Price tracking charts
- [ ] Email notifications for price drops
- [ ] Multi-user support with authentication
- [ ] Mobile app version
- [ ] Integration with Google Lens API
- [ ] Automated listing generation for marketplaces

## Contributing

This is a personal project, but feel free to fork and customize for your own needs!

## License

MIT License - Use freely for personal or commercial purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API endpoint documentation
3. Check the browser console for JavaScript errors
4. Check the Flask console for server errors

## Notes on AI Analysis

- **Accuracy**: AI identification is generally accurate but should be verified
- **Cost**: Each AI analysis uses Claude API tokens (typically $0.01-0.05 per item)
- **Privacy**: Images are sent to Anthropic's API for analysis
- **Rate Limits**: Anthropic API has rate limits; bulk operations may need throttling

## Database Backup

To backup your data:
```bash
cp home_inventory.db home_inventory_backup_$(date +%Y%m%d).db
```

To restore from backup:
```bash
cp home_inventory_backup_YYYYMMDD.db home_inventory.db
```

---

**Happy Selling!** 📦💰
