Sushaki Kitchen Order System
A simple web-based kitchen order system with a Flask backend for order processing and receipt printing.

Project Structure
.
├── app.py              # Flask backend server, handles orders and printing
├── sushaki.html        # Frontend HTML, CSS, and JavaScript for the order interface
├── data/               # Directory for data files
│   └── menu.json       # Editable menu data
│   └── orders_YYYY-MM-DD.csv # Daily order logs (created automatically)
├── Start_Sushaki_App.bat # (Optional) Batch file to launch the application on Windows
└── README.md           # This file

Prerequisites
Python 3: Ensure Python 3 is installed on your system. You can download it from python.org.

pip: Python's package installer, usually comes with Python.

Web Browser: A modern web browser (e.g., Chrome, Firefox, Edge).

Thermal Receipt Printer: An ESC/POS compatible thermal receipt printer (e.g., an 80mm series printer).

Setup Instructions
1. Install Python Dependencies
Open a command prompt or terminal and navigate to the project directory. Install the required Python libraries:

pip install Flask pywin32

Flask: For the web server.

pywin32: For interacting with the Windows printing system. This application is currently configured for Windows printing.

2. Printer Setup (Crucial)
For the system to print receipts, you must correctly configure your thermal receipt printer:

a. Install Printer Drivers:
* Ensure that the correct drivers for your thermal receipt printer are installed on the Windows machine where app.py will run.
* Follow the manufacturer's instructions for driver installation.
* After installation, verify that you can print a test page to the printer from Windows.

b. Identify the Exact Printer Name:
* Go to Control Panel > Hardware and Sound > Devices and Printers (or search for "Printers & scanners" in Windows Settings).
* Locate your installed thermal receipt printer in the list.
* Note down the exact name of the printer as it appears in Windows. This is case-sensitive and must be precise (e.g., "80mm Series Printer", "EPSON TM-T20II", "POS-80C").

c. Configure app.py:
* Open the app.py file in a text editor.
* Find the line:
python PRINTER_NAME = "80mm Series Printer" 
* Change "80mm Series Printer" to the exact printer name you noted down in the previous step. For example, if your printer is named "My POS Printer", the line should be:
python PRINTER_NAME = "My POS Printer" 
* Save the app.py file.

3. Prepare Menu Data
Edit the data/menu.json file to define your restaurant's categories and items. The structure is as follows:

{
  "Category Name 1": [
    { "id": 1, "name": "Item Name 1A", "price": 10.50 },
    { "id": 2, "name": "Item Name 1B", "price": 8.00, "options": ["Option X", "Option Y"] }
  ],
  "Category Name 2": [
    { "id": 3, "name": "Item Name 2A", "price": 12.75 }
  ]
}

id: Must be a unique number for each item across all categories.

options: (Optional) An array of strings if the item has variants.

Running the Application
Navigate to Project Directory: Open a command prompt or terminal and go to the directory where app.py, sushaki.html, and the data folder are located.

Start the Flask Server:

python app.py

You should see output indicating the server is running, typically on http://localhost:5000/ or http://0.0.0.0:5000/.

Open in Browser:
Open your web browser and go to http://localhost:5000/.
The Sushaki Kitchen Order System interface should load.

Using the Start_Sushaki_App.bat (Windows Only):
If you have created the Start_Sushaki_App.bat file as provided:

Ensure the .bat file is in the same directory as app.py and sushaki.html.

Double-click Start_Sushaki_App.bat. This will start the server and open the application in your browser automatically.

How to Use
Order Panel (Left):

Shows the current order number, items added, and total.

Use the Numpad to adjust the quantity of a selected item.

Add "Order Notes" for universal comments applying to the whole order.

"New Order": Clears the current order and increments the order number.

"Send Order": Sends the order to the kitchen (prints the receipt via app.py) and logs it to a CSV file in the data directory.

Menu Panel (Right):

Select categories to view items.

Click on an item to add it to the current order. If an item has options, a modal will appear to select one.

Settings Gear (Bottom Right):

Click to open the management modal.

Manage Items: Add, edit, or delete menu items and their options.

Manage Categories: Add or delete categories.

Changes made here are saved to data/menu.json and will reflect immediately in the menu panel.

Troubleshooting
Cannot Print / Printing Errors:

Double-check the PRINTER_NAME in app.py matches exactly with the name in Windows Devices and Printers.

Ensure the printer is turned on, connected, has paper, and no error lights are showing.

Verify printer drivers are correctly installed.

Check the "Sushaki Server" command prompt window (where app.py is running) for any error messages related to printing.

pywin32 not found: Make sure you have installed it via pip install pywin32.

Menu not loading / "Error loading menu":

Ensure data/menu.json exists in the correct location and is valid JSON.

Check the Flask server console for errors.

Application not accessible at http://localhost:5000/:

Confirm the Flask server (app.py) is running and did not encounter an error on startup.

Check if another application is using port 5000.