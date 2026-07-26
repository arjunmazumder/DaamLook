from rest_framework import serializers
from .models import BroadcastAnnouncement

class BroadcastAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastAnnouncement
        fields = '__all__'
        read_only_fields = ['created_at']
