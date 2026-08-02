from rest_framework import serializers
from .models import Category, SubCategory, Product, BulkPricingTier, ProductImage

class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = SubCategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = '__all__'
        read_only_fields = ['created_at']



class BulkPricingTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = BulkPricingTier
        fields = '__all__'

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    bulk_pricing_tiers = BulkPricingTierSerializer(many=True, read_only=True)
    after_discount_price = serializers.SerializerMethodField()
    shop_name = serializers.CharField(source='shop.shop_name', read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user = request.user
            is_admin = user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role and user.role.name == 'ROLE' and user.role.value == 'ADMIN')
            if not is_admin:
                self.fields['approval_status'].read_only = True
                self.fields['rejection_reason'].read_only = True

    def get_after_discount_price(self, obj):
        from django.utils import timezone
        
        # Determine the base price based on product type
        base_price = obj.retail_price if obj.product_type == 'RETAIL' else obj.base_wholesale_price
        
        if not base_price:
            return None
            
        if obj.discount_type == 'NONE' or not obj.discount_value:
            return None
            
        # Check if discount dates are valid
        now = timezone.now()
        if obj.discount_start_date and obj.discount_end_date:
            if not (obj.discount_start_date <= now <= obj.discount_end_date):
                return None
                
        # Calculate discount
        if obj.discount_type == 'FLAT':
            return max(0.0, float(base_price) - float(obj.discount_value))
        elif obj.discount_type == 'PERCENTAGE':
            discount_amount = float(base_price) * (float(obj.discount_value) / 100)
            return max(0.0, float(base_price) - discount_amount)
            
        return None
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Move these fields to the end of the JSON response
        after_discount = representation.pop('after_discount_price', None)
        images = representation.pop('images', [])
        bulk_pricing_tiers = representation.pop('bulk_pricing_tiers', [])
        
        representation['after_discount_price'] = after_discount
        representation['images'] = images
        representation['bulk_pricing_tiers'] = bulk_pricing_tiers
        return representation

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
        if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user = request.user
            is_admin = user.is_staff or user.is_superuser or (hasattr(user, 'role') and user.role and user.role.name == 'ROLE' and user.role.value == 'ADMIN')
            
            if not is_admin:
                shop = attrs.get('shop')
                if self.instance:
                    if shop and shop.user != user:
                        raise serializers.ValidationError({"shop": "You can only assign products to your own shop."})
                else:
                    if not shop or shop.user != user:
                        raise serializers.ValidationError({"shop": "You can only add products to your own shop."})
        return attrs
