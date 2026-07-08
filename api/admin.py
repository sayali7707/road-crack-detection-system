from django.contrib import admin
from .models import CrackDetection, UserProfile, DetectionReport

@admin.register(CrackDetection)
class CrackDetectionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'crack_count', 'severity', 'crack_density_score', 'created_at']
    list_filter = ['severity', 'crack_type', 'created_at']
    search_fields = ['user__username', 'road_name', 'location_address']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone_number', 'department']
    list_filter = ['role']

@admin.register(DetectionReport)
class DetectionReportAdmin(admin.ModelAdmin):
    list_display = ['detection', 'generated_at', 'downloaded_count']