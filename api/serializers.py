from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CrackDetection, UserProfile, DetectionReport


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'date_joined']

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return 'VIEWER'


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = '__all__'


class CrackDetectionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    suggested_action = serializers.SerializerMethodField()
    severity_display = serializers.SerializerMethodField()
    crack_type_display = serializers.SerializerMethodField()

    class Meta:
        model = CrackDetection
        fields = '__all__'
        read_only_fields = ['user', 'detected_image', 'crack_count', 'confidence_score']

    def get_suggested_action(self, obj):
        return obj.get_suggested_action()

    def get_severity_display(self, obj):
        return dict(CrackDetection.SEVERITY_CHOICES).get(obj.severity, 'Unknown')

    def get_crack_type_display(self, obj):
        return dict(CrackDetection.CRACK_TYPES).get(obj.crack_type, 'Unknown')


class CrackDetectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrackDetection
        fields = ['original_image', 'latitude', 'longitude', 'location_address',
                  'road_name', 'notes', 'crack_type', 'severity']


class DetectionReportSerializer(serializers.ModelSerializer):
    detection = CrackDetectionSerializer(read_only=True)

    class Meta:
        model = DetectionReport
        fields = '__all__'