# app.py
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import csv
import os
import win32print # type: ignore
import tempfile
import time
import json

app = Flask(__name__)

# Printer configuration
PRINTER_NAME = "80mm Series Printer" 

# CSV and Menu File Configuration
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
MENU_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/menu.json')

# --- ESC/POS Commands ---
ESC = b'\x1B'
GS = b'\x1D'

InitializePrinter = ESC + b'@'
BoldOn = ESC + b'E\x01'
BoldOff = ESC + b'E\x00'
DoubleHeightWidth = GS + b'!\x11' # For item name
DoubleHeight = GS + b'!\x01'    # Proposed for option text, used for universal comment
NormalText = GS + b'!\x00'      # For pricing, etc.
SelectFontA = ESC + b'M\x00'
FullCut = GS + b'V\x00'

def to_bytes(s, encoding='cp437'):
    if isinstance(s, bytes):
        return s
    return s.encode(encoding, errors='replace')

# --- New Word Wrap Helper Function ---
def word_wrap_text(text, max_width):
    """
    A simple word wrap function. Breaks words longer than max_width.
    """
    lines = []
    if not text:
        return lines
    
    current_line = []
    current_length = 0
    
    for word in text.split(' '):
        if not word: # handle multiple spaces if any
            continue

        # If current line is empty and word is too long, break the word
        if not current_line and len(word) > max_width:
            start = 0
            while start < len(word):
                lines.append(word[start:start+max_width])
                start += max_width
            continue # Word processed, move to next word

        # If adding the word (plus a space if line isn't empty) fits
        if current_length + len(word) + (1 if current_line else 0) <= max_width:
            current_line.append(word)
            current_length += len(word) + (1 if len(current_line) > 1 else 0) # Add 1 for space if not first word
        else:
            # Word doesn't fit, finalize current line
            if current_line:
                lines.append(" ".join(current_line))
            
            # Start new line with current word
            # If this new word itself is too long, break it
            if len(word) > max_width:
                start = 0
                while start < len(word):
                    lines.append(word[start:start+max_width])
                    start += max_width
                current_line = []
                current_length = 0
            else:
                current_line = [word]
                current_length = len(word)
            
    if current_line: # Add any remaining line
        lines.append(" ".join(current_line))
        
    return lines if lines else [""] # Return [""] for empty input to ensure a line is processed

@app.route('/')
def serve_index():
    return send_from_directory('.', 'sushaki.html')

@app.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({})

@app.route('/api/menu', methods=['POST'])
def save_menu():
    new_menu_data = request.json
    os.makedirs(os.path.dirname(MENU_FILE), exist_ok=True)
    with open(MENU_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_menu_data, f, indent=2)
    return jsonify({"status": "success"})

