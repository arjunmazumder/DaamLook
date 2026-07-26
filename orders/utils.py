from django.utils import timezone
from decimal import Decimal

def calculate_product_unit_price(product, quantity):
    """
    Calculate the unit price for a product given a specific quantity.
    Takes into account Retail vs Wholesale, Active Discounts, and Bulk Pricing Tiers.
    """
    base_price = product.retail_price if product.product_type == 'RETAIL' else product.base_wholesale_price
    if not base_price:
        return Decimal('0.00')
        
    # Check Bulk Pricing (only if wholesale and there are tiers)
    if product.product_type == 'WHOLESALE':
        tiers = product.bulk_pricing_tiers.filter(min_quantity__lte=quantity, max_quantity__gte=quantity)
        if tiers.exists():
            base_price = tiers.first().price_per_unit

    # Check Discounts
    if product.discount_type != 'NONE' and product.discount_value:
        now = timezone.now()
        is_discount_valid = True
        if product.discount_start_date and product.discount_end_date:
            if not (product.discount_start_date <= now <= product.discount_end_date):
                is_discount_valid = False
                
        if is_discount_valid:
            if product.discount_type == 'FLAT':
                base_price = max(Decimal('0.00'), Decimal(base_price) - Decimal(product.discount_value))
            elif product.discount_type == 'PERCENTAGE':
                discount_amount = Decimal(base_price) * (Decimal(product.discount_value) / Decimal('100.00'))
                base_price = max(Decimal('0.00'), Decimal(base_price) - discount_amount)
                
    return Decimal(base_price)
