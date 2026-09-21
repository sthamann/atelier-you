"""One resident model, pinned to the explicitly selected RTX PRO 6000."""
import os
import time
from pathlib import Path
from .identity import face_reference

REVISION = 'b3179ad355be050328e483a9dfdd9e60cd62adfa'
MODEL_ID = 'Qwen/Qwen-Image-2.1'
RECIPE = 'atelier-v3-face-anchor-single-view-768x1024-28steps'


class Engine:
    def __init__(self):
        import torch
        from diffusers import QwenImage21Pipeline
        self.torch = torch
        self.pipe = QwenImage21Pipeline.from_pretrained(
            os.environ.get('MODEL_PATH', MODEL_ID), torch_dtype=torch.bfloat16,
            **({} if os.environ.get('MODEL_PATH') else {'revision': REVISION}),
        ).to('cuda')
        self.pipe.set_progress_bar_config(disable=True)

    def generate(self, person: Path, garment, output: Path, description, view='front', front=None):
        from PIL import Image
        descriptions = description if isinstance(description, list) else [description]
        garments = garment if isinstance(garment, list) else [garment]
        with Image.open(person) as source:
            customer = source.convert('RGB')
        face = face_reference(customer)
        if face is not None:
            images = [face, customer]
            prompt = ('IMAGE 1 IS THE FACE IDENTITY ANCHOR. Image 2 is the same person and the body reference. '
                      'Keep the EXACT facial identity, facial proportions, asymmetric details, glasses, nose, '
                      'jaw, stubble and expression from image 1. Do not make a similar-looking fashion model. '
                      'Do not beautify, smooth the skin or change age. ')
        else:
            images = [customer]
            prompt = ('Image 1 is the customer and the identity reference. Preserve their exact facial '
                      'geometry, expression, glasses, age, skin and body proportions. No beautification. ')
        first_garment = len(images) + 1
        for path in garments:
            with Image.open(path) as source:
                images.append(source.convert('RGB'))
        prompt += ('Edit the clothing of this exact person into one full-body photograph wearing all the '
                   'following product references together: ' + '; '.join(
                       f'image {i+first_garment}: {d}' for i, d in enumerate(descriptions)) + '. ')
        if view == 'front':
            prompt += ('Keep the reference head orientation and gaze; do not straighten the head toward '
                       'the camera. Jacket over top if both are selected. Preserve exact product colors, '
                       'textures and cuts. Natural standing pose with arms down, no microphone or props. ')
        else:
            # Rotate the completed look as one image. Multiple product/person
            # references caused duplicate people and dropped outerwear in views.
            with Image.open(front) as source:
                images = [source.convert('RGB')]
            angle = ('90 degrees so the whole body AND head face right in strict side profile'
                     if view == 'side' else
                     '180 degrees so the back of the body AND back of the head face the camera')
            prompt = ('Edit this photograph: rotate the single person ' + angle + '. '
                      'Show only the rotated person, centered alone. Replace the original front view; '
                      'do not keep a second person or a front-view copy. Keep every garment exactly '
                      'as worn in the input photograph, including the outer jacket, hat, trousers '
                      'and shoes. Keep the same person, glasses, hair, build and proportions. '
                      'Keep the same warm off-white studio, lighting and framing. '
                      'For a rear view the face must not be visible. ')
        prompt += ('Full body from head to soles, warm off-white studio, soft light. '
                   'Only one person, no text, no collage, no split screen.')
        for im in images:
            im.thumbnail((1024, 1024))
        started = time.monotonic()
        with self.torch.inference_mode():
            result = self.pipe(prompt=prompt, image=images, width=768, height=1024,
                               num_inference_steps=28,
                               generator=self.torch.Generator('cuda').manual_seed(42)).images[0]
        result.convert('RGB').save(output, 'WEBP', quality=92)
        return round(time.monotonic() - started, 3)
