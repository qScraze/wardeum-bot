import io
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices("0123456789", k=length))

def generate_captcha_gif(code: str, width: int = 320, height: int = 120, frames: int = 100, fps: int = 10) -> bytes:
    """
    Generate a advanced kinetic optical illusion GIF captcha.
    - Captcha length: 10 seconds (100 frames at 10 FPS).
    - Phase 1 (4 seconds, frames 0-39): Background moves rapidly in direction 1. Text is stationary (visible).
    - Phase 2 (2 seconds, frames 40-59): Background stops completely (dx=0, dy=0) and text texture merges (completely hidden).
    - Phase 3 (4 seconds, frames 60-99): Background resumes rapid movement in direction 2. Text is stationary (visible).
    """
    # 1. Create a binary text mask (255 for text pixels, 0 for background)
    mask_img = Image.new('L', (width, height), 0)
    draw_mask = ImageDraw.Draw(mask_img)
    
    # Load Inter-Bold font from bot directory
    try:
        font = ImageFont.truetype("bot/Inter-Bold.ttf", 65)
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
    speed = 2.0  # Speed of movement (2 grains/4px per frame)
    
    # Phases (4s motion, 2s pause, 4s motion)
    phase1_end = 40
    phase2_end = 60
    
    max_shift = 350  # Max accumulated pixel shift (with buffer)
    
    big_width = width + 2 * max_shift
    big_height = height + 2 * max_shift
    
    # Generate high-contrast monochrome noise (0 or 255)
    small_noise = np.random.choice([0, 255], size=(big_height // grain, big_width // grain), p=[0.5, 0.5]).astype(np.uint8)
    
    # Upscale noise to create blocky grain pattern
    big_noise = np.repeat(np.repeat(small_noise, grain, axis=0), grain, axis=1)
    
    # Random directions
    angle1 = random.uniform(0, 2 * math.pi)
    angle2 = angle1 + math.pi + random.uniform(-math.pi/3, math.pi/3)
    
    x_offset = 0.0
    y_offset = 0.0
    
    image_frames = []
    for t in range(frames):
        if t < phase1_end:
            # Phase 1: Movement 1
            x_offset += speed * math.cos(angle1)
            y_offset += speed * math.sin(angle1)
            
            dx = int(round(x_offset)) * grain
            dy = int(round(y_offset)) * grain
            
            bg_slice = big_noise[max_shift + dy : max_shift + dy + height, max_shift + dx : max_shift + dx + width]
            fg_slice = big_noise[max_shift : max_shift + height, max_shift : max_shift + width]
            
        elif t < phase2_end:
            # Phase 2: Pause (Perfect merge)
            dx = int(round(x_offset)) * grain
            dy = int(round(y_offset)) * grain
            
            bg_slice = big_noise[max_shift + dy : max_shift + dy + height, max_shift + dx : max_shift + dx + width]
            # Copy background to foreground to achieve complete invisibility (perfect texture alignment)
            fg_slice = bg_slice
            
        else:
            # Phase 3: Movement 2
            x_offset += speed * math.cos(angle2)
            y_offset += speed * math.sin(angle2)
            
            dx = int(round(x_offset)) * grain
            dy = int(round(y_offset)) * grain
            
            bg_slice = big_noise[max_shift + dy : max_shift + dy + height, max_shift + dx : max_shift + dx + width]
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
