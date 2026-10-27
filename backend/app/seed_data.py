import random
from datetime import date, datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models import Product, SalesTransaction, ImportLog
from backend.app.analytics.metrics import (
    compute_actual_selling_price,
    compute_revenue,
    compute_gross_profit,
    compute_gross_margin
)

# Product catalog seed templates
CATEGORIES = {
    "Electronics": [
        ("Noise-Cancelling Wireless Headphones", 149.99, 65.00),
        ("Mechanical RGB Gaming Keyboard", 89.99, 38.00),
        ("Ultra-HD 4K Streaming Webcam", 79.99, 32.00),
        ("Fast Multi-Port USB-C GaN Charger", 49.99, 18.00),
        ("Ergonomic Vertical Bluetooth Mouse", 39.99, 14.50),
        ("Portable Waterproof Bluetooth Speaker", 59.99, 22.00),
        ("Active Smart Fitness Tracker Band", 69.99, 26.00),
        ("Magnetic Wireless Charging Stand", 34.99, 12.00),
        ("High-Speed Thunderbolt 4 Docking Station", 229.99, 110.00),
        ("True Wireless ANC Earbuds Pro", 119.99, 45.00),
        ("Digital Smart Alarm Clock with Qi Pad", 44.99, 18.00),
        ("Smart Wi-Fi Security Indoor Camera", 54.99, 21.00),
        ("Compact USB Studio Condenser Microphone", 84.99, 35.00),
        ("Ultra-Slim 15.6-inch Portable Monitor", 179.99, 92.00),
        ("Adjustable Dual Monitor Mounting Arm", 64.99, 25.00),
        ("Universal Smart TV Soundbar 2.1", 129.99, 58.00),
        ("High-Capacity 26800mAh Power Bank", 59.99, 24.00),
        ("Smart Home Zigbee Bridge Hub", 39.99, 16.00),
    ],
    "Home & Kitchen": [
        ("Precision Temperature Electric Kettle", 79.99, 32.00),
        ("Professional Grade Countertop Blender", 159.99, 70.00),
        ("Japanese Damascus Steel Chef Knife 8\"", 89.99, 34.00),
        ("Enameled Cast Iron Dutch Oven 6-Qt", 119.99, 52.00),
        ("Non-Stick Ceramic Frying Pan Set", 69.99, 28.00),
        ("Digital Smart Food Scale with App", 29.99, 9.50),
        ("Cold Brew Iced Coffee Maker 1L", 34.99, 12.00),
        ("Aero-Circulation Air Fryer XL", 109.99, 48.00),
        ("Cordless Handheld Stick Vacuum", 189.99, 85.00),
        ("Aromatherapy Ultrasonic Cool Mist Diffuser", 24.99, 8.00),
        ("Double-Walled Glass Coffee Mugs (Set of 4)", 32.99, 11.50),
        ("Heavy Duty Bamboo Kitchen Cutting Board", 39.99, 14.00),
        ("Compact Stainless Steel Toaster 4-Slice", 54.99, 23.00),
        ("Under-Sink 5-Stage Reverse Osmosis Filter", 219.99, 105.00),
        ("Automatic Hands-Free Trash Can 13-Gal", 69.99, 29.00),
        ("Smart Sous Vide Immersion Precision Cooker", 99.99, 42.00),
        ("Silicone Cooking Utensils Set 12-Piece", 27.99, 9.00),
    ],
    "Apparel & Footwear": [
        ("Merino Wool Everyday Crewneck Sweater", 95.00, 38.00),
        ("Waterproof Breathable Trail Running Shoes", 130.00, 52.00),
        ("Four-Way Stretch Performance Chino Pant", 78.00, 26.00),
        ("All-Weather Packable Hooded Windbreaker", 88.00, 33.00),
        ("Seamless High-Waisted Workout Leggings", 58.00, 16.00),
        ("Classic Organic Cotton Oxford Shirt", 64.00, 22.00),
        ("Thermal Polarized UV400 Sunglasses", 45.00, 12.00),
        ("Anti-Blister Cushioned Athletic Socks (6-Pack)", 24.00, 6.50),
        ("Genuine Leather Minimalist Bifold Wallet", 42.00, 14.00),
        ("Heavyweight French Terry Pullover Hoodie", 72.00, 25.00),
        ("Lightweight Ripstop Utility Cargo Shorts", 48.00, 17.00),
        ("Water-Resistant Canvas Everyday Backpack", 68.00, 24.00),
        ("Thermal Base Layer Top and Bottom Set", 52.00, 18.00),
        ("Slip-On Memory Foam Casual Sneakers", 65.00, 23.00),
        ("Heritage Wool Knit Winter Beanie", 28.00, 7.50),
        ("Recycled Fleece Full-Zip Midlayer Jacket", 84.00, 31.00),
    ],
    "Health & Personal Care": [
        ("Sonic Electric Toothbrush with 5 Modes", 69.99, 22.00),
        ("Percussion Muscle Massage Therapy Gun", 119.99, 42.00),
        ("Organic Hyaluronic Acid & Vitamin C Serum", 26.99, 6.00),
        ("Ionic Ceramic Salon Hair Dryer", 79.99, 28.00),
        ("Extra Thick Non-Slip Eco Yoga Mat", 44.99, 15.00),
        ("Deep Cleansing Facial Pore Scrubber", 39.99, 13.00),
        ("Rechargeable Heated Neck & Back Massager", 59.99, 21.00),
        ("Bluetooth Smart Body Fat Bathroom Scale", 34.99, 11.50),
        ("Titanium Beard & Stubble Trimmer Kit", 49.99, 17.00),
        ("Aromatherapy Sleep Sound & Light Machine", 42.99, 14.00),
        ("Mineral Broad Spectrum Sunscreen SPF 50", 22.99, 5.50),
        ("High-Potency Omega-3 Fish Oil Softgels", 29.99, 8.50),
        ("Ergonomic Foam Lumbar Support Pillow", 36.99, 12.00),
        ("Collagen Peptides Hydrolyzed Powder 16oz", 38.99, 13.00),
        ("Water Flosser Cordless Dental Oral Irrigator", 49.99, 16.00),
        ("Anti-Fatigue Standing Desk Comfort Mat", 54.99, 19.00),
    ],
    "Sports & Outdoors": [
        ("Ultralight 2-Person Backpacking Tent", 199.99, 85.00),
        ("Insulated Double-Wall Stainless Tumbler 32oz", 29.99, 8.00),
        ("Adjustable Quick-Select Dumbbell (Single 52lb)", 179.99, 88.00),
        ("Carbon Fiber Folding Trekking Poles (Pair)", 59.99, 21.00),
        ("Heavy-Duty Natural Latex Resistance Bands", 24.99, 6.00),
        ("Tactical Hydration Pack with 2L Bladder", 46.99, 16.00),
        ("Inflatable Stand Up Paddleboard 10.6ft", 349.99, 165.00),
        ("Portable Camping Stove with Piezo Ignition", 39.99, 13.50),
        ("High-Output LED USB Rechargeable Headlamp", 32.99, 10.00),
        ("Self-Inflating Sleeping Pad with Pillow", 54.99, 20.00),
        ("Cast Iron Kettlebell 35lb Powder Coated", 49.99, 24.00),
        ("Speed Jump Rope with Ball Bearings", 18.99, 4.50),
        ("Waterproof Dry Bag Sack 20L", 22.99, 6.50),
        ("Sports Duffle Bag with Shoe Compartment", 44.99, 15.00),
        ("Foam Roller for Muscle Recovery 18\"", 24.99, 7.00),
        ("Compact Folding Camping Chair", 42.99, 16.00),
    ],
    "Office & Workspace": [
        ("Ergonomic Mesh High-Back Office Chair", 249.99, 115.00),
        ("Electric Dual-Motor Standing Desk Frame", 299.99, 140.00),
        ("Vegan Leather Waterproof Large Desk Pad", 28.99, 8.00),
        ("Aluminum Elevated Laptop Cooling Riser", 36.99, 12.00),
        ("Cross-Cut Micro Heavy-Duty Paper Shredder", 79.99, 33.00),
        ("Under-Desk Cable Management Tray System", 26.99, 8.50),
        ("LED Desk Lamp with Wireless Qi Charger", 48.99, 17.00),
        ("Noise-Cancelling USB Office Headset with Mic", 59.99, 22.00),
        ("Ergonomic Memory Foam Keyboard Wrist Rest", 21.99, 6.50),
        ("Ultra-Quiet Desktop Personal Oscillating Fan", 27.99, 9.00),
        ("Magnetic Glass Dry Erase Whiteboard 24x36", 64.99, 25.00),
        ("Steel Mobile Filing Cabinet with Lock", 119.99, 54.00),
        ("Monitor Light Bar with Auto-Dimming Sensor", 49.99, 18.00),
        ("Foot Rest Cushion for Under Desk", 32.99, 11.00),
        ("Modular Desktop Document Organizer Tray", 34.99, 12.50),
        ("Multi-Device Bluetooth Mechanical Numpad", 38.99, 14.00),
        ("Surge Protector Power Strip with 8 Outlets", 29.99, 9.50),
    ]
}

