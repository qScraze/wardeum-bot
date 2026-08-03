import io
import math
import random
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices("0123456789", k=length))

def generate_captcha_gif(code: str, width: int = 320, height: int = 120, frames: int = 30, fps: int = 10) -> bytes:
    """
    Generate a fast, continuous kinetic optical illusion GIF captcha.
    - Captcha length: 3 seconds (30 frames at 10 FPS).
    - Background moves rapidly in a single random straight direction without stopping.
    - Foreground (text) remains stationary.
    """
    # 1. Create a binary text mask (255 for text pixels, 0 for background)
    mask_img = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask_img)
    
    # Calculate absolute path to Inter-Bold.ttf dynamically
    current_dir = os.path.dirname(os.path.abspath(__file__))  # bot/services
    bot_dir = os.path.dirname(current_dir)  # bot
    font_path = os.path.join(bot_dir, "Inter-Bold.ttf")
    
    try:
        font = ImageFont.truetype(font_path, 65)
    except IOError:
        font = ImageFont.load_default(size=65) if hasattr(ImageFont, "load_default") else ImageFont.load_default()
        
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
    speed = 3.0  # Speed of movement (3 grains/6px per frame)
    max_shift = 200  # Max accumulated pixel shift (with buffer)
    
    big_width = width + 2 * max_shift
    big_height = height + 2 * max_shift
    
    # Generate high-contrast monochrome noise (0 or 255)
    small_noise = np.random.choice([0, 255], size=(big_height // grain, big_width // grain), p=[0.5, 0.5]).astype(np.uint8)
    
    # Upscale noise to create blocky grain pattern
    big_noise = np.repeat(np.repeat(small_noise, grain, axis=0), grain, axis=1)
    
    # Random angle for movement
    angle = random.uniform(0, 2 * math.pi)
    
    image_frames = []
    for t in range(frames):
        # Linear background movement in the chosen direction
        current_shift_grains = t * speed
        dx = int(round(current_shift_grains * math.cos(angle))) * grain
        dy = int(round(current_shift_grains * math.sin(angle))) * grain
            
        # Crop background slice
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
