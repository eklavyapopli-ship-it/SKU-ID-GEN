from flask import Flask, render_template, request, jsonify, url_for
import os, re, random, string, time
from dotenv import load_dotenv
from pymongo import MongoClient
import barcode
from barcode.writer import ImageWriter


app = Flask(__name__)
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "skuDB")

if not MONGO_URI:
    raise ValueError("❌ MONGO_URI not found in .env file!")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
skus_collection = db["skus"]


app.config["UPLOAD_FOLDER"] = os.path.join("static", "barcodes")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


def random_suffix(length=4):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def create_sku(name, categories):
 
 
    skus_collection.delete_many({})
    print("🗑️ Deleted all existing SKUs in database")

   
    name = name.strip().title()
    categories = {k.strip().title(): v.strip().title() for k, v in categories.items()}


    words = name.split()
    name_prefix = '-'.join([w[:3].upper() for w in words[:3]]) or "PRD"

    cat_prefixes = []
    for value in categories.values():
        val_words = value.split()
        if len(val_words) == 1:
            cat_prefix = value[:3].upper()
        else:
            cat_prefix = ''.join(word[0].upper() for word in val_words)
        cat_prefixes.append(cat_prefix)

    base_sku = f"{name_prefix}-{'-'.join(cat_prefixes)}" if cat_prefixes else name_prefix
    sku = base_sku

  
    while skus_collection.find_one({"sku": sku}):
        sku = f"{base_sku}-{random_suffix()}"

 
    skus_collection.insert_one({
        "product_name": name,
        "categories": categories,
        "sku": sku,
        "created_at": time.time()
    })

    print(f"✅ Created new SKU: {sku}")
    return sku


def save_barcode(sku, name):
    """Generate and save barcode image."""
    safe_name = re.sub(r'\W+', '_', name)
    filename = f"{safe_name}_{int(time.time())}.png"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    try:
        barcode_class = barcode.get_barcode_class("code128")
        code128 = barcode_class(sku, writer=ImageWriter())
        code128.save(filepath.replace(".png", ""), options={"write_text": True})
        return filepath
    except Exception as e:
        print("❌ Error generating barcode:", e)
        return None


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
    barcode_path = save_barcode(sku, name)

    if not barcode_path:
        return jsonify({"error": "Failed to generate barcode"}), 500

    barcode_url = url_for('static', filename=f"barcodes/{os.path.basename(barcode_path)}")

   
    category_codes = {}
    for key, value in categories.items():
        val_words = value.strip().split()
        code = value[:3].upper() if len(val_words) == 1 else ''.join(word[0].upper() for word in val_words)
        category_codes[value] = code

    return jsonify({
        "sku": sku,
        "barcode_url": barcode_url,
        "category_heads": list(categories.keys()),
        "category_codes": category_codes
    })



if __name__ == '__main__':
    print("✅ Connected to MongoDB successfully!")
    app.run(host='0.0.0.0', debug=True)
