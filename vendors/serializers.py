from rest_framework import serializers
from .models import ShopProfile, ShopReview

class ShopProfileSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = ShopProfile
        fields = '__all__'
        read_only_fields = ['user', 'average_rating', 'total_reviews', 'created_at', 'updated_at']

class ShopReviewSerializer(serializers.ModelSerializer):
    reviewer_phone = serializers.CharField(source='reviewer.phone_number', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.full_name', read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = ShopReview
        fields = '__all__'
        read_only_fields = ['reviewer', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        shop = attrs.get('shop')

        if request and request.user:
            # Check if user is trying to review their own shop
            if shop and shop.user == request.user:
                raise serializers.ValidationError({"error": "You cannot review your own shop."})
                
        return attrs