CHANNELS = ["Direct Online", "Retail Partner", "Amazon Marketplace", "B2B Wholesale"]

def generate_synthetic_catalog() -> List[Dict[str, Any]]:
    """
    Generates exactly 100 products deterministically with rich category distribution.
    """
    products = []
    prod_counter = 1

    for cat_name, items in CATEGORIES.items():
        for name, base_price, cogs in items:
            if prod_counter > 100:
                break
            sku_prefix = cat_name[:4].upper()
            sku = f"{sku_prefix}-{prod_counter:03d}"
            
            # Specific margin profiles for insights:
            # Item 42 (e.g. low-margin anomaly: cogs high relative to base price)
            adjusted_cogs = cogs
            if prod_counter == 12:  # Razor thin margin product
                adjusted_cogs = round(base_price * 0.92, 2)
            elif prod_counter == 28: # Heavily commoditized item
                adjusted_cogs = round(base_price * 0.88, 2)
            elif prod_counter == 73: # Margin negative under standard 15% discount
                adjusted_cogs = round(base_price * 0.95, 2)

            products.append({
                "sku": sku,
                "name": name,
                "category": cat_name,
                "base_price": base_price,
                "cogs": adjusted_cogs,
                "inventory_count": random.Random(42 + prod_counter).randint(80, 650),
                "description": f"Synthetic retail catalog item: {name} in {cat_name}.",
                "is_active": True
            })
            prod_counter += 1

    return products[:100]

