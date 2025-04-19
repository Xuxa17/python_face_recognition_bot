from botocore.response import StreamingBody
from deepface import DeepFace
from io import IOBase
import numpy as np
import cv2


def compare_faces_bool(image1_streaming_body: IOBase, image2_streaming_body: IOBase) -> bool:
    numpy_image1 = np.fromstring(image1_streaming_body.read(), np.uint8)
    numpy_image2 = np.fromstring(image2_streaming_body.read(), np.uint8)
    image1 = cv2.imdecode(numpy_image1, cv2.IMREAD_COLOR)
    image2 = cv2.imdecode(numpy_image2, cv2.IMREAD_COLOR)

      # Найти лица на втором изображении
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    faces2 = face_cascade.detectMultiScale(gray_image2, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Проверить совпадение для каждого лица на втором изображении
    for (x, y, w, h) in faces2:
        face2 = image2[y:y+h, x:x+w]

        # Сравнить лицо с изображениями модели
        try:
            result = DeepFace.verify(image1, face2, model_name='VGG-Face', enforce_detection=False)
            if result["verified"]:
                return True
        except Exception as e:
            return str(e)

    return False

def has_face_on_image(image_streaming_body: IOBase) -> bool:
    numpy_image = np.fromstring(image_streaming_body.read(), np.uint8)
    image = cv2.imdecode(numpy_image, cv2.IMREAD_COLOR)

    # Найти лица на втором изображении
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        return False
    else:
        return True