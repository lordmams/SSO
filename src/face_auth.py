import face_recognition
import numpy as np
import cv2
from base64 import b64decode
import io

def process_face_image(image_data):
    """Convert base64 image to face encoding"""
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Convert BGR to RGB
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Get face encoding
        face_locations = face_recognition.face_locations(rgb_img)
        if not face_locations:
            return None
            
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not face_encodings:
            return None
            
        return face_encodings[0]
    except Exception as e:
        print(f"Error processing face image: {e}")
        return None