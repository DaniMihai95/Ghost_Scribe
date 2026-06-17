"""Convert image.png to .ico file for the application"""
from PIL import Image
import sys

def convert_image_to_icon():
    """Convert image.png to ghost_scribe.ico with multiple sizes."""
    try:
        # Load the image
        img = Image.open("image.png")
        print(f"Loaded image.png: {img.size}, mode: {img.mode}")
        
        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Make the image square by padding (important for icons)
        width, height = img.size
        max_dim = max(width, height)
        
        # Create square canvas with transparent background
        square_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))
        
        # Paste original image centered
        offset_x = (max_dim - width) // 2
        offset_y = (max_dim - height) // 2
        square_img.paste(img, (offset_x, offset_y))
        
        print(f"Created square image: {square_img.size}")
        
        # Windows ICO standard sizes (must have these for proper display)
        sizes = [16, 24, 32, 48, 64, 128, 256]
        icons = []
        
        for size in sizes:
            # Use high-quality resampling
            resized = square_img.resize((size, size), Image.Resampling.LANCZOS)
            icons.append(resized)
            print(f"  Created {size}x{size} icon")
        
        # Save as ICO - the largest icon first, then smaller ones
        # Reverse order: largest to smallest for better Windows compatibility
        icons_reversed = icons[::-1]
        icons_reversed[0].save(
            "ghost_scribe.ico", 
            format='ICO',
            append_images=icons_reversed[1:],
            sizes=[(s, s) for s in sizes[::-1]]
        )
        print("Created ghost_scribe.ico from image.png")
        
        # Also save a PNG version for the tray icon
        square_img.resize((256, 256), Image.Resampling.LANCZOS).save("ghost_scribe.png", format='PNG')
        print("Created ghost_scribe.png (256x256) from image.png")
        
        return True
        
    except FileNotFoundError:
        print("ERROR: image.png not found!")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = convert_image_to_icon()
    sys.exit(0 if success else 1)