def print_kitchen_ticket(order_data):
    try:
        ticket_content = bytearray()
        ticket_content += InitializePrinter
        # ticket_content += SelectFontA # Font A is often default, GS ! commands affect current font

        NORMAL_FONT_LINE_WIDTH = 42
        EFFECTIVE_LARGE_FONT_LINE_WIDTH = NORMAL_FONT_LINE_WIDTH // 2

        ticket_content += NormalText + BoldOff # Default state for headers
        restaurant_name = "SUSHAKI RESTAURANT"
        padding_restaurant = " " * ((NORMAL_FONT_LINE_WIDTH - len(restaurant_name)) // 2)
        ticket_content += to_bytes(padding_restaurant + restaurant_name + "\n")
        
        header_text = "Kitchen Order"
        padding_header = " " * ((NORMAL_FONT_LINE_WIDTH - len(header_text)) // 2)
        ticket_content += to_bytes(padding_header + header_text + "\n")
        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n")

        # Order Number - Large and Bold
        ticket_content += SelectFontA + DoubleHeightWidth + BoldOn # Ensure Font A before styling
        order_num_text = f"Order #: {order_data.get('number', 'N/A')}"
        ticket_content += to_bytes(order_num_text + "\n")
        # Reset to normal for time, then switch for items title
        ticket_content += SelectFontA + NormalText + BoldOff 

        ticket_content += to_bytes(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        ticket_content += BoldOn + to_bytes("ITEMS:\n") + BoldOff # "ITEMS:" title normal size, bold
        grand_total = 0.0

        for item in order_data.get('items', []):
            item_quantity = item.get('quantity', 0)
            item_name_orig = item.get('name', 'Unknown Item')
            item_price_unit = item.get('price', 0.0)
            line_total = item_quantity * item_price_unit
            grand_total += line_total

            # --- Item Name and Quantity Line(s) - Large & Bold with Word Wrap ---
            ticket_content += SelectFontA + DoubleHeightWidth + BoldOn # Item name is Large & Bold
            
            qty_prefix_str = f"{item_quantity}x "
            
            width_for_name_on_first_line = EFFECTIVE_LARGE_FONT_LINE_WIDTH - len(qty_prefix_str)
            
            first_line_name_part = ""
            remaining_name_for_wrap = item_name_orig

            if len(item_name_orig) <= width_for_name_on_first_line:
                first_line_name_part = item_name_orig
                remaining_name_for_wrap = ""
            else:
                temp_first_part = item_name_orig[:width_for_name_on_first_line + 1] 
                wrap_at = temp_first_part.rfind(' ')
                
                if wrap_at > 0: 
                    first_line_name_part = item_name_orig[:wrap_at]
                    remaining_name_for_wrap = item_name_orig[wrap_at+1:]
                else: 
                    first_line_name_part = item_name_orig[:width_for_name_on_first_line]
                    remaining_name_for_wrap = item_name_orig[width_for_name_on_first_line:]
            
            ticket_content += to_bytes(qty_prefix_str + first_line_name_part.strip() + "\n")

            if remaining_name_for_wrap.strip():
                indent_str = " " * len(qty_prefix_str) 
                sub_lines_max_width = EFFECTIVE_LARGE_FONT_LINE_WIDTH - len(indent_str)
                wrapped_name_lines = word_wrap_text(remaining_name_for_wrap.strip(), sub_lines_max_width)
                for line in wrapped_name_lines:
                    ticket_content += to_bytes(indent_str + line.strip() + "\n")
            
            # --- SELECTED OPTION ---
            selected_option = item.get('selectedOption', '').strip()
            if selected_option:
                # Switch to DoubleHeight font for the option line, not bold
                ticket_content += SelectFontA + DoubleHeight + BoldOff # << MODIFIED FONT HERE
                option_line = f"  Option: {selected_option}" # Indent with 2 spaces
                ticket_content += to_bytes(option_line + "\n")
            
            # Reset font for subsequent lines like pricing and comments.
            ticket_content += SelectFontA + NormalText + BoldOff 
            # --- End Item Name / Option ---

            # Line 2: Pricing - Normal Font A, Not Bold, Right Aligned
            pricing_text = f"({item_quantity} x ${item_price_unit:.2f} = ${line_total:.2f})"
            padding_pricing = " " * (NORMAL_FONT_LINE_WIDTH - len(pricing_text))
            ticket_content += to_bytes(padding_pricing + pricing_text + "\n")

            # Line 3 (Optional): Item Comment - Font A, Normal Size, Bold, indented
            item_comment = item.get('comment', '').strip()
            if item_comment:
                # Item comment is NormalText, but Bold
                ticket_content += BoldOn 
                ticket_content += to_bytes(f"    Note: {item_comment}\n") 
                ticket_content += BoldOff # Turn off bold after comment
            
            ticket_content += to_bytes("\n") 

        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n")

        # TOTAL line - Normal size, Bold
        ticket_content += SelectFontA + NormalText + BoldOn 
        total_string = f"TOTAL: ${grand_total:.2f}"
        padding_total = " " * (NORMAL_FONT_LINE_WIDTH - len(total_string))
        ticket_content += to_bytes(padding_total + total_string + "\n")
        ticket_content += BoldOff # Turn off bold

        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n\n")

        universal_comment = order_data.get('universalComment', '').strip()
        if universal_comment:
            # "ORDER NOTES:" title is NormalText, Bold
            ticket_content += SelectFontA + NormalText + BoldOn 
            ticket_content += to_bytes("ORDER NOTES:\n")
            ticket_content += BoldOff # Turn off bold for the actual comment text

            # Universal comment text itself is DoubleHeight
            ticket_content += SelectFontA + DoubleHeight # Ensure Font A, set DoubleHeight
            
            # Corrected wrapping for DoubleHeight (normal width)
            max_line_len_comment = NORMAL_FONT_LINE_WIDTH 
            wrapped_universal_comment_lines = word_wrap_text(universal_comment, max_line_len_comment)
            for line in wrapped_universal_comment_lines:
                ticket_content += to_bytes(line + "\n")

            ticket_content += SelectFontA + NormalText # Reset from DoubleHeight for any following text
            ticket_content += to_bytes("\n")

        ticket_content += to_bytes("\n" * 3) 
        ticket_content += FullCut 

        hprinter = win32print.OpenPrinter(PRINTER_NAME)
        try:
            win32print.StartDocPrinter(hprinter, 1, ("Kitchen Order ESCPOS", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, bytes(ticket_content))
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)
        
        return True

    except Exception as e:
        print(f"Printing error (ESC/POS): {str(e)}")
        return False
        
# (The rest of your app.py code: log_order_to_csv, handle_order, Flask routes, if __name__ == '__main__', etc.
# should remain the same as in the previous complete file version I provided that had these functions.)
# For completeness, here are the other critical functions assuming they are up-to-date:

def log_order_to_csv(order_data):
    """Append order to daily CSV file and update total"""
    try:
        os.makedirs(CSV_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(CSV_DIR, f"orders_{date_str}.csv")

        fieldnames = [
            'order_number', 'timestamp', 'items', 
            'universal_comment', 'total', 'printed'
        ]

        existing_rows = []
        if os.path.exists(filename):
            with open(filename, 'r', newline='', encoding='utf-8') as f_read:
                reader = csv.DictReader(f_read)
                for row in reader:
                    if row.get('order_number') != 'Total':
                        existing_rows.append(row)
        
        printed_status = 'Yes' if print_kitchen_ticket(order_data) else 'No'

        new_order_total = sum(item.get('price', 0) * item.get('quantity', 0) for item in order_data.get('items', []))
        
        # Correctly calculate running total from existing valid rows
        current_running_total_from_csv = 0.0
        for r in existing_rows:
            if r.get('order_number') != 'Total':
                try:
                    # Ensure 'total' key exists and is not empty before trying to replace/convert
                    total_val_str = r.get('total', '0').replace('$', '')
                    if total_val_str: # Check if string is not empty after stripping $
                         current_running_total_from_csv += float(total_val_str)
                except ValueError:
                    print(f"Warning: Could not parse total '{r.get('total')}' from CSV row for order {r.get('order_number')}.")

        final_running_total = current_running_total_from_csv + new_order_total


        new_row = {
            'order_number': order_data.get('number', 'N/A'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items': " | ".join(
                f"{item.get('quantity', 0)}x {item.get('name', 'N/A')}" +
                (f" (Note: {item.get('comment','').strip()})" if item.get('comment','').strip() else "") +
                f" (${item.get('price', 0):.2f})"
                for item in order_data.get('items', [])
            ),
            'universal_comment': order_data.get('universalComment', '').strip(),
            'total': f"${new_order_total:.2f}",
            'printed': printed_status
        }
        existing_rows.append(new_row)

        with open(filename, 'w', newline='', encoding='utf-8') as f_write:
            writer = csv.DictWriter(f_write, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
            writer.writerow({
                'order_number': 'Total', 'timestamp': 'End of Day Summary',
                'items': f"{len(existing_rows)} orders", 
                'universal_comment': '', 'total': f"${final_running_total:.2f}",
                'printed': ''
            })
        return True
    except Exception as e:
        print(f"CSV logging error: {str(e)}")
        return False

@app.route('/api/orders', methods=['POST'])
def handle_order():
    order_data = request.json
    if not order_data or 'items' not in order_data:
        return jsonify({"status": "error", "message": "Invalid order data"}), 400
    try:
        if 'number' not in order_data: 
            order_data['number'] = int(datetime.now().timestamp() % 10000) 
        
        success = log_order_to_csv(order_data)
        
        if success:
            return jsonify({"status": "success", "order_number": order_data['number']})
        else: 
            return jsonify({"status": "error", "message": "Failed to process order (log/print)"}), 500
    except Exception as e: 
        print(f"Error in handle_order: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    try:
        import win32print
    except ImportError:
        print("pywin32 not found. Please ensure it is installed (pip install pywin32).")
    
    print(f"CSV files will be saved to: {CSV_DIR}")
    if PRINTER_NAME: 
        print(f"Attempting to use printer: {PRINTER_NAME}")
    else:
        print("Warning: PRINTER_NAME is not set. Printing will likely fail.")
    app.run(host='0.0.0.0', port=5000, debug=True)