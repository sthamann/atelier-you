"""Face-detail reference preparation; no recognition, embedding or identity score."""
from PIL import Image


def face_reference(person: Image.Image):
    """Use the clearly dominant face, or abstain when detection is ambiguous."""
    import cv2
    import numpy as np
    gray = cv2.cvtColor(np.asarray(person), cv2.COLOR_RGB2GRAY)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=7, minSize=(50, 50))
    ranked = sorted(faces, key=lambda box: int(box[2]) * int(box[3]), reverse=True)
    if not ranked:
        return None
    x, y, w, h = (int(v) for v in ranked[0])
    if len(ranked) > 1 and int(ranked[1][2]) * int(ranked[1][3]) > w * h * .55:
        return None
    bounds = (max(0, int(x-.15*w)), max(0, int(y-.28*h)),
              min(person.width, int(x+1.15*w)), min(person.height, int(y+1.2*h)))
    return person.crop(bounds)
