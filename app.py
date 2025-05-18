# app.py
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import csv
import os
import win32print
import tempfile
import time
import json

app = Flask(__name__)

# Printer configuration (update with your printer name)
PRINTER_NAME = win32print.GetDefaultPrinter()  # or specify exact name like "EPSON TM-T20II Receipt"

# CSV configuration
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

MENU_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/menu.json')

@app.route('/')
def serve_index():
    return send_from_directory('.', 'sushaki.html')
    
@app.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        with open(MENU_FILE, 'r') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({})

@app.route('/api/menu', methods=['POST'])
def save_menu():
    new_menu_data = request.json
    
    # Save exactly what the frontend sends
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    with open(MENU_FILE, 'w') as f:
        json.dump(new_menu_data, f, indent=2)
    
    return jsonify({"status": "success"})

def print_kitchen_ticket(order_data):
    """Print order to thermal printer on Windows"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f: # Add encoding
            f.write("\n" * 2)
            f.write(" " * 15 + "SUSHAKI RESTAURANT\n") # Your restaurant name
            f.write(" " * 18 + "Kitchen Order\n")
            f.write("-" * 48 + "\n")
            f.write(f"Order #: {order_data.get('number', 'N/A')}\n") # Use .get for safety
            f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            universal_comment = order_data.get('universalComment', '').strip()
            if universal_comment:
                f.write(f"\nORDER NOTES:\n{universal_comment}\n")

            f.write("\nITEMS:\n")

            for item in order_data.get('items', []): # Use .get for safety
                f.write(f"{item.get('quantity', 0)}x {item.get('name', 'Unknown Item')}\n")
                item_comment = item.get('comment', '').strip()
                if item_comment:
                    f.write(f"  - Note: {item_comment}\n")
                # Price might not be needed on kitchen ticket, but if so:
                # f.write(f"  Price: ${item.get('price', 0):.2f} each\n")

            f.write("\n" + "-" * 48 + "\n")
            f.write(" " * 16 + "THANK YOU!\n") # Or other footer
            f.write("\n" * 5)
            temp_filename = f.name

        hprinter = win32print.OpenPrinter(PRINTER_NAME)
        try:
            with open(temp_filename, 'rb') as f_read: # Read as bytes
                raw_data = f_read.read()
            win32print.StartDocPrinter(hprinter, 1, ("Kitchen Order", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, raw_data)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)

        time.sleep(1)
        os.unlink(temp_filename)
        return True

    except Exception as e:
        print(f"Printing error: {str(e)}")
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.unlink(temp_filename)
            except Exception as e_unlink:
                print(f"Error unlinking temp file: {e_unlink}")
        return False

def log_order_to_csv(order_data):
    """Append order to daily CSV file and update total"""
    try:
        os.makedirs(CSV_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(CSV_DIR, f"orders_{date_str}.csv")

        fieldnames = [
            'order_number',
            'timestamp',
            'items', # Will include item comments here
            'universal_comment', # <-- NEW FIELD
            'total',
            'printed'
        ]

        existing_rows = []
        running_total = 0.0
        file_exists = os.path.exists(filename)

        if file_exists:
            with open(filename, 'r', newline='', encoding='utf-8') as f_read:
                reader = csv.DictReader(f_read)
                for row in reader:
                    if row.get('order_number') != 'Total': # Use .get for safety
                        existing_rows.append(row)
                        try:
                            running_total += float(row.get('total', '0').replace('$', ''))
                        except ValueError:
                            print(f"Warning: Could not parse total '{row.get('total')}' from CSV row.")


        # Perform printing before defining 'printed_status'
        printed_status = 'Yes' if print_kitchen_ticket(order_data) else 'No'

        new_order_total = sum(item.get('price', 0) * item.get('quantity', 0) for item in order_data.get('items', []))
        # If recalculating running_total from scratch each time, reset it before loop:
        # running_total = sum(float(r['total'].replace('$', '')) for r in existing_rows if r.get('order_number') != 'Total' and r.get('total'))
        # Then add current order total
        # running_total += new_order_total
        # For simplicity, the original logic of appending is kept, but ensure it's robust.
        # To avoid issues, let's recalculate the total from existing rows + new one
        current_running_total = sum(float(r['total'].replace('$', '')) for r in existing_rows if r.get('order_number') != 'Total' and r.get('total'))
        current_running_total += new_order_total


        new_row = {
            'order_number': order_data.get('number', 'N/A'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': " | ".join(
                f"{item.get('quantity', 0)}x {item.get('name', 'N/A')}" +
                (f" (Note: {item.get('comment','').strip()})" if item.get('comment','').strip() else "") +
                f" (${item.get('price', 0):.2f})"
                for item in order_data.get('items', [])
            ),
            'universal_comment': order_data.get('universalComment', '').strip(), # <-- ADDED
            'total': f"${new_order_total:.2f}",
            'printed': printed_status
        }
        existing_rows.append(new_row) # Add new row before writing

        with open(filename, 'w', newline='', encoding='utf-8') as f_write:
            writer = csv.DictWriter(f_write, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows) # Write all (old + new) order rows

            # Add total row (use the recalculated current_running_total)
            writer.writerow({
                'order_number': 'Total',
                'timestamp': 'End of Day Summary',
                'items': f"{len(existing_rows)} orders", # Number of actual orders
                'universal_comment': '',
                'total': f"${current_running_total:.2f}",
                'printed': ''
            })
        return True
    except Exception as e:
        print(f"CSV logging error: {str(e)}")
        return False

@app.route('/api/orders', methods=['POST'])
def handle_order():
    """Endpoint to receive orders from the frontend"""
    order_data = request.json
    
    if not order_data or 'items' not in order_data:
        return jsonify({"status": "error", "message": "Invalid order data"}), 400
    
    try:
        # Assign order number if not provided
        if 'number' not in order_data:
            order_data['number'] = int(datetime.now().timestamp() % 10000)
        
        # Log order and print ticket
        success = log_order_to_csv(order_data)
        
        if success:
            return jsonify({
                "status": "success",
                "order_number": order_data['number']
            })
        return jsonify({"status": "error", "message": "Failed to process order"}), 500
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Install required packages if missing
    try:
        import win32print
    except ImportError:
        print("Installing required packages...")
        os.system("pip install pywin32 flask")
    
    print(f"CSV files will be saved to: {CSV_DIR}")
    print(f"Using printer: {PRINTER_NAME}")
    app.run(host='0.0.0.0', port=5000, debug=True)