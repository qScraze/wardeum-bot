import io
import random
import string
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices(string.digits, k=length))

def generate_captcha_gif(code: str, width: int = 320, height: int = 120, frames: int = 30, fps: int = 20) -> bytes:
    """Generate an animated GIF captcha with TV static noise."""
    image_frames = []
    
    try:
        font = ImageFont.truetype("arialbd.ttf", 60)
    except IOError:
        font = ImageFont.load_default(size=60) if hasattr(ImageFont, "load_default") else ImageFont.load_default()

    for i in range(frames):
        # Generate TV static noise
        noise = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        img = Image.fromarray(noise, 'RGB')
        
        # Overlay semi-transparent dark panel
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 150))
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        
        # Calculate text position and add jitter
        text_bbox = draw.textbbox((0, 0), code, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        base_x = (width - text_width) // 2
        base_y = (height - text_height) // 2
        
        # Add slight per-frame offset
        x_offset = random.randint(-3, 3)
        y_offset = random.randint(-3, 3)
        
        # Add slight alpha variation (shimmer)
        alpha = random.randint(200, 255)
        text_color = (255, 255, 255, alpha)
        
        draw.text((base_x + x_offset, base_y + y_offset), code, font=font, fill=text_color)
        
        image_frames.append(img.convert('P', palette=Image.ADAPTIVE))
        
    out_io = io.BytesIO()
    image_frames[0].save(
        out_io,
        format='GIF',
        save_all=True,
        append_images=image_frames[1:],
        duration=1000 // fps,
        loop=0
    )
    return out_io.getvalue()
