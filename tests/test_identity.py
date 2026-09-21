import cv2
from PIL import Image
from api.identity import face_reference


def test_no_face_does_not_invent_a_crop():
    assert face_reference(Image.new('RGB',(512,768),'gray')) is None


def test_ambiguous_multiple_faces_abstain(monkeypatch):
    class Detector:
        def detectMultiScale(self,*a,**kw):
            return [(30,20,100,100),(210,20,98,98)]
    monkeypatch.setattr(cv2,'CascadeClassifier',lambda _:Detector())
    assert face_reference(Image.new('RGB',(400,600),'gray')) is None


def test_dominant_face_crop_stays_inside_image(monkeypatch):
    class Detector:
        def detectMultiScale(self,*a,**kw):
            return [(0,0,100,100),(210,200,20,20)]
    monkeypatch.setattr(cv2,'CascadeClassifier',lambda _:Detector())
    image=Image.new('RGB',(400,600),'gray')
    face=face_reference(image)
    assert face is not None and face.width<=400 and face.height<=600
    assert face.getpixel((0,0))==image.getpixel((0,0))
