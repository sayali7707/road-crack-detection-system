from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

def upload_image_path(instance, filename):
    return f'detections/{timezone.now().strftime("%Y/%m/%d")}/{filename}'

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('FIELD_ENGINEER', 'Field Engineer'),
        ('VIEWER', 'Viewer'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    phone_number = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class CrackDetection(models.Model):
    SEVERITY_CHOICES = [
        ('LOW', 'Low - Minor cracks'),
        ('MEDIUM', 'Medium - Needs monitoring'),
        ('HIGH', 'High - Immediate repair'),
        ('SEVERE', 'Severe - Emergency'),
    ]
    
    CRACK_TYPES = [
        ('LONGITUDINAL', 'Longitudinal Crack'),
        ('TRANSVERSE', 'Transverse Crack'),
        ('ALLIGATOR', 'Alligator Cracking'),
        ('BLOCK', 'Block Cracking'),
        ('UNKNOWN', 'Unknown Type'),
    ]
    
    # Basic information
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='detections')
    original_image = models.ImageField(upload_to=upload_image_path)
    detected_image = models.ImageField(upload_to=upload_image_path, null=True, blank=True)
    
    # Detection results
    crack_count = models.IntegerField(default=0)
    crack_type = models.CharField(max_length=20, choices=CRACK_TYPES, default='UNKNOWN')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='LOW')
    confidence_score = models.FloatField(default=0.0)
    
    # New fields
    crack_density_score = models.FloatField(default=0.0)
    severity_score = models.IntegerField(default=0)
    maintenance_priority = models.CharField(max_length=20, default='LOW', blank=True)
    estimated_repair_cost = models.CharField(max_length=100, blank=True, default='')
    
    # Location information (GPS)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_address = models.TextField(blank=True, default='')
    road_name = models.CharField(max_length=200, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=100, blank=True, default='')
    country = models.CharField(max_length=100, default='India')
    
    # Additional details
    notes = models.TextField(blank=True, default='')
    inspector_name = models.CharField(max_length=100, blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Detection {self.id} - {self.crack_count} cracks - {self.severity}"
    
    @property
    def has_location(self):
        return self.latitude is not None and self.longitude is not None
    
    def get_suggested_action(self):
        suggestions = {
            'LOW': 'Regular monitoring recommended.',
            'MEDIUM': 'Schedule maintenance within 3-6 months.',
            'HIGH': 'Priority repair needed within 1-2 months.',
            'SEVERE': 'Immediate action required!',
        }
        return suggestions.get(self.severity, 'Consult engineer.')

class DetectionReport(models.Model):
    detection = models.OneToOneField(CrackDetection, on_delete=models.CASCADE, related_name='report')
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    downloaded_count = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Report for Detection #{self.detection.id}"