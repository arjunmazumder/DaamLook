from rest_framework import serializers
from .models import Category, SubCategory, Product, BulkPricingTier, ProductImage

class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = SubCategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ['product', 'created_at']

class BulkPricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkPricingTier
        fields = '__all__'
        read_only_fields = ['product']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    bulk_pricing_tiers = BulkPricingTierSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['approval_status', 'rejection_reason', 'created_at', 'updated_at']

    def to_internal_value(self, data):
        # Convert empty strings to None for Decimal fields to prevent "A valid number is required" error
        for field in ['retail_price', 'base_wholesale_price', 'discount_value']:
            if field in data and data[field] == '':
                # Ensure the data dictionary is mutable, handle QueryDict from form-data
                if hasattr(data, '_mutable'):
                    data._mutable = True
                data[field] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            if not (user.is_staff or user.is_superuser):
                shop = attrs.get('shop')
                if not shop or shop.user != user:
                    raise serializers.ValidationError({"shop": "You can only add products to your own shop."})
        return attrs
