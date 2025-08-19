from rest_framework import serializers
from .models import TravelQuery

class TravelQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelQuery
        fields = '__all__'
