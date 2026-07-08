from ultralytics import YOLO
import cv2
import numpy as np
import os


class CrackDetector:
    def __init__(self):
        # UPDATE THIS PATH
        self.model_path = r"C:\Users\SAYAL\runs\detect\train2\weights\best.pt"
        self.model = None
        self.load_model()

    def load_model(self):
        """Load YOLO model"""
        if os.path.exists(self.model_path):
            try:
                self.model = YOLO(self.model_path)
                print(f"✅ Model loaded successfully from {self.model_path}")
            except Exception as e:
                print(f"❌ Error loading model: {e}")
                self.model = None
        else:
            print(f"⚠️ Model not found at {self.model_path}")
            self.model = None

    def detect_cracks(self, image_path):
        """Perform crack detection on image"""
        if self.model is None:
            self.load_model()
            if self.model is None:
                return {
                    'crack_count': 0,
                    'confidence_score': 0.0,
                    'crack_type': 'UNKNOWN',
                    'severity': 'LOW',
                    'annotated_image': None
                }

        try:
            results = self.model.predict(image_path, conf=0.25)

            if len(results) > 0:
                result = results[0]
                crack_count = len(result.boxes) if result.boxes is not None else 0

                confidence = 0.0
                if crack_count > 0 and result.boxes is not None:
                    confidences = result.boxes.conf.cpu().numpy()
                    confidence = float(np.mean(confidences))

                crack_type = self.determine_crack_type(result)
                severity = self.determine_severity(crack_count, confidence)
                annotated_img = result.plot()

                return {
                    'crack_count': crack_count,
                    'confidence_score': confidence,
                    'crack_type': crack_type,
                    'severity': severity,
                    'annotated_image': annotated_img
                }
        except Exception as e:
            print(f"Error during detection: {e}")

        return {
            'crack_count': 0,
            'confidence_score': 0.0,
            'crack_type': 'UNKNOWN',
            'severity': 'LOW',
            'annotated_image': None
        }

    def determine_crack_type(self, result):
        if result.boxes is None or len(result.boxes) == 0:
            return 'UNKNOWN'

        boxes = result.boxes.xyxy.cpu().numpy()
        if len(boxes) == 0:
            return 'UNKNOWN'

        aspect_ratios = []
        for box in boxes:
            width = box[2] - box[0]
            height = box[3] - box[1]
            if height > 0:
                aspect_ratios.append(width / height)

        avg_aspect = np.mean(aspect_ratios) if aspect_ratios else 0

        if avg_aspect > 3:
            return 'LONGITUDINAL'
        elif avg_aspect < 0.33:
            return 'TRANSVERSE'
        elif len(boxes) > 5:
            return 'ALLIGATOR'
        else:
            return 'BLOCK'

    def determine_severity(self, crack_count, confidence):
        if crack_count == 0:
            return 'LOW'
        elif crack_count <= 3:
            return 'MEDIUM'
        elif crack_count <= 7:
            return 'HIGH'
        else:
            return 'SEVERE'


detector = CrackDetector()