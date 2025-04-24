import cv2
from PIL import Image

class ImageCapture:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
    
    def take_photo(self):
        _, frame = self.cap.read()
        image = Image.fromarray(frame)
        return image

