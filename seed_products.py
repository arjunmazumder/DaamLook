import os
import django
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'damlook.settings')
django.setup()

from users.models import User
from lookup.models import Lookup
from vendors.models import ShopProfile
from products.models import Category, SubCategory, Product, BulkPricingTier

def run():
    print("Starting product data seeding...")

    # Ensure a vendor role exists
    vendor_role, _ = Lookup.objects.get_or_create(name='ROLE', value='VENDOR')

    # Ensure a vendor user exists
    vendor_user, _ = User.objects.get_or_create(
        phone_number='01799999999', 
        defaults={'role': vendor_role}
    )
    if not vendor_user.role:
        vendor_user.role = vendor_role
        vendor_user.save()

    # Ensure a ShopProfile exists
    shop_profile, _ = ShopProfile.objects.get_or_create(
        user=vendor_user,
        defaults={
            'shop_type': 'WHOLESALER',
            'shop_name': 'Global Mart Wholesale & Retail',
            'shop_address': '123 Market Street, Dhaka'
        }
    )

    # 1. Create Categories and SubCategories
    categories_data = {
        'Electronics': ['Smartphones', 'Laptops', 'Audio', 'Accessories'],
        'Clothing': ['Men', 'Women', 'Kids', 'Shoes'],
        'Home & Kitchen': ['Furniture', 'Decor', 'Kitchen Appliances'],
        'Beauty & Health': ['Skincare', 'Makeup', 'Haircare'],
        'Groceries': ['Snacks', 'Beverages', 'Spices']
    }

    subcategories_map = {}
    for cat_name, sub_names in categories_data.items():
        cat, _ = Category.objects.get_or_create(name=cat_name, description=f"{cat_name} category")
        for sub_name in sub_names:
            sub, _ = SubCategory.objects.get_or_create(category=cat, name=sub_name, description=f"{sub_name} subcategory")
            subcategories_map[sub_name] = (cat, sub)

    # 2. Create 50 Products
    product_templates = [
        ("iPhone 14 Pro", "Electronics", "Smartphones", 110000, 105000),
        ("Samsung Galaxy S23", "Electronics", "Smartphones", 95000, 90000),
        ("MacBook Pro M2", "Electronics", "Laptops", 250000, 240000),
        ("Dell XPS 13", "Electronics", "Laptops", 180000, 175000),
        ("Sony WH-1000XM5", "Electronics", "Audio", 35000, 32000),
        ("AirPods Pro 2", "Electronics", "Audio", 28000, 26000),
        ("Anker Power Bank 10000mAh", "Electronics", "Accessories", 3000, 2500),
        ("USB-C Fast Charger", "Electronics", "Accessories", 1500, 1200),
        ("Men's Formal Shirt", "Clothing", "Men", 2500, 2000),
        ("Men's Denim Jacket", "Clothing", "Men", 4500, 3800),
        ("Women's Silk Saree", "Clothing", "Women", 12000, 10000),
        ("Women's Cotton Kurti", "Clothing", "Women", 1800, 1400),
        ("Kids Graphic T-Shirt", "Clothing", "Kids", 800, 600),
        ("Kids Winter Jacket", "Clothing", "Kids", 2200, 1800),
        ("Nike Running Shoes", "Clothing", "Shoes", 15000, 13500),
        ("Leather Formal Loafers", "Clothing", "Shoes", 6500, 5500),
        ("Wooden Dining Table", "Home & Kitchen", "Furniture", 45000, 40000),
        ("Ergonomic Office Chair", "Home & Kitchen", "Furniture", 12500, 11000),
        ("Wall Clock Vintage", "Home & Kitchen", "Decor", 2500, 2000),
        ("Ceramic Flower Vase", "Home & Kitchen", "Decor", 1800, 1500),
        ("Philips Air Fryer", "Home & Kitchen", "Kitchen Appliances", 16000, 14500),
        ("Panasonic Microwave Oven", "Home & Kitchen", "Kitchen Appliances", 19000, 17500),
        ("Vitamin C Serum", "Beauty & Health", "Skincare", 1200, 950),
        ("Hydrating Moisturizer", "Beauty & Health", "Skincare", 850, 700),
        ("Matte Lipstick", "Beauty & Health", "Makeup", 650, 500),
        ("Liquid Foundation", "Beauty & Health", "Makeup", 1500, 1200),
        ("Argan Oil Shampoo", "Beauty & Health", "Haircare", 950, 750),
        ("Hair Heat Protectant", "Beauty & Health", "Haircare", 1100, 900),
        ("Potato Chips Family Pack", "Groceries", "Snacks", 150, 120),
        ("Mixed Nuts 500g", "Groceries", "Snacks", 850, 750),
        ("Orange Juice 1L", "Groceries", "Beverages", 220, 180),
        ("Green Tea 50 Bags", "Groceries", "Beverages", 450, 380),
        ("Cumin Powder 200g", "Groceries", "Spices", 180, 150),
        ("Turmeric Powder 200g", "Groceries", "Spices", 120, 100),
        ("Bluetooth Speaker Portable", "Electronics", "Audio", 4500, 3800),
        ("Wireless Mouse", "Electronics", "Accessories", 1200, 950),
        ("Men's Chino Pants", "Clothing", "Men", 2200, 1800),
        ("Women's Party Gown", "Clothing", "Women", 8500, 7500),
        ("Baby Romper Set", "Clothing", "Kids", 1500, 1200),
        ("Canvas Sneakers", "Clothing", "Shoes", 3500, 2800),
        ("Bookshelf 4-Tier", "Home & Kitchen", "Furniture", 6500, 5500),
        ("LED Table Lamp", "Home & Kitchen", "Decor", 1800, 1500),
        ("Electric Kettle", "Home & Kitchen", "Kitchen Appliances", 2500, 2100),
        ("Sunscreen SPF 50", "Beauty & Health", "Skincare", 1100, 900),
        ("Eyeshadow Palette", "Beauty & Health", "Makeup", 2500, 2100),
        ("Hair Styling Gel", "Beauty & Health", "Haircare", 450, 350),
        ("Chocolate Bar Dark", "Groceries", "Snacks", 350, 300),
        ("Cold Coffee Bottle", "Groceries", "Beverages", 120, 100),
        ("Chili Powder 200g", "Groceries", "Spices", 160, 130),
        ("Gaming Headset", "Electronics", "Audio", 6500, 5800)
    ]

    total_created = 0
    for title, cat_name, sub_name, r_price, w_price in product_templates:
        cat, sub = subcategories_map.get(sub_name, (None, None))
        if not cat or not sub:
            continue

        product_type = random.choice(['RETAIL', 'WHOLESALE'])
        moq = 1 if product_type == 'RETAIL' else random.randint(5, 50)
        
        has_discount = random.choice([True, False])
        discount_type = random.choice(['FLAT', 'PERCENTAGE']) if has_discount else 'NONE'
        discount_value = None
        discount_start_date = None
        discount_end_date = None
        
        if has_discount:
            discount_value = Decimal('100.00') if discount_type == 'FLAT' else Decimal('10.00')
            discount_start_date = timezone.now() - timedelta(days=2)
            discount_end_date = timezone.now() + timedelta(days=15)

        product, created = Product.objects.get_or_create(
            title=title,
            shop=shop_profile,
            defaults={
                'category': cat,
                'subcategory': sub,
                'description': f"Premium quality {title}. Perfect for all your needs.",
                'product_type': product_type,
                'stock_quantity': random.randint(10, 500),
                'retail_price': Decimal(r_price),
                'base_wholesale_price': Decimal(w_price),
                'moq': moq,
                'discount_type': discount_type,
                'discount_value': discount_value,
                'discount_start_date': discount_start_date,
                'discount_end_date': discount_end_date,
                'approval_status': 'APPROVED',
                'is_active': True
            }
        )
        
        if created:
            total_created += 1
            # Add Bulk Pricing for Wholesale products
            if product_type == 'WHOLESALE':
                BulkPricingTier.objects.create(
                    product=product,
                    min_quantity=moq,
                    max_quantity=moq + 20,
                    price_per_unit=Decimal(w_price) * Decimal('0.95') # 5% off base wholesale
                )
                BulkPricingTier.objects.create(
                    product=product,
                    min_quantity=moq + 21,
                    max_quantity=moq + 100,
                    price_per_unit=Decimal(w_price) * Decimal('0.90') # 10% off base wholesale
                )

    print(f"Successfully created/verified 5 Categories, {len(subcategories_map)} Subcategories, and {total_created} Products!")

if __name__ == '__main__':
    run()
