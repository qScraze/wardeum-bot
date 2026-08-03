import io
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices("0123456789", k=length))

def generate_captcha_gif(code: str, width: int = 320, height: int = 120, frames: int = 24, fps: int = 15) -> bytes:
    """
    Generate a kinetic optical illusion GIF captcha.
    Both foreground (text) and background consist of the exact same monochrome noise pattern (2x2 grain size).
    The background moves in a circular path over time, while the foreground remains stationary.
    This makes the text completely invisible in a static frame but readable in animation.
    """
    # 1. Create a binary text mask (255 for text pixels, 0 for background)
    mask_img = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask_img)
    
    try:
        font = ImageFont.truetype("arialbd.ttf", 55)
    except IOError:
        font = ImageFont.load_default(size=55) if hasattr(ImageFont, "load_default") else ImageFont.load_default()
        
    # Calculate text position and draw it
    text_bbox = draw_mask.textbbox((0, 0), code, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    draw_mask.text(
        ((width - text_width) // 2, (height - text_height) // 2 - 5),
        code,
        font=font,
        fill=255
    )
    
    # Convert mask to float numpy array [0.0, 1.0]
    mask = np.array(mask_img) / 255.0
    
    # 2. Setup noise parameters
    grain = 2  # Grain size of the static noise (2x2 pixels)
    max_shift_grains = 5
    max_shift = max_shift_grains * grain  # Maximum pixel shift (10px)
    
    big_width = width + 2 * max_shift
    big_height = height + 2 * max_shift
    
    # Generate high-contrast monochrome noise (0 or 255)
    small_noise = np.random.choice([0, 255], size=(big_height // grain, big_width // grain), p=[0.5, 0.5]).astype(np.uint8)
    
    # Upscale noise to create blocky grain pattern
    big_noise = np.repeat(np.repeat(small_noise, grain, axis=0), grain, axis=1)
    
    image_frames = []
    for t in range(frames):
        # Calculate circular offset for the background
        angle = 2 * math.pi * t / frames
        dx = int(round(max_shift_grains * math.cos(angle))) * grain
        dy = int(round(max_shift_grains * math.sin(angle))) * grain
        
        # Crop background slice (shifting over time)
        bg_slice = big_noise[max_shift + dy : max_shift + dy + height, max_shift + dx : max_shift + dx + width]
        
        # Crop foreground slice (always stationary at center)
        fg_slice = big_noise[max_shift : max_shift + height, max_shift : max_shift + width]
        
        # Merge background and foreground using the text mask
        frame_data = (bg_slice * (1.0 - mask) + fg_slice * mask).astype(np.uint8)
        
        # Convert to P-mode image for GIF format
        frame_img = Image.fromarray(frame_data, 'L').convert('P')
        image_frames.append(frame_img)
        
    # 3. Save as animated GIF to memory
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