def seed_database_if_empty(db: Session, force: bool = False) -> Dict[str, Any]:
    """
    Deterministically seeds the database if no products currently exist, or if forced.
    Generates ~100 products and >5000 transactions over 14 months.
    """
    existing_count = db.query(Product).count()
    if existing_count > 0 and not force:
        return {
            "status": "ALREADY_SEEDED",
            "message": f"Database already populated with {existing_count} products.",
            "products_count": existing_count,
            "transactions_count": db.query(SalesTransaction).count()
        }

    if force:
        db.query(SalesTransaction).delete()
        db.query(Product).delete()
        db.query(ImportLog).delete()
        db.commit()

    rng = random.Random(42)  # Deterministic seed for reproducible analytical results
    catalog = generate_synthetic_catalog()
    
    # 1. Insert Products
    product_objects = []
    for p_data in catalog:
        prod = Product(**p_data)
        db.add(prod)
        product_objects.append(prod)
    db.commit()

    # Re-fetch products with assigned IDs
    db_products = db.query(Product).order_by(Product.id).all()
    prod_map = {p.id: p for p in db_products}

    # 2. Generate Sales Transactions
    start_date = date(2024, 1, 1)
    end_date = date(2025, 2, 28)
    total_days = (end_date - start_date).days

    transactions = []
    txn_code_counter = 10001

    # Product behavioral segmentation for statistical fidelity:
    # 1. Elastic segment (ids 1..25): responsive to price discounts (log-log beta < -1.2)
    # 2. Static price segment (ids 26..35): zero price variation -> triggers NO_PRICE_VARIATION
    # 3. Low sample size segment (ids 36..45): only 3-5 sales records -> triggers INSUFFICIENT_DATA
    # 4. Inelastic segment (ids 46..70): stable demand regardless of price (beta between -0.3 and -0.8)
    # 5. Anomalous segment (ids 71..75): positive beta due to holiday demand correlation
    # 6. Standard segment (remaining): healthy normal retail variation

    for prod in db_products:
        p_id = prod.id
        base_p = prod.base_price
        cogs = prod.cogs

        # Determine number of sales observations
        if 36 <= p_id <= 45:
            # Low data / new products
            num_txns = rng.randint(3, 6)
        elif 26 <= p_id <= 35:
            # Static price items
            num_txns = rng.randint(25, 45)
        else:
            # Normal distribution of transactions
            num_txns = rng.randint(40, 75)

        for _ in range(num_txns):
            # Select date
            random_day_offset = rng.randint(0, total_days)
            sale_dt = start_date + timedelta(days=random_day_offset)

            # Pricing & discount logic per segment
            if 26 <= p_id <= 35:
                # Static price segment: exact 0% discount, constant price
                disc_pct = 0.0
                unit_p = base_p
                qty = rng.randint(2, 10)
            elif 36 <= p_id <= 45:
                # Low data segment
                disc_pct = rng.choice([0.0, 5.0, 10.0])
                unit_p = base_p
                qty = rng.randint(1, 4)
            elif 1 <= p_id <= 25:
                # Elastic segment: higher discounts drive significantly higher volume
                disc_pct = rng.choice([0.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0])
                # Occasional catalog price adjustment
                if sale_dt.month in [6, 7, 11, 12]:
                    unit_p = round(base_p * rng.choice([0.95, 1.0, 1.05]), 2)
                else:
                    unit_p = base_p

                # Quantity is strongly inversely proportional to actual price (Elastic Demand)
                actual_p = compute_actual_selling_price(unit_p, disc_pct)
                price_ratio = actual_p / base_p
                # Power-law response with beta ~ -1.6 plus noise
                base_qty = rng.randint(4, 8)
                mult = max(0.5, (1.0 / max(0.4, price_ratio)) ** 1.6)
                qty = max(1, int(round(base_qty * mult + rng.uniform(-1, 1))))
            elif 71 <= p_id <= 75:
                # Anomalous positive segment: prices slightly higher in Q4, but volume surges (holiday seasonality confounder)
                is_q4 = (sale_dt.month in [11, 12])
                if is_q4:
                    unit_p = round(base_p * 1.15, 2)
                    disc_pct = 0.0
                    qty = rng.randint(12, 25)  # Heavy holiday shopping
                else:
                    unit_p = base_p
                    disc_pct = rng.choice([0.0, 10.0])
                    qty = rng.randint(2, 6)
            else:
                # Standard retail distribution
                disc_pct = rng.choice([0.0, 0.0, 0.0, 5.0, 10.0, 15.0, 20.0])
                unit_p = base_p
                actual_p = compute_actual_selling_price(unit_p, disc_pct)
                qty = rng.randint(2, 12)

            actual_selling_p = compute_actual_selling_price(unit_p, disc_pct)
            revenue = compute_revenue(qty, actual_selling_p)
            gross_profit = compute_gross_profit(revenue, qty, cogs)
            gross_margin = compute_gross_margin(gross_profit, revenue)
            channel = rng.choice(CHANNELS)

            txn = SalesTransaction(
                transaction_code=f"TXN-2024-{txn_code_counter}",
                product_id=p_id,
                sale_date=sale_dt,
                quantity=qty,
                unit_price=unit_p,
                discount_pct=disc_pct,
                actual_selling_price=actual_selling_p,
                cogs_per_unit=cogs,
                revenue=revenue,
                gross_profit=gross_profit,
                gross_margin=gross_margin,
                channel=channel,
                is_synthetic=True
            )
            transactions.append(txn)
            txn_code_counter += 1

    # Bulk insert transactions
    db.bulk_save_objects(transactions)

    # Insert an initial ImportLog entry explaining the synthetic initialization
    import_log = ImportLog(
        filename="system_synthetic_seed_v1.0.csv",
        row_count=len(transactions),
        valid_count=len(transactions),
        error_count=0,
        status="SUCCESS",
        details="Initial system startup deterministic synthetic dataset (100 products, 14 months sales history)."
    )
    db.add(import_log)
    db.commit()

    return {
        "status": "SEEDED_SUCCESSFULLY",
        "message": "Deterministic synthetic retail catalog and transactions initialized successfully.",
        "products_count": len(db_products),
        "transactions_count": len(transactions),
        "dataset_notice": "SYNTHETIC_DATA_FLAG_ACTIVE"
    }
