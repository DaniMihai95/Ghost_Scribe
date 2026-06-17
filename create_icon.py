"""
Script to create Ghost Scribe icon file
"""
from PIL import Image, ImageDraw

def create_ghost_icon():
    """Create a ghost icon in multiple sizes for Windows ICO file."""
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Scale factors
        s = size / 64
        
        # Background circle (dark)
        margin = int(2 * s)
        draw.ellipse([margin, margin, size-margin, size-margin], fill=(26, 26, 46))
        
        # Ghost body
        head_top = int(12 * s)
        head_bottom = int(40 * s)
        head_left = int(16 * s)
        head_right = int(48 * s)
        
        # Draw ghost head (ellipse)
        draw.ellipse([head_left, head_top, head_right, head_bottom], fill=(0, 255, 136))
        
        # Draw ghost body (rectangle)
        body_top = int(26 * s)
        body_bottom = int(52 * s)
        draw.rectangle([head_left, body_top, head_right, body_bottom], fill=(0, 255, 136))
        
        # Draw wavy bottom
        wave_y = int(48 * s)
        wave_height = int(8 * s)
        wave_width = int(8 * s)
        for i in range(4):
            x = head_left + i * wave_width
            if i % 2 == 0:
                draw.ellipse([x, wave_y, x + wave_width, wave_y + wave_height], fill=(0, 255, 136))
        
        # Draw eyes
        eye_size = int(8 * s)
        eye_y = int(22 * s)
        left_eye_x = int(22 * s)
        right_eye_x = int(36 * s)
        
        draw.ellipse([left_eye_x, eye_y, left_eye_x + eye_size, eye_y + eye_size], fill=(0, 0, 0))
        draw.ellipse([right_eye_x, eye_y, right_eye_x + eye_size, eye_y + eye_size], fill=(0, 0, 0))
        
        # Draw eye highlights
        highlight_size = int(3 * s)
        highlight_offset = int(1 * s)
        draw.ellipse([left_eye_x + highlight_offset, eye_y + highlight_offset, 
                      left_eye_x + highlight_offset + highlight_size, eye_y + highlight_offset + highlight_size], 
                     fill=(255, 255, 255))
        draw.ellipse([right_eye_x + highlight_offset, eye_y + highlight_offset,
                      right_eye_x + highlight_offset + highlight_size, eye_y + highlight_offset + highlight_size], 
                     fill=(255, 255, 255))
        
        images.append(image)
    
    # Save as ICO
    images[0].save('ghost_scribe.ico', format='ICO', sizes=[(s, s) for s in sizes], 
                   append_images=images[1:])
    print("Created ghost_scribe.ico")
    
    # Also save a PNG for reference
    images[-1].save('ghost_scribe.png', format='PNG')
    print("Created ghost_scribe.png")

if __name__ == "__main__":
    create_ghost_icon()
