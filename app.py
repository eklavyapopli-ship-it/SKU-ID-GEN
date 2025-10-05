from flask import Flask, render_template, request, jsonify
import random
import string

app = Flask(__name__)

# Track SKUs per product name
existing_skus = {}

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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate_sku', methods=['POST'])
def generate_sku():
    data = request.get_json()
    name = data.get('name', '').strip()
    categories = data.get('categories', {})

    if not name:
        return jsonify({"error": "Product name is required"}), 400

    sku = create_sku(name, categories)

    # Generate short codes for category values
    category_codes = {}
    for key, value in categories.items():
        val_words = value.strip().split()
        if len(val_words) == 1:
            code = value[:3].upper()
        else:
            code = ''.join(word[0].upper() for word in val_words)
        category_codes[value] = code

    return jsonify({
        "sku": sku,
        "category_heads": list(categories.keys()),
        "category_codes": category_codes  # full form -> code
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
