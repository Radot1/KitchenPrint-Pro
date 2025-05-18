1 Install required packages:
pip install flask python-escpos
pip install pywin32 flask

2Identify your printer's USB IDs (Linux):
lsusb
# Look for your printer and note the IDs (format: ID vendor:product)

Update printer configuration in app.py:
PRINTER_VENDOR_ID = 0xYourVendorID  # Change to your printer's vendor ID
PRINTER_PRODUCT_ID = 0xYourProductID  # Change to your printer's product ID

Create a requirements.txt:
flask
python-escpos