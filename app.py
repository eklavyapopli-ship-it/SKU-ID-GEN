from flask import Flask, render_template, request, jsonify, url_for
import os, re, random, string, time
import barcode
from barcode.writer import ImageWriter
from flask import send_from_directory
# Optional fallback library
try:
    import treepoem
except ImportError:
    treepoem = None

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'barcodes')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Track SKUs and barcode files per product name
existing_skus = {}
existing_barcodes = {}

# Generate short random string (used if duplicate SKUs occur)
def random_suffix(length=4):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

# Create SKU from product name + category dictionary
def create_sku(name, categories):
    words = name.strip().split()
    name_prefix = '-'.join([w[:3].upper() for w in words[:3]]) or "PRD"

    cat_prefixes = []
    for value in categories.values():
        val = value.strip()
        val_words = val.split()
        if len(val_words) == 1:
            cat_prefix = val_words[0][:3].upper()
        else:
            cat_prefix = ''.join(word[0].upper() for word in val_words)
        cat_prefixes.append(cat_prefix)

    base_sku = f"{name_prefix}-{'-'.join(cat_prefixes)}" if cat_prefixes else name_prefix

    # Ensure unique SKU per product
    product_skus = existing_skus.get(name, set())
    sku = base_sku
    while sku in product_skus:
        sku = f"{base_sku}-{random_suffix()}"
    product_skus.add(sku)
    existing_skus[name] = product_skus

    return sku

# Save barcode image (and delete previous one if exists)
def save_barcode(sku, name):
    safe_name = re.sub(r'\W+', '_', name)
    filename = f"{safe_name}_{int(time.time())}.png"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Delete previous barcode for this product if it exists
    if name in existing_barcodes:
        old_file = existing_barcodes[name]
        if os.path.exists(old_file):
            try:
                os.remove(old_file)
                print(f"🗑️ Deleted old barcode: {old_file}")
            except Exception as e:
                print(f"⚠️ Could not delete old barcode: {e}")

    # Generate new barcode
    try:
        barcode_class = barcode.get_barcode_class('code128')
        code128 = barcode_class(sku, writer=ImageWriter())
        code128.save(filepath.replace('.png', ''), options={"write_text": True})
        existing_barcodes[name] = filepath
        return filepath
    except Exception:
        if treepoem:
            img = treepoem.generate_barcode(barcode_type="code128", data=sku)
            img.convert("1").save(filepath)
            existing_barcodes[name] = filepath
            return filepath
        return None
@app.route('/')
def home():
    # Serves static/index.html
    return app.send_static_file('index.html')


@app.route('/generate_sku', methods=['POST'])
def generate_sku():
    data = request.get_json()
    name = data.get('name', '').strip()
    categories = data.get('categories', {})

    if not name:
        return jsonify({"error": "Product name is required"}), 400

    sku = create_sku(name, categories)
    barcode_path = save_barcode(sku, name)

    if not barcode_path:
        return jsonify({"error": "Failed to generate barcode"}), 500

    barcode_url = url_for('static', filename=f"barcodes/{os.path.basename(barcode_path)}")
    return jsonify({"sku": sku, "barcode_url": barcode_url})

if __name__ == '__main__':
    app.run(debug=True)
