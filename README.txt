Sushaki Kitchen Order System 🍣🍜
A simple, web-based kitchen order system designed for small restaurants. It features a Flask backend for order processing, CSV logging, and direct-to-printer thermal receipt generation.

Features
Web-based Interface: Easy-to-use interface for taking orders, accessible from any device on the local network.

Dynamic Menu Management: Add, edit, and delete categories and items (including items with options/variants) directly through the UI. Menu changes are saved to menu.json.

ESC/POS Receipt Printing: Sends orders directly to a connected thermal receipt printer using ESC/POS commands.

Order Logging: Saves all orders to daily CSV files (orders_YYYY-MM-DD.csv) for record-keeping.

Numpad Integration: Quick quantity adjustments for selected order items.

Order Notes: Add universal notes for the entire order or specific notes for individual items.

Project Structure
.
├── app.py              # Flask backend server (Python)
├── sushaki.html        # Frontend (HTML, CSS, JavaScript)
├── data/
│   ├── menu.json       # Editable menu data
│   └── orders_YYYY-MM-DD.csv # Daily order logs (auto-created)
├── Start_Sushaki_App.bat # Optional Windows launcher
└── README.md           # This file

Prerequisites
Python 3: Download from python.org.

pip: Python package installer (usually included with Python).

Web Browser: Modern browser (Chrome, Firefox, Edge recommended).

Thermal Receipt Printer: ESC/POS compatible (e.g., 80mm series).

Setup Instructions
1. Clone or Download the Repository (If applicable)
If you're working with Git:

git clone <repository_url>
cd <repository_directory>

Otherwise, ensure all project files are in a single directory.

2. Install Python Dependencies
Open your terminal or command prompt, navigate to the project directory, and run:

pip install Flask pywin32

Flask: Powers the web server.

pywin32: Enables interaction with the Windows printing system (Note: Printing is currently Windows-specific).

3. Printer Configuration (Critical)
Accurate printer setup is essential for receipt printing.

a. Install Printer Drivers:
* Install the correct Windows drivers for your thermal printer.
* Print a test page from Windows to confirm basic functionality.

b. Identify Exact Printer Name:
* In Windows, go to: Control Panel > Hardware and Sound > Devices and Printers (or search "Printers & scanners").
* Find your thermal printer and copy its exact name (case-sensitive). Examples: "80mm Series Printer", "EPSON TM-T20II".

c. Configure app.py:
* Open app.py in a text editor.
* Locate the PRINTER_NAME variable:
python PRINTER_NAME = "80mm Series Printer" 
* Replace "80mm Series Printer" with your printer's exact name:
python PRINTER_NAME = "Your Exact Printer Name Here" # Example: "My POS Printer" 
* Save app.py.

4. Prepare Menu Data
The menu is defined in data/menu.json. You can edit this file manually or through the application's settings interface.

The structure is:

{
  "Category Name 1": [
    { "id": 1, "name": "Item Name 1A", "price": 10.50 },
    { "id": 2, "name": "Item Name 1B", "price": 8.00, "options": ["Option X", "Option Y"] }
  ],
  "Category Name 2": [
    // ... more items
  ]
}

id: Must be a unique number for each item across all categories.

options: (Optional) An array of strings for item variants.

Running the Application
Navigate to Project Directory:
Open your terminal/command prompt and cd into the project folder.

Start the Flask Server:

python app.py

The server will typically start on http://localhost:5000/ or http://0.0.0.0:5000/.

Access in Browser:
Open your web browser and navigate to http://localhost:5000/.

Using Start_Sushaki_App.bat (Windows):

Ensure the .bat file is in the same directory as app.py.

Double-click Start_Sushaki_App.bat to launch the server and open the app in your browser.

How to Use the Interface
Order Panel (Left):

Displays current order number, items, and total.

Use the on-screen Numpad to change quantities of selected items.

"Order Notes": Add comments for the entire order.

Item-specific notes can be added by clicking the pencil icon next to an item in the order list.

New Order: Clears the current order, increments the order number.

Send Order: Prints the receipt (via app.py) and logs the order to a CSV file.

Menu Panel (Right):

Browse categories and click items to add them to the order.

If an item has options, a selection modal will appear.

Settings Gear Icon (⚙️ Bottom Right):

Manage Items: Add, edit, or delete menu items and their options.

Manage Categories: Add or delete categories.

Changes are saved to data/menu.json and update the UI instantly.

Troubleshooting
Cannot Print / Printing Errors:

Verify PRINTER_NAME in app.py: Must exactly match the name in Windows "Devices and Printers".

Printer Status: Check if it's on, connected, has paper, and no error lights.

Drivers: Confirm correct drivers are installed and working.

Server Logs: Look for error messages in the "Sushaki Server" command prompt window (where app.py is running).

pywin32 Errors / "ModuleNotFoundError":

Ensure it's installed: pip install pywin32.

Menu Not Loading / "Error loading menu":

Confirm data/menu.json exists and contains valid JSON.

Check the Flask server console for file access or JSON parsing errors.

Application Not Accessible (e.g., http://localhost:5000/ doesn't load):

Ensure app.py (Flask server) is running without startup errors.

Check if another application is using port 5000. If so, you can change the port in app.py (e.g., app.run(host='0.0.0.0', port=5001, debug=True)).

Future Considerations / Potential Improvements
Cross-platform printing support (e.g., using python-escpos library for direct USB/Network printing).

User authentication for accessing settings.

More detailed sales reports.

Cloud synchronization for menu and orders (e.g., using Firebase/Supabase).
