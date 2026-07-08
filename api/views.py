from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import CrackDetection, DetectionReport
from .serializers import CrackDetectionSerializer
import os
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from ultralytics import YOLO

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff

class CrackDetectionViewSet(viewsets.ModelViewSet):
    queryset = CrackDetection.objects.all()
    serializer_class = CrackDetectionSerializer
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'])
    def detect(self, request):
        print("\n>>> DETECTION STARTED <<<")
        
        try:
            image_file = request.FILES.get('original_image')
            if not image_file:
                return Response({'error': 'No image'}, status=400)
            
            # Get GPS data from request
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            location_address = request.data.get('location_address', '')
            road_name = request.data.get('road_name', '')
            
            # Create detection record
            detection = CrackDetection.objects.create(
                user=request.user if request.user.is_authenticated else None,
                original_image=image_file,
                latitude=latitude if latitude else None,
                longitude=longitude if longitude else None,
                location_address=location_address,
                road_name=road_name
            )
            print(f"Created ID: {detection.id}")
            
            # Load model
            model_path = r"C:\Users\SAYAL\runs\segment\train3\weights\best.pt"
            
            if not os.path.exists(model_path):
                return Response({'error': 'Model not found'}, status=500)
            
            model = YOLO(model_path)
            results = model(detection.original_image.path, conf=0.25)
            result = results[0]
            
            # Get crack count
            crack_count = 0
            if result.masks is not None:
                crack_count = len(result.masks)
            elif result.boxes is not None:
                crack_count = len(result.boxes)
            
            # Calculate crack density score (0-100)
            crack_density_score = min(100, crack_count * 10)
            
            # Determine severity
            if crack_count == 0:
                severity = 'LOW'
                severity_score = 1
            elif crack_count <= 3:
                severity = 'MEDIUM'
                severity_score = 5
            elif crack_count <= 7:
                severity = 'HIGH'
                severity_score = 8
            else:
                severity = 'SEVERE'
                severity_score = 10
            
            # Save annotated image
            annotated_img = result.plot()
            img_rgb = cv2.cvtColor(annotated_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            img_io = BytesIO()
            pil_img.save(img_io, format='PNG')
            img_io.seek(0)
            
            filename = f"detected_{detection.id}.png"
            detection.detected_image.save(filename, ContentFile(img_io.read()), save=False)
            detection.crack_count = crack_count
            detection.severity = severity
            detection.crack_density_score = crack_density_score
            detection.severity_score = severity_score
            detection.save()
            
            return Response({
                'id': detection.id,
                'crack_count': crack_count,
                'severity': severity,
                'crack_density_score': crack_density_score,
                'detected_image': detection.detected_image.url if detection.detected_image else None,
                'suggested_action': detection.get_suggested_action(),
                'latitude': detection.latitude,
                'longitude': detection.longitude,
                'location_address': detection.location_address,
                'created_at': detection.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }, status=201)
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        """Generate and download PDF report"""
        try:
            detection = self.get_object()
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="crack_report_{detection.id}.pdf"'
            
            doc = SimpleDocTemplate(response, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, alignment=1, spaceAfter=30)
            story.append(Paragraph("Road Crack Detection Report", title_style))
            story.append(Spacer(1, 12))
            
            # Detection Info
            info_data = [
                ['Detection ID', str(detection.id)],
                ['Date', detection.created_at.strftime('%Y-%m-%d %H:%M:%S')],
                ['Crack Count', str(detection.crack_count)],
                ['Severity', detection.severity],
                ['Crack Density', f"{getattr(detection, 'crack_density_score', 0):.1f}%"],
            ]
            
            if detection.has_location:
                info_data.append(['Location', f"{detection.latitude}, {detection.longitude}"])
                if detection.location_address:
                    info_data.append(['Address', detection.location_address])
            
            table = Table(info_data, colWidths=[2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Recommendation
            story.append(Paragraph("<b>Recommendation:</b>", styles['Heading2']))
            story.append(Paragraph(detection.get_suggested_action(), styles['Normal']))
            
            doc.build(story)
            
            # Save report to database
            report, created = DetectionReport.objects.get_or_create(detection=detection)
            
            # Save the PDF content
            pdf_content = response.content
            report_file_name = f"report_{detection.id}.pdf"
            report.report_file.save(report_file_name, ContentFile(pdf_content), save=True)
            
            return response
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get dashboard statistics - Open for all"""
        
        try:
            total_detections = CrackDetection.objects.count()
            total_cracks = sum(d.crack_count for d in CrackDetection.objects.all()) if total_detections > 0 else 0
            
            # Average confidence
            avg_confidence_result = CrackDetection.objects.filter(confidence_score__gt=0).aggregate(Avg('confidence_score'))
            avg_confidence = avg_confidence_result['confidence_score__avg'] or 0
            
            # Severity counts
            severity_counts = {
                'LOW': CrackDetection.objects.filter(severity='LOW').count(),
                'MEDIUM': CrackDetection.objects.filter(severity='MEDIUM').count(),
                'HIGH': CrackDetection.objects.filter(severity='HIGH').count(),
                'SEVERE': CrackDetection.objects.filter(severity='SEVERE').count(),
            }
            
            # Last 7 days data
            last_7_days = []
            for i in range(7):
                date = (timezone.now().date() - timedelta(days=i))
                count = CrackDetection.objects.filter(created_at__date=date).count()
                last_7_days.append({'date': date.isoformat(), 'count': count})
            
            # Detections with location
            location_data = list(CrackDetection.objects.filter(
                latitude__isnull=False
            ).exclude(
                latitude=0
            ).values('id', 'latitude', 'longitude', 'severity', 'crack_count', 'created_at')[:50])
            
            # Print for debugging
            print(f"Dashboard data - Total: {total_detections}, Severity: {severity_counts}")
            
            return Response({
                'total_detections': total_detections,
                'total_cracks': total_cracks,
                'avg_confidence': avg_confidence * 100 if avg_confidence else 0,
                'severity_breakdown': severity_counts,
                'last_7_days': last_7_days,
                'location_data': location_data,
            })
        except Exception as e:
            print(f"Dashboard error: {e}")
            return Response({'error': str(e)}, status=500)