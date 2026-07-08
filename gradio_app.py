import gradio as gr
import requests
from PIL import Image
import io
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# Set matplotlib style for better looking charts
plt.style.use('seaborn-v0_8-darkgrid')

class CrackDetectionApp:
    def __init__(self):
        self.api_url = "http://localhost:8000/api"
        self.token = None
        self.is_admin = False
    
    def login(self, username, password):
        """Login for admin access"""
        if username == "admin" and password == "admin123":
            self.is_admin = True
            return "✅ Admin login successful! You have access to dashboard."
        else:
            self.is_admin = False
            return "✅ Logged in as regular user."
    
    def detect_from_camera(self, image, latitude, longitude, road_name):
        """Detect cracks from camera image with GPS"""
        if image is None:
            return None, "Please capture an image first!", ""
        
        try:
            temp_path = "temp_camera.jpg"
            image.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                response = requests.post(
                    f"{self.api_url}/detections/detect/",
                    files={'original_image': f},
                    data={
                        'latitude': latitude,
                        'longitude': longitude,
                        'road_name': road_name,
                        'location_address': f"Lat: {latitude}, Lon: {longitude}"
                    },
                    timeout=60
                )
            
            os.remove(temp_path)
            
            if response.status_code == 201:
                result = response.json()
                
                detected_img = None
                if result.get('detected_image'):
                    img_resp = requests.get(f"http://localhost:8000{result['detected_image']}")
                    if img_resp.status_code == 200:
                        detected_img = Image.open(io.BytesIO(img_resp.content))
                
                severity_colors = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'SEVERE': '🔴'}
                severity_icon = severity_colors.get(result.get('severity', 'LOW'), '⚪')
                
                msg = f"""
## 📊 Detection Results

| Metric | Value |
|--------|-------|
| **Detection ID** | `{result.get('id')}` |
| **Crack Count** | 🔍 {result.get('crack_count', 0)} |
| **Severity** | {severity_icon} {result.get('severity', 'N/A')} |
| **Crack Density** | 📊 {result.get('crack_density_score', 0):.1f}% |
| **Location** | 📍 {latitude}, {longitude} |
| **Road** | 🛣️ {road_name if road_name else 'Not specified'} |

### 🔧 Recommended Action:
{result.get('suggested_action', 'Consult engineer')}

---
💡 **Use this Detection ID to download the PDF report**
"""
                return detected_img, msg, result.get('id')
            else:
                return image, f"❌ Error: {response.status_code}", None
                
        except Exception as e:
            return image, f"❌ Error: {str(e)}", None
    
    def detect_from_upload(self, image, road_name, notes):
        """Detect cracks from uploaded image"""
        if image is None:
            return None, "Please upload an image!", None
        
        try:
            temp_path = "temp_upload.jpg"
            image.save(temp_path)
            
            with open(temp_path, 'rb') as f:
                response = requests.post(
                    f"{self.api_url}/detections/detect/",
                    files={'original_image': f},
                    data={'road_name': road_name, 'notes': notes},
                    timeout=60
                )
            
            os.remove(temp_path)
            
            if response.status_code == 201:
                result = response.json()
                
                detected_img = None
                if result.get('detected_image'):
                    img_resp = requests.get(f"http://localhost:8000{result['detected_image']}")
                    if img_resp.status_code == 200:
                        detected_img = Image.open(io.BytesIO(img_resp.content))
                
                severity_colors = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'SEVERE': '🔴'}
                severity_icon = severity_colors.get(result.get('severity', 'LOW'), '⚪')
                
                msg = f"""
## 📊 Detection Results

| Metric | Value |
|--------|-------|
| **Detection ID** | `{result.get('id')}` |
| **Crack Count** | 🔍 {result.get('crack_count', 0)} |
| **Severity** | {severity_icon} {result.get('severity', 'N/A')} |
| **Crack Density** | 📊 {result.get('crack_density_score', 0):.1f}% |

### 🔧 Recommended Action:
{result.get('suggested_action', 'Consult engineer')}

---
💡 **Use this Detection ID to download the PDF report**
"""
                return detected_img, msg, result.get('id')
            else:
                return image, f"❌ Error: {response.status_code}", None
                
        except Exception as e:
            return image, f"❌ Error: {str(e)}", None
    
    def download_report(self, detection_id):
        """Download PDF report"""
        if not detection_id:
            return "⚠️ Please enter a Detection ID!"
        
        try:
            response = requests.get(
                f"{self.api_url}/detections/{detection_id}/download_report/",
                timeout=60
            )
            
            if response.status_code == 200:
                pdf_path = f"crack_report_{detection_id}.pdf"
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                return f"✅ Report downloaded!\n📄 Saved as: {pdf_path}\n📁 Location: {os.path.abspath(pdf_path)}"
            else:
                return f"❌ Error: {response.text}"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def view_report(self, detection_id):
        """View report in UI (show as text)"""
        if not detection_id:
            return "⚠️ Please enter a Detection ID!"
        
        try:
            response = requests.get(f"{self.api_url}/detections/{detection_id}/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return f"""
## 📄 Report for Detection #{detection_id}

**Date:** {data.get('created_at', 'N/A')}
**Crack Count:** {data.get('crack_count', 0)}
**Severity:** {data.get('severity', 'N/A')}
**Crack Density:** {data.get('crack_density_score', 0):.1f}%

**Location:**
- Latitude: {data.get('latitude', 'N/A')}
- Longitude: {data.get('longitude', 'N/A')}
- Road: {data.get('road_name', 'N/A')}

**Recommended Action:**
{data.get('suggested_action', 'Consult engineer')}

---
💾 Use the "Download Report" button to save the PDF
"""
            else:
                return f"❌ Detection ID {detection_id} not found!"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def get_dashboard_with_charts(self):
        """Get admin dashboard data with charts"""
        if not self.is_admin:
            return None, None, None, None, None, "⚠️ Admin access required. Please login with admin credentials."
        
        try:
            response = requests.get(f"{self.api_url}/detections/dashboard_stats/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                severity = data.get('severity_breakdown', {})
                days_data = data.get('last_7_days', [])
                
                # ========== 1. PIE CHART - Severity Distribution ==========
                fig1, ax1 = plt.subplots(figsize=(6, 4))
                severity_labels = ['LOW', 'MEDIUM', 'HIGH', 'SEVERE']
                severity_counts = [
                    severity.get('LOW', 0),
                    severity.get('MEDIUM', 0),
                    severity.get('HIGH', 0),
                    severity.get('SEVERE', 0)
                ]
                severity_colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
                
                # Filter out zero values
                non_zero = [(l, c) for l, c in zip(severity_labels, severity_counts) if c > 0]
                if non_zero:
                    labels, counts = zip(*non_zero)
                    colors = [severity_colors[severity_labels.index(l)] for l in labels]
                    wedges, texts, autotexts = ax1.pie(counts, labels=labels, colors=colors, 
                                                         autopct='%1.1f%%', startangle=90)
                    ax1.set_title('Crack Severity Distribution', fontsize=14, fontweight='bold')
                else:
                    ax1.text(0.5, 0.5, 'No data available', ha='center', va='center')
                    ax1.set_title('Crack Severity Distribution')
                
                # ========== 2. BAR CHART - Last 7 Days Trend ==========
                fig2, ax2 = plt.subplots(figsize=(8, 4))
                if days_data:
                    dates = [d['date'][5:10] for d in days_data[:7]]
                    counts = [d['count'] for d in days_data[:7]]
                    bars = ax2.bar(dates, counts, color='#3498db', edgecolor='black')
                    ax2.set_xlabel('Date', fontsize=12)
                    ax2.set_ylabel('Number of Detections', fontsize=12)
                    ax2.set_title('Detections - Last 7 Days', fontsize=14, fontweight='bold')
                    ax2.tick_params(axis='x', rotation=45)
                    for bar, count in zip(bars, counts):
                        if count > 0:
                            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                                    str(count), ha='center', va='bottom', fontweight='bold')
                else:
                    ax2.text(0.5, 0.5, 'No data available', ha='center', va='center')
                    ax2.set_title('Detections - Last 7 Days')
                
                # ========== 3. HORIZONTAL BAR CHART - Severity Count ==========
                fig3, ax3 = plt.subplots(figsize=(6, 4))
                y_pos = np.arange(len(severity_labels))
                bars = ax3.barh(y_pos, severity_counts, color=severity_colors)
                ax3.set_yticks(y_pos)
                ax3.set_yticklabels(severity_labels)
                ax3.set_xlabel('Number of Detections', fontsize=12)
                ax3.set_title('Severity Level Counts', fontsize=14, fontweight='bold')
                for i, (label, count) in enumerate(zip(severity_labels, severity_counts)):
                    if count > 0:
                        ax3.text(count + 0.5, i, str(count), va='center', fontweight='bold')
                
                # ========== 4. LINE CHART - Cumulative Growth ==========
                fig4, ax4 = plt.subplots(figsize=(8, 4))
                if days_data:
                    dates = [d['date'][5:10] for d in days_data[:7]]
                    cumulative = []
                    total = 0
                    for d in days_data[:7]:
                        total += d['count']
                        cumulative.append(total)
                    ax4.plot(dates, cumulative, marker='o', linewidth=2, markersize=8, color='#9b59b6')
                    ax4.fill_between(dates, cumulative, alpha=0.3, color='#9b59b6')
                    ax4.set_xlabel('Date', fontsize=12)
                    ax4.set_ylabel('Total Detections', fontsize=12)
                    ax4.set_title('Cumulative Detections Over Time', fontsize=14, fontweight='bold')
                    ax4.tick_params(axis='x', rotation=45)
                    ax4.grid(True, alpha=0.3)
                    for i, (date, count) in enumerate(zip(dates, cumulative)):
                        ax4.text(i, count + 0.5, str(count), ha='center', va='bottom', fontweight='bold')
                else:
                    ax4.text(0.5, 0.5, 'No data available', ha='center', va='center')
                    ax4.set_title('Cumulative Detections Over Time')
                
                # ========== 5. Statistics Text ==========
                total_detections = data.get('total_detections', 0)
                total_cracks = data.get('total_cracks', 0)
                locations_count = len(data.get('location_data', []))
                avg_confidence = data.get('avg_confidence', 0)
                
                # Find most common severity
                if severity_counts:
                    most_common = severity_labels[severity_counts.index(max(severity_counts))]
                else:
                    most_common = 'N/A'
                
                stats_text = f"""
## 📊 Dashboard Statistics

| Metric | Value |
|--------|-------|
| **Total Detections** | {total_detections} |
| **Total Cracks Found** | {total_cracks} |
| **Average Confidence** | {avg_confidence:.1f}% |
| **Locations Mapped** | {locations_count} |

### Severity Summary:
- 🟢 **LOW**: {severity.get('LOW', 0)} detections
- 🟡 **MEDIUM**: {severity.get('MEDIUM', 0)} detections  
- 🟠 **HIGH**: {severity.get('HIGH', 0)} detections
- 🔴 **SEVERE**: {severity.get('SEVERE', 0)} detections

### Performance Indicators:
- **Most Common Severity**: {most_common}
- **Detections with GPS**: {locations_count}
- **Average Cracks per Detection**: {total_cracks/total_detections if total_detections > 0 else 0:.1f}

---
📊 **Charts above show visual representation of your data**
"""
                
                return fig1, fig2, fig3, fig4, stats_text
            else:
                return None, None, None, None, f"❌ Error: {response.status_code}"
        except Exception as e:
            return None, None, None, None, f"❌ Error: {str(e)}"
    
    def get_dashboard(self):
        """Get admin dashboard data (text only)"""
        if not self.is_admin:
            return "⚠️ Admin access required. Please login with admin credentials."
        
        try:
            response = requests.get(f"{self.api_url}/detections/dashboard_stats/", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                severity = data.get('severity_breakdown', {})
                severity_text = f"""
**Severity Breakdown:**
- 🟢 LOW: {severity.get('LOW', 0)}
- 🟡 MEDIUM: {severity.get('MEDIUM', 0)}
- 🟠 HIGH: {severity.get('HIGH', 0)}
- 🔴 SEVERE: {severity.get('SEVERE', 0)}
"""
                
                trend_text = "**Last 7 Days Trend:**\n"
                for day in data.get('last_7_days', []):
                    trend_text += f"- {day['date']}: {day['count']} detections\n"
                
                locations = data.get('location_data', [])
                location_text = f"**Locations with Cracks:** {len(locations)} locations mapped"
                
                return f"""
## 📊 Admin Dashboard

### Overview
| Metric | Value |
|--------|-------|
| **Total Detections** | {data.get('total_detections', 0)} |
| **Total Cracks Found** | {data.get('total_cracks', 0)} |
| **Average Confidence** | {data.get('avg_confidence', 0):.1f}% |

### {severity_text}

### {trend_text}

### {location_text}

---
📍 **GPS Map Data:** {len(locations)} crack locations recorded
"""
            else:
                return f"❌ Error: {response.status_code}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

# Create the Gradio UI
app = CrackDetectionApp()

with gr.Blocks(title="Road Crack Detection System", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🛣️ Road Crack Detection System
    ### AI-Powered Infrastructure Inspection with GPS & Reporting
    """)
    
    with gr.Tabs():
        # Tab 1: Camera Detection with GPS
        with gr.TabItem("📸 Live Camera Detection"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Capture Image")
                    camera_input = gr.Image(type="pil", sources=["webcam"], label="Take a photo", height=350)
                    
                    gr.Markdown("### 📍 GPS Location")
                    with gr.Row():
                        latitude = gr.Number(label="Latitude", value=0.0)
                        longitude = gr.Number(label="Longitude", value=0.0)
                    road_name = gr.Textbox(label="Road Name", placeholder="Enter road name")
                    
                    detect_cam_btn = gr.Button("🔍 Detect Cracks", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### Detection Result")
                    cam_output_img = gr.Image(type="pil", label="Cracks Highlighted", height=350)
                    cam_output_text = gr.Markdown("Waiting for detection...")
                    cam_detection_id = gr.Number(visible=False)
            
            detect_cam_btn.click(
                fn=app.detect_from_camera,
                inputs=[camera_input, latitude, longitude, road_name],
                outputs=[cam_output_img, cam_output_text, cam_detection_id]
            )
        
        # Tab 2: Upload Image
        with gr.TabItem("📤 Upload Image"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Upload Road Image")
                    upload_input = gr.Image(type="pil", label="Choose image", height=350)
                    road_name_upload = gr.Textbox(label="Road Name", placeholder="Enter road name")
                    notes = gr.Textbox(label="Additional Notes", placeholder="Any observations...", lines=3)
                    detect_upload_btn = gr.Button("🔍 Detect Cracks", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### Detection Result")
                    upload_output_img = gr.Image(type="pil", label="Cracks Highlighted", height=350)
                    upload_output_text = gr.Markdown("Waiting for detection...")
                    upload_detection_id = gr.Number(visible=False)
            
            detect_upload_btn.click(
                fn=app.detect_from_upload,
                inputs=[upload_input, road_name_upload, notes],
                outputs=[upload_output_img, upload_output_text, upload_detection_id]
            )
        
        # Tab 3: Reports
        with gr.TabItem("📄 Reports"):
            gr.Markdown("## 📄 Crack Detection Reports")
            
            with gr.Row():
                with gr.Column(scale=1):
                    report_id = gr.Number(label="Detection ID", precision=0)
                    with gr.Row():
                        view_report_btn = gr.Button("👁️ View Report", variant="secondary")
                        download_report_btn = gr.Button("📥 Download PDF Report", variant="primary")
                
                with gr.Column(scale=2):
                    report_view = gr.Markdown("Enter a Detection ID to view report")
            
            view_report_btn.click(
                fn=app.view_report,
                inputs=report_id,
                outputs=report_view
            )
            
            download_report_btn.click(
                fn=app.download_report,
                inputs=report_id,
                outputs=report_view
            )
        
        # Tab 4: Admin Dashboard with Charts
        with gr.TabItem("📊 Admin Dashboard"):
            gr.Markdown("## 👑 Admin Dashboard with Analytics")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Admin Login")
                    admin_user = gr.Textbox(label="Username", placeholder="admin")
                    admin_pass = gr.Textbox(label="Password", type="password", placeholder="admin123")
                    login_btn = gr.Button("Login", variant="primary")
                    login_status = gr.Markdown("Not logged in")
                
                with gr.Column(scale=2):
                    refresh_btn = gr.Button("🔄 Refresh Dashboard", variant="secondary")
                    dashboard_content = gr.Markdown("Login to view dashboard")
            
            # Charts Row 1
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Severity Distribution")
                    pie_chart = gr.Plot(label="Pie Chart")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📈 Last 7 Days Trend")
                    bar_chart = gr.Plot(label="Bar Chart")
            
            # Charts Row 2
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Severity Counts")
                    horizontal_chart = gr.Plot(label="Horizontal Bar Chart")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📈 Cumulative Growth")
                    line_chart = gr.Plot(label="Line Chart")
            
            # Statistics
            with gr.Row():
                with gr.Column(scale=1):
                    stats_text = gr.Markdown("")
            
            login_btn.click(
                fn=app.login,
                inputs=[admin_user, admin_pass],
                outputs=login_status
            )
            
            refresh_btn.click(
                fn=app.get_dashboard_with_charts,
                inputs=[],
                outputs=[pie_chart, bar_chart, horizontal_chart, line_chart, stats_text]
            )
        
        # Tab 5: Instructions
        with gr.TabItem("ℹ️ Instructions"):
            gr.Markdown("""
            ## 📖 How to Use This System
            
            ### 1. Live Camera Detection (with GPS)
            - Click "Live Camera Detection" tab
            - Allow camera access
            - Take a photo of the road
            - Enter GPS coordinates or use auto-detected location
            - Click "Detect Cracks"
            
            ### 2. Upload Image
            - Go to "Upload Image" tab
            - Upload a road image (JPG/PNG)
            - Add road name and notes
            - Click "Detect Cracks"
            
            ### 3. View Reports
            - Go to "Reports" tab
            - Enter Detection ID from detection results
            - Click "View Report" to see details
            - Click "Download PDF Report" to save PDF
            
            ### 4. Admin Dashboard with Charts
            - Login with admin credentials (admin/admin123)
            - Click "Refresh Dashboard"
            - View interactive charts:
              - **Pie Chart**: Severity distribution
              - **Bar Chart**: Daily detection trends
              - **Horizontal Bar**: Severity counts comparison
              - **Line Chart**: Cumulative growth over time
            
            ### Features:
            ✅ Real-time crack detection with YOLOv8
            ✅ GPS location tagging
            ✅ Crack severity classification
            ✅ Crack density scoring
            ✅ PDF report generation
            ✅ Admin dashboard with interactive charts
            ✅ Downloadable reports saved in database
            """)
    
    gr.Markdown("""
    ---
    ### 📞 Support
    **© 2026 Road Crack Detection System | Final Year Project**
    """)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Road Crack Detection System")
    print("="*60)
    print("\n📌 Make sure Django is running: python manage.py runserver")
    print("🌐 Open: http://localhost:7860")
    print("👑 Admin Login: admin / admin123")
    print("="*60 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True
    )