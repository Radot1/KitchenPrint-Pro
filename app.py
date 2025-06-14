# app.py
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import csv
import os
import win32print # type: ignore
import tempfile
import time
import json
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')

# Printer configuration
PRINTER_NAME = "80mm Series Printer" 

# CSV and Menu File Configuration
CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
MENU_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/menu.json')

# --- ESC/POS Commands (Updated to match app DUMMY.py for more formatting options) ---
ESC = b'\x1B'
GS = b'\x1D'

InitializePrinter = ESC + b'@'
BoldOn = ESC + b'E\x01'
BoldOff = ESC + b'E\x00'
DoubleHeightWidth = GS + b'!\x11'  # Double Height and Double Width
DoubleHeight = GS + b'!\x01'       # Double Height only
DoubleWidth = GS + b'!\x10'        # Double Width only
NormalText = GS + b'!\x00'
AlignLeft = ESC + b'a\x00'
AlignCenter = ESC + b'a\x01'
AlignRight = ESC + b'a\x02'
SelectFontA = ESC + b'M\x00' # Standard Font A
SelectFontB = ESC + b'M\x01' # Smaller Font B
FullCut = GS + b'V\x00'


def to_bytes(s, encoding='cp437'):
    if isinstance(s, bytes):
        return s
    return s.encode(encoding, errors='replace')

# --- Word Wrap Helper Function (Updated to match app DUMMY.py for better wrapping) ---
def word_wrap_text(text, max_width, initial_indent="", subsequent_indent=""):
    lines = []
    if not text: return lines
    
    paragraphs = text.split('\n')
    
    for i, paragraph_text in enumerate(paragraphs):
        if not paragraph_text.strip() and i < len(paragraphs) -1 : 
            lines.append(initial_indent if not lines else subsequent_indent) 
            continue

        current_line = []
        current_length = 0
        words = paragraph_text.split(' ')
        
        current_indent = initial_indent if not lines and not any(lines) else subsequent_indent
        
        for word_idx, word in enumerate(words):
            if not word: 
                if current_line: current_line.append("") 
                continue

            available_width_for_word = max_width - len(current_indent) - current_length - (1 if current_line else 0)
            if len(word) > available_width_for_word and not current_line : 
                part_fits = word[:available_width_for_word]
                remaining_part = word[available_width_for_word:]
                lines.append(current_indent + part_fits)
                
                while remaining_part:
                    available_width_for_remaining = max_width - len(subsequent_indent)
                    part_fits = remaining_part[:available_width_for_remaining]
                    remaining_part = remaining_part[available_width_for_remaining:]
                    lines.append(subsequent_indent + part_fits)
                current_line = []
                current_length = 0
                current_indent = subsequent_indent 
                continue

            if current_length + len(word) + (1 if current_line else 0) <= (max_width - len(current_indent)):
                current_line.append(word)
                current_length += len(word) + (1 if len(current_line) > 1 else 0) 
            else:
                if current_line: 
                    lines.append(current_indent + " ".join(current_line))
                
                current_line = [word]
                current_length = len(word)
                current_indent = subsequent_indent 
        
        if current_line: 
            lines.append(current_indent + " ".join(current_line))
            
    return lines if lines else [initial_indent]

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

# --- THIS IS THE MAIN MODIFIED FUNCTION ---
def print_kitchen_ticket(order_data, copy_info="", original_timestamp_str=None):
    hprinter = None
    try:
        ticket_content = bytearray()
        ticket_content += InitializePrinter
        
        NORMAL_FONT_LINE_WIDTH = 42
        SMALL_FONT_LINE_WIDTH = 56 

        # --- Header Section (As per app DUMMY.py) ---
        ticket_content += AlignCenter + SelectFontA + DoubleHeightWidth + BoldOn
        restaurant_name = "To Sushaki" 
        ticket_content += to_bytes(restaurant_name + "\n")
        ticket_content += BoldOff 
        
        ticket_content += AlignCenter + SelectFontA + NormalText
        header_text = "Kitchen Order"
        if copy_info:
             header_text += f" - {copy_info.upper()}"
        ticket_content += to_bytes(header_text + "\n")
        
        ticket_content += AlignLeft 
        
        ticket_content += SelectFontA + DoubleHeightWidth + BoldOn
        order_num_text = f"Order #: {order_data.get('number', 'N/A')}"
        ticket_content += to_bytes(order_num_text + "\n")
        ticket_content += BoldOff

        ticket_content += SelectFontA + NormalText
        time_to_display = original_timestamp_str if original_timestamp_str else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ticket_content += to_bytes(f"Time: {time_to_display}\n")
        
        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n")
        
        # --- Items Section (Logic from app DUMMY.py) ---
        grand_total = 0.0
        for item_idx, item in enumerate(order_data.get('items', [])):
            item_quantity = item.get('quantity', 0)
            item_name_orig = item.get('name', 'Unknown Item')
            item_price_unit = float(item.get('price', 0.0))
            
            selected_options = item.get('selectedOptions', [])
            total_options_price = 0.0
            if selected_options and isinstance(selected_options, list):
                for option in selected_options:
                    total_options_price += float(option.get('price', 0.0))

            line_total = item_quantity * (item_price_unit + total_options_price)
            grand_total += line_total

            left_side = f"{item_quantity}x {item_name_orig}"
            right_side = f"EUR {line_total:.2f}"

            large_text_width = len(left_side) * 2
            normal_text_width = len(right_side)
            
            # Smartly print large item name and normal price on the same line if it fits
            if large_text_width + normal_text_width < NORMAL_FONT_LINE_WIDTH:
                ticket_content += SelectFontA + DoubleHeightWidth + BoldOn
                ticket_content += to_bytes(left_side)
                
                ticket_content += NormalText + BoldOff
                
                padding_size = NORMAL_FONT_LINE_WIDTH - large_text_width - normal_text_width
                padding = " " * padding_size
                ticket_content += to_bytes(padding)
                
                ticket_content += to_bytes(right_side + "\n")
            else:
                # Handle multi-line items if they don't fit
                ticket_content += SelectFontA + DoubleHeightWidth + BoldOn
                DOUBLE_WIDTH_LINE_CHARS = NORMAL_FONT_LINE_WIDTH // 2
                wrapped_name_lines = word_wrap_text(left_side, DOUBLE_WIDTH_LINE_CHARS)
                
                for line in wrapped_name_lines[:-1]:
                    ticket_content += to_bytes(line + "\n")
                
                last_line = wrapped_name_lines[-1]
                last_line_width = len(last_line) * 2
                
                available_space = NORMAL_FONT_LINE_WIDTH - last_line_width
                padding = " " * max(0, available_space - normal_text_width)
                
                ticket_content += to_bytes(last_line)
                
                ticket_content += NormalText + BoldOff + to_bytes(padding + right_side + "\n")
                ticket_content += AlignLeft

            ticket_content += NormalText + BoldOff 

            # Print selected options (indented)
            if selected_options and isinstance(selected_options, list):
                for option in selected_options:
                    option_name = option.get('name', 'N/A')
                    option_price = float(option.get('price', 0.0))
                    price_change_str = ""
                    if option_price != 0:
                        price_change_str = f" ({'+' if option_price > 0 else ''}EUR {option_price:.2f})"
                    
                    option_line = f"  -> {option_name}{price_change_str}"
                    wrapped_option_lines = word_wrap_text(option_line, NORMAL_FONT_LINE_WIDTH, initial_indent="  ", subsequent_indent="    ") 
                    for opt_line_part in wrapped_option_lines:
                        ticket_content += to_bytes(opt_line_part + "\n")

            # Print item comment (indented)
            item_comment = item.get('comment', '').strip()
            if item_comment:
                ticket_content += BoldOn
                wrapped_comments = word_wrap_text(f"Note: {item_comment}", NORMAL_FONT_LINE_WIDTH, initial_indent="    ", subsequent_indent="    ")
                for comment_line in wrapped_comments:
                     ticket_content += to_bytes(comment_line + "\n")
                ticket_content += BoldOff                  
            
            # Add a separator between items
            if item_idx < len(order_data.get('items', [])) - 1:
                ticket_content += to_bytes("." * NORMAL_FONT_LINE_WIDTH + "\n")

        # --- Footer Section (As per app DUMMY.py) ---
        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n")
        ticket_content += SelectFontA + DoubleHeightWidth + BoldOn + AlignRight
        total_string = f"TOTAL: EUR {grand_total:.2f}"
        ticket_content += to_bytes(total_string + "\n")
        ticket_content += BoldOff + AlignLeft
        
        ticket_content += SelectFontA + NormalText
        ticket_content += to_bytes("-" * NORMAL_FONT_LINE_WIDTH + "\n\n") 
        
        universal_comment = order_data.get('universalComment', '').strip()
        if universal_comment:
            ticket_content += SelectFontA + NormalText + BoldOn 
            ticket_content += to_bytes("ORDER NOTES:\n") + BoldOff 
            ticket_content += SelectFontA + NormalText 
            wrapped_universal_comment_lines = word_wrap_text(universal_comment, NORMAL_FONT_LINE_WIDTH, initial_indent="", subsequent_indent="") 
            for line in wrapped_universal_comment_lines:
                ticket_content += to_bytes(line + "\n")
            ticket_content += to_bytes("\n")
        
        ticket_content += to_bytes("\n")
        ticket_content += AlignCenter + SelectFontB
        disclaimer_text = "This is not a legal receipt and is for informational purposes only."
        wrapped_disclaimer_lines = word_wrap_text(disclaimer_text, SMALL_FONT_LINE_WIDTH)
        for line in wrapped_disclaimer_lines:
            ticket_content += to_bytes(line + "\n")

        ticket_content += SelectFontA + AlignLeft
            
        ticket_content += to_bytes("\n\n\n\n") 
        ticket_content += FullCut

        hprinter = win32print.OpenPrinter(PRINTER_NAME)
        try:
            doc_name = f"Order_{order_data.get('number', 'N/A')}_Ticket_{copy_info.replace(' ','_')}"
            win32print.StartDocPrinter(hprinter, 1, (doc_name, None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, bytes(ticket_content))
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
        finally:
            win32print.ClosePrinter(hprinter)
        
        return True

    except Exception as e:
        app.logger.error(f"Printing error (ESC/POS): {str(e)}")
        if hprinter:
             win32print.ClosePrinter(hprinter)
        return False
        
def log_order_to_csv(order_data):
    try:
        os.makedirs(CSV_DIR, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(CSV_DIR, f"orders_{date_str}.csv")

        fieldnames = [
            'order_number', 'table_number', 'timestamp', 'items_summary', 
            'universal_comment', 'order_total', 'printed_status', 'items_json'
        ]

        # Print the receipt twice, without the copy info
        app.logger.info(f"Printing receipt for order #{order_data.get('number', 'N/A')}")
        print_success1 = print_kitchen_ticket(order_data, copy_info="Kitchen")
        time.sleep(1)  # Small delay for the printer queue
        print_success2 = print_kitchen_ticket(order_data, copy_info="Customer")

        if print_success1 and print_success2:
            printed_status = 'Yes (2 copies)'
        elif print_success1 or print_success2:
            printed_status = 'Partial (1 copy)'
        else:
            printed_status = 'No'

        existing_rows = []
        file_exists = os.path.exists(filename)
        if file_exists:
            with open(filename, 'r', newline='', encoding='utf-8') as f_read:
                reader = csv.DictReader(f_read)
                for row in reader:
                    if row.get('order_number', '').lower() != 'total':
                        existing_rows.append(row)
        
        new_order_total = 0.0
        items_summary_parts = []
        for item in order_data.get('items', []):
            item_price = float(item.get('price', 0))
            
            total_options_price = 0.0
            option_summary_parts = []
            selected_options = item.get('selectedOptions', [])
            if selected_options and isinstance(selected_options, list):
                for option in selected_options:
                    option_price = float(option.get('price', 0.0))
                    total_options_price += option_price
                    option_name = option.get('name', '')
                    price_str = f" (+{option_price:.2f})" if option_price > 0 else ""
                    option_summary_parts.append(f"{option_name}{price_str}")
            
            new_order_total += (item_price + total_options_price) * item.get('quantity', 0)
            
            summary_part = f"{item.get('quantity', 0)}x {item.get('name', 'N/A')}"
            if option_summary_parts:
                summary_part += f" (Opts: {', '.join(option_summary_parts)})"

            if item.get('comment','').strip():
                 summary_part += f" (Note: {item.get('comment','').strip()})"
            items_summary_parts.append(summary_part)

        items_summary_str = " | ".join(items_summary_parts)

        new_row = {
            'order_number': order_data.get('number', 'N/A'),
            'table_number': order_data.get('tableNumber', 'N/A'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'items_summary': items_summary_str,
            'items_json': json.dumps(order_data.get('items', [])),
            'universal_comment': order_data.get('universalComment', '').strip(),
            'order_total': f"€{new_order_total:.2f}",
            'printed_status': printed_status
        }
        existing_rows.append(new_row)

        with open(filename, 'w', newline='', encoding='utf-8') as f_write:
            writer = csv.DictWriter(f_write, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_rows)
            
        return True
    except Exception as e:
        app.logger.error(f"CSV logging error: {str(e)}")
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
        app.logger.error(f"Error in handle_order: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- NEW ENDPOINTS FOR REPRINT FUNCTIONALITY ---

@app.route('/api/todays_orders_for_reprint', methods=['GET'])
def get_todays_orders_for_reprint():
    try:
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(CSV_DIR, f"orders_{today_date_str}.csv")
        
        if not os.path.exists(filename):
            return jsonify([])

        orders_for_reprint = []
        with open(filename, 'r', newline='', encoding='utf-8') as f_read:
            reader = csv.DictReader(f_read)
            for row in reader:
                if row.get('order_number', '').lower() not in ['total', ''] and row.get('items_json'): 
                    orders_for_reprint.append({
                        'order_number': row.get('order_number'),
                        'table_number': row.get('table_number', 'N/A'),
                        'timestamp': row.get('timestamp')
                    })
        orders_for_reprint.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return jsonify(orders_for_reprint)

    except Exception as e:
        app.logger.error(f"Error fetching today's orders for reprint: {str(e)}")
        return jsonify({"status": "error", "message": f"Could not fetch today's orders: {str(e)}"}), 500


@app.route('/api/reprint_order', methods=['POST'])
def reprint_order_endpoint():
    data = request.json
    order_number_to_reprint = data.get('order_number')

    if not order_number_to_reprint:
        return jsonify({"status": "error", "message": "Order number is required for reprint."}), 400

    try:
        today_date_str = datetime.now().strftime("%Y-%m-%d")
        filename = os.path.join(CSV_DIR, f"orders_{today_date_str}.csv")

        if not os.path.exists(filename):
            return jsonify({"status": "error", "message": f"No orders found for today."}), 404

        found_order_row = None
        with open(filename, 'r', newline='', encoding='utf-8') as f_read:
            reader = csv.DictReader(f_read)
            for row in reader:
                if row.get('order_number') == str(order_number_to_reprint):
                    found_order_row = row
                    break
        
        if not found_order_row:
            return jsonify({"status": "error", "message": f"Order #{order_number_to_reprint} not found in today's records."}), 404

        items_list_str = found_order_row.get('items_json', '[]')
        items_list = json.loads(items_list_str)
        
        reprint_order_data = {
            'number': found_order_row.get('order_number'),
            'tableNumber': found_order_row.get('table_number', 'N/A'),
            'items': items_list,
            'universalComment': found_order_row.get('universal_comment', '')
        }
        original_timestamp = found_order_row.get('timestamp')

        app.logger.info(f"Attempting to reprint order #{order_number_to_reprint}")

        # Reprint the receipt twice, with a simple "Reprint" header
        reprint_success1 = print_kitchen_ticket(reprint_order_data, 
                                               copy_info="Reprint", 
                                               original_timestamp_str=original_timestamp)
        time.sleep(1) # Small delay for the printer
        reprint_success2 = print_kitchen_ticket(reprint_order_data, 
                                               copy_info="Reprint", 
                                               original_timestamp_str=original_timestamp)
        
        reprint_success = reprint_success1 and reprint_success2
        
        if reprint_success:
            return jsonify({"status": "success", "message": f"Order #{order_number_to_reprint} REPRINTED successfully (2 copies)."}), 200
        else:
            return jsonify({"status": "error", "message": f"Failed to reprint Order #{order_number_to_reprint}. Check printer."}), 500

    except json.JSONDecodeError:
        app.logger.error(f"Error decoding item data for order #{order_number_to_reprint} during reprint.")
        return jsonify({"status": "error", "message": f"Corrupted item data for order #{order_number_to_reprint}. Cannot reprint."}), 500
    except Exception as e:
        app.logger.error(f"Error reprinting order #{order_number_to_reprint}: {str(e)}")
        return jsonify({"status": "error", "message": f"Could not reprint order #{order_number_to_reprint}: {str(e)}"}), 500


if __name__ == '__main__':
    try:
        import win32print
    except ImportError:
        app.logger.error("pywin32 not found. Please ensure it is installed (pip install pywin32).")
    
    app.logger.info(f"CSV files will be saved to: {CSV_DIR}")
    if PRINTER_NAME: 
        app.logger.info(f"Attempting to use printer: {PRINTER_NAME}")
    else:
        app.logger.warning("Warning: PRINTER_NAME is not set. Printing will likely fail.")
    app.run(host='0.0.0.0', port=5000, debug=True)
