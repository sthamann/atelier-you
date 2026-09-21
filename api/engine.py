"""One resident model, pinned to the explicitly selected RTX PRO 6000."""
import os
import time
from pathlib import Path

REVISION = 'b3179ad355be050328e483a9dfdd9e60cd62adfa'
MODEL_ID = 'Qwen/Qwen-Image-2.1'
RECIPE = 'atelier-v1-768x1024-28steps'

class Engine:
    def __init__(self):
        import torch
        from diffusers import QwenImage21Pipeline
        self.torch = torch
        self.pipe = QwenImage21Pipeline.from_pretrained(
            os.environ.get('MODEL_PATH', MODEL_ID),
            torch_dtype=torch.bfloat16,
            **({} if os.environ.get('MODEL_PATH') else {'revision': REVISION}),
        ).to('cuda')
        self.pipe.set_progress_bar_config(disable=True)

    def generate(self, person: Path, garment: Path, output: Path, description: str, view='front', front=None):
        from PIL import Image
        descriptions = description if isinstance(description,list) else [description]
        description = '; '.join(descriptions)
        prompt = (
            'Create a photorealistic premium fashion e-commerce photograph. '
            'The person in image 1 is the customer: preserve their exact face, hairstyle, '
            'age, body proportions, skin tone and identity. Dress that same person in '
            'the fashion item from image 2. Preserve the exact product color, texture, '
            'cut, details and design. Product: ' + description + '. '
            'Show the person from head to shoes, standing naturally in a clean warm '
            'off-white photography studio, soft daylight, realistic fabric and shadows. '
            'Keep other clothes understated and coordinated. Only one person. '
            'No text, no collage, no split screen. Do not change the person to the model in image 2.'
        )
        garments = garment if isinstance(garment,list) else [garment]
        refs = [person] + garments
        if len(garments) > 1:
            prompt = (
                'Create one photorealistic full-body fashion catalog photograph. Image 1 is the customer. '
                'Preserve this exact person, face, glasses, hairstyle, age, body build and identity. '
                'Dress this person in ALL the following reference products together as one coherent outfit: '
                + '; '.join(f'Image {i+2}: {d}' for i,d in enumerate(descriptions)) + '. '
                'Every reference item must appear worn correctly on the same person. Wear the jacket over the top. '
                'Wear the specified trousers, shoes and cap if provided. Preserve every item color, shape and texture. '
                'Front view, standing naturally with arms down. No microphone, no props. '
                'Full body from top of head to soles of shoes. Warm off-white studio, soft daylight, premium editorial photography. '
                'Only one person, no montage, no text, no split-screen.'
            )
        if view != 'front':
            refs.append(front)
            angle = 'strict 90-degree side profile facing right, with the whole body and head turned sideways' if view == 'side' else 'strict rear view, 180 degrees from the front, back of head and back of garment facing the camera, face NOT visible'
            prompt = (
                'Image 1 identifies the customer. The following images show the garments. The LAST image is the approved front-view outfit photograph. '
                'Generate a matching catalog photograph of the exact same person wearing the exact same full outfit as the LAST image, '
                'but photographed from a ' + angle + '. Preserve hairstyle, glasses, body build, clothing colors, garment material, pants and shoes. '
                'Full body head to shoes, consistent warm off-white studio and soft lighting. Natural standing pose, arms down. '
                'No microphone, no props, no text, no montage. Do not show the original front angle. Products: ' + '; '.join(descriptions)
            )
        images = [Image.open(p).convert('RGB') for p in refs]
        for im in images:
            im.thumbnail((1024, 1024))
        started = time.monotonic()
        with self.torch.inference_mode():
            result = self.pipe(prompt=prompt, image=images, width=768, height=1024,
                               num_inference_steps=28,
                               generator=self.torch.Generator('cuda').manual_seed(42)).images[0]
        result.convert('RGB').save(output, 'WEBP', quality=92)
        return round(time.monotonic() - started, 3)
