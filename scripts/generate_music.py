import os
os.environ['CUDA_VISIBLE_DEVICES']='GPU-c5489862-1768-0719-a514-b0f5ad58d976'
import torch
import scipy.io.wavfile as wav
from transformers import AutoProcessor, MusicgenForConditionalGeneration
processor=AutoProcessor.from_pretrained('facebook/musicgen-small')
model=MusicgenForConditionalGeneration.from_pretrained('facebook/musicgen-small').to('cuda')
inputs=processor(text=['Minimal luxury fashion runway instrumental, relaxed electronic house beat, warm deep bass, soft syncopated keyboard chords, crisp percussion, no vocals, 108 BPM'],padding=True,return_tensors='pt').to('cuda')
with torch.inference_mode():
 audio=model.generate(**inputs,max_new_tokens=1400,do_sample=True,guidance_scale=3)
wav.write('/home/aime/atelier-tryon/music.wav',model.config.audio_encoder.sampling_rate,audio[0].cpu().numpy().T)
print('Music ready',flush=True)
