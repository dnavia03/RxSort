from picamera2 import Picamera2, Preview
from time import sleep

camera = Picamera2()

camera.start_preview(Preview.QTGL)
camera.start()

print("Camera preview started...")
sleep(2)

input("Position the pill, then press ENTER to take the picture...")

camera.capture_file("python_test.jpg")

print("Picture saved as python_test.jpg")

camera.stop()
camera.stop_preview()
