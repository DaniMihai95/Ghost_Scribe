"""
Ghost Scribe - Local AI Writing Assistant
Runs on Intel NPU (Neural Processing Unit)
Press Ctrl+Space to process clipboard content
"""

import sys
import os
from pathlib import Path

# Runtime hook handles DLL paths - no additional setup needed here

import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox
import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw
import openvino_genai
import traceback

# --- CONFIGURATION ---
def get_model_path():
    """Get the model path, handling both development and packaged scenarios."""
    possible_paths = []
    
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        exe_dir = Path(os.path.dirname(sys.executable))
        possible_paths = [
            exe_dir / "tinyllama-model",
            exe_dir / "_internal" / "tinyllama-model",
        ]
        if hasattr(sys, '_MEIPASS'):
            possible_paths.append(Path(sys._MEIPASS) / "tinyllama-model")
    else:
        # Running as script
        script_dir = Path(__file__).parent.resolve()
        possible_paths = [
            script_dir / "tinyllama-model",
            Path.cwd() / "tinyllama-model",
        ]
    
    for path in possible_paths:
        if path.exists():
            print(f"[MODEL] Found at: {path}")
            return path.resolve()
    
    # Return first path for error message
    print(f"[MODEL] Not found! Checked: {possible_paths}")
    return possible_paths[0] if possible_paths else Path("tinyllama-model")

MODEL_PATH = get_model_path()
DEVICE = "NPU"  # Intel NPU for fast inference
HOTKEY = "ctrl+space"
APP_NAME = "Ghost Scribe"
VERSION = "1.0.0"

# --- COLOR PALETTE (Matching the logo) ---
COLORS = {
    'bg_dark': '#0a0e1a',
    'bg_card': '#0f1628',
    'bg_header': '#141d35',
    'accent_cyan': '#00d4ff',
    'accent_purple': '#8b5cf6',
    'accent_glow': '#00ffaa',
    'text_primary': '#ffffff',
    'text_secondary': '#8892a8',
    'text_muted': '#4a5568',
    'border': '#1e2a4a',
    'button_bg': '#1a2744',
    'button_hover': '#243352',
    'success': '#10b981',
    'error': '#ef4444',
    'warning': '#f59e0b',
}

# --- GLOBAL STATE ---
pipe = None
is_loading = True
load_error = None
root = None
popup_window = None
output_box = None
icon = None
status_label = None
device_label = None
is_processing = False  # Prevent multiple simultaneous requests

# --- 1. MODEL LOADER (Background Thread) ---
def load_model():
    """Load the AI model - try NPU first for speed, fall back to CPU."""
    global pipe, is_loading, DEVICE, load_error
    
    import traceback as tb
    
    # Try NPU first (faster), then CPU (more compatible)
    devices_to_try = ["NPU", "CPU"]
    
    # First check if model exists
    if not MODEL_PATH.exists():
        load_error = f"Model folder not found:\n{MODEL_PATH}\n\nPlease ensure tinyllama-model folder exists next to the executable."
        is_loading = False
        notify("Error", "Model folder not found")
        return
    
    # Check for required files
    required_files = ["openvino_model.xml", "openvino_model.bin"]
    missing = [f for f in required_files if not (MODEL_PATH / f).exists()]
    if missing:
        load_error = f"Missing model files:\n{', '.join(missing)}\n\nModel folder: {MODEL_PATH}"
        is_loading = False
        notify("Error", "Missing model files")
        return
    
    last_error = None
    for device in devices_to_try:
        try:
            pipe = openvino_genai.LLMPipeline(str(MODEL_PATH), device)
            
            # Warmup run
            config = openvino_genai.GenerationConfig()
            config.max_new_tokens = 5
            result = pipe.generate("Hi", config)
            
            DEVICE = device
            is_loading = False
            load_error = None
            notify("Ghost Scribe Ready", f"Running on {device}. Press {HOTKEY} to use.")
            return
            
        except Exception as e:
            last_error = str(e)
            pipe = None
            continue
    
    # All devices failed
    load_error = f"Could not initialize AI model.\n\nLast error:\n{last_error}\n\nTried devices: {', '.join(devices_to_try)}\nModel path: {MODEL_PATH}"
    notify("Error", "Could not load AI model")
    is_loading = False
    
    # Write error to log file
    try:
        log_path = MODEL_PATH.parent / "ghostscribe_error.log"
        with open(log_path, 'w') as f:
            f.write(f"Ghost Scribe Error Log\n")
            f.write(f"={'=' * 49}\n")
            f.write(f"Model Path: {MODEL_PATH}\n")
            f.write(f"Model Exists: {MODEL_PATH.exists()}\n")
            if MODEL_PATH.exists():
                f.write(f"Model Contents: {list(MODEL_PATH.iterdir())}\n")
            f.write(f"\nLast Error: {last_error}\n")
            f.write(f"\nFull traceback:\n{tb.format_exc()}")
    except Exception:
        pass

# --- 2. THE AI WORKER ---
def detect_content_type(text):
    """Detect the type of content in clipboard."""
    code_indicators = ['def ', 'class ', 'import ', 'function ', 'const ', 'let ', 'var ', 
                       '{', '}', '=>', '<?php', '<html', '#include', 'public ', 'private ']
    if any(indicator in text for indicator in code_indicators):
        return "code"
    
    if '@' in text and ('dear' in text.lower() or 'hi ' in text.lower() or 'hello' in text.lower()):
        return "email"
    
    if len(text) > 500:
        return "long_text"
    
    return "general"

def get_prompt_for_type(text, content_type):
    """Generate appropriate prompt based on content type."""
    prompts = {
        "code": f"Briefly improve this code:\n{text}\n\nImproved:",
        "email": f"Rewrite concisely:\n{text}\n\nRewritten:",
        "long_text": f"Summarize in 3 bullets:\n{text}\n\nSummary:",
        "general": f"Rewrite concisely:\n{text}\n\nRewritten:"
    }
    return prompts.get(content_type, prompts["general"])

def process_clipboard(text, custom_action=None):
    """Process the given text with AI."""
    global load_error
    
    if is_loading:
        return "⏳ AI model is still loading...\n\nPlease wait a moment for initialization to complete."
    
    if load_error:
        return f"❌ Model Error\n\n{load_error}"
    
    if pipe is None:
        return "❌ Model not initialized\n\nThe AI model could not be loaded. Please check the console output for details."
    
    if not text:
        return "📋 Clipboard is empty\n\nCopy some text first, then press Ctrl+Space or click Reprocess."
    
    # Limit input text length to avoid long processing
    if len(text) > 2000:
        text = text[:2000] + "..."
    
    if custom_action:
        prompt = f"{custom_action}:\n\n{text}"
    else:
        content_type = detect_content_type(text)
        prompt = get_prompt_for_type(text, content_type)
    
    try:
        config = openvino_genai.GenerationConfig()
        config.max_new_tokens = 256  # Longer responses
        config.do_sample = False
        
        start_time = time.time()
        response = pipe.generate(prompt, config)
        elapsed = time.time() - start_time
        
        tokens_approx = len(response.split())
        speed = tokens_approx / elapsed if elapsed > 0 else 0
        
        return f"{response}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ Generated in {elapsed:.1f}s  •  ~{speed:.1f} tokens/sec  •  {DEVICE}"
    except Exception as e:
        return f"❌ Generation Error\n\n{str(e)}"

# --- 3. PROFESSIONAL GUI ---
class ModernButton(tk.Canvas):
    """A modern styled button with hover effects."""
    def __init__(self, parent, text, command, accent=False, width=120, **kwargs):
        super().__init__(parent, width=width, height=36, highlightthickness=0, 
                         bg=COLORS['bg_card'], **kwargs)
        
        self.command = command
        self.accent = accent
        self.text = text
        self.hover = False
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        
        self._draw()
    
    def _draw(self):
        self.delete("all")
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        
        if self.accent:
            fill = COLORS['accent_cyan'] if not self.hover else COLORS['accent_glow']
            text_color = COLORS['bg_dark']
        else:
            fill = COLORS['button_hover'] if self.hover else COLORS['button_bg']
            text_color = COLORS['text_primary']
        
        # Rounded rectangle
        r = 8
        self.create_rounded_rect(2, 2, w-2, h-2, r, fill=fill, outline=COLORS['border'])
        
        # Text
        self.create_text(w//2, h//2, text=self.text, fill=text_color, 
                        font=("Segoe UI Semibold", 9))
    
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
            x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_enter(self, e):
        self.hover = True
        self._draw()
    
    def _on_leave(self, e):
        self.hover = False
        self._draw()
    
    def _on_click(self, e):
        if self.command:
            self.command()

def create_popup_window(text=""):
    """Creates the professional popup window."""
    global popup_window, output_box, status_label, device_label
    
    if popup_window is not None and popup_window.winfo_exists():
        popup_window.deiconify()
        popup_window.lift()
        popup_window.focus_force()
        # Process the NEW text passed from hotkey
        threading.Thread(target=lambda: run_and_display(text), daemon=True).start()
        return
    
    popup_window = tk.Toplevel(root)
    popup_window.title(APP_NAME)
    popup_window.geometry("680x560")
    popup_window.attributes("-topmost", True)
    popup_window.configure(bg=COLORS['bg_dark'])
    popup_window.resizable(True, True)
    popup_window.minsize(500, 400)
    
    # Remove default window decorations for cleaner look (optional)
    # popup_window.overrideredirect(True)
    
    # Center window
    popup_window.update_idletasks()
    x = (popup_window.winfo_screenwidth() // 2) - (340)
    y = (popup_window.winfo_screenheight() // 2) - (280)
    popup_window.geometry(f'+{x}+{y}')
    
    # === HEADER ===
    header = tk.Frame(popup_window, bg=COLORS['bg_header'], height=70)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    
    # Logo area
    logo_frame = tk.Frame(header, bg=COLORS['bg_header'])
    logo_frame.pack(side=tk.LEFT, padx=20, pady=15)
    
    # Ghost icon (text-based for simplicity)
    icon_label = tk.Label(
        logo_frame,
        text="👻",
        font=("Segoe UI Emoji", 24),
        bg=COLORS['bg_header'],
        fg=COLORS['accent_cyan']
    )
    icon_label.pack(side=tk.LEFT)
    
    title_frame = tk.Frame(logo_frame, bg=COLORS['bg_header'])
    title_frame.pack(side=tk.LEFT, padx=12)
    
    title = tk.Label(
        title_frame,
        text="GHOST SCRIBE",
        font=("Segoe UI", 16, "bold"),
        bg=COLORS['bg_header'],
        fg=COLORS['text_primary']
    )
    title.pack(anchor=tk.W)
    
    subtitle = tk.Label(
        title_frame,
        text="Local NPU Utility",
        font=("Segoe UI", 9),
        bg=COLORS['bg_header'],
        fg=COLORS['text_secondary']
    )
    subtitle.pack(anchor=tk.W)
    
    # Status area (right side of header)
    status_frame = tk.Frame(header, bg=COLORS['bg_header'])
    status_frame.pack(side=tk.RIGHT, padx=20, pady=15)
    
    device_label = tk.Label(
        status_frame,
        text=f"● {DEVICE}" if not is_loading else "● Loading...",
        font=("Segoe UI", 9),
        bg=COLORS['bg_header'],
        fg=COLORS['success'] if not is_loading else COLORS['warning']
    )
    device_label.pack(anchor=tk.E)
    
    status_label = tk.Label(
        status_frame,
        text="Ready",
        font=("Segoe UI", 9),
        bg=COLORS['bg_header'],
        fg=COLORS['text_muted']
    )
    status_label.pack(anchor=tk.E)
    
    # === DIVIDER LINE ===
    divider = tk.Frame(popup_window, bg=COLORS['accent_cyan'], height=2)
    divider.pack(fill=tk.X)
    
    # === MAIN CONTENT ===
    content = tk.Frame(popup_window, bg=COLORS['bg_dark'], padx=20, pady=16)
    content.pack(fill=tk.BOTH, expand=True)
    
    # Output container with border effect
    output_container = tk.Frame(content, bg=COLORS['border'], padx=1, pady=1)
    output_container.pack(fill=tk.BOTH, expand=True)
    
    output_inner = tk.Frame(output_container, bg=COLORS['bg_card'])
    output_inner.pack(fill=tk.BOTH, expand=True)
    
    # Output text
    output_box = scrolledtext.ScrolledText(
        output_inner,
        wrap=tk.WORD,
        font=("Consolas", 11),
        bg=COLORS['bg_card'],
        fg=COLORS['text_primary'],
        insertbackground=COLORS['accent_cyan'],
        selectbackground=COLORS['accent_purple'],
        selectforeground=COLORS['text_primary'],
        relief=tk.FLAT,
        padx=16,
        pady=16,
        borderwidth=0,
        highlightthickness=0
    )
    output_box.pack(fill=tk.BOTH, expand=True)
    
    # Configure scrollbar colors (limited in tkinter)
    output_box.vbar.configure(troughcolor=COLORS['bg_card'], bg=COLORS['button_bg'])
    
    # === FOOTER / BUTTON BAR ===
    footer = tk.Frame(popup_window, bg=COLORS['bg_dark'], height=70)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    footer.pack_propagate(False)
    
    # Top border
    footer_border = tk.Frame(footer, bg=COLORS['border'], height=1)
    footer_border.pack(fill=tk.X)
    
    button_container = tk.Frame(footer, bg=COLORS['bg_dark'])
    button_container.pack(expand=True)
    
    # Left buttons
    left_btns = tk.Frame(button_container, bg=COLORS['bg_dark'])
    left_btns.pack(side=tk.LEFT, padx=20)
    
    copy_btn = ModernButton(left_btns, "📋 Copy Result", copy_result, accent=True, width=130)
    copy_btn.pack(side=tk.LEFT, padx=4)
    
    reprocess_btn = ModernButton(left_btns, "🔄 Reprocess", 
                                  lambda: threading.Thread(target=lambda: run_and_display(pyperclip.paste().strip()), daemon=True).start(),
                                  width=120)
    reprocess_btn.pack(side=tk.LEFT, padx=4)
    
    summarize_btn = ModernButton(left_btns, "📝 Summarize",
                                  lambda: threading.Thread(target=lambda: run_custom_action("Summarize briefly"), daemon=True).start(),
                                  width=110)
    summarize_btn.pack(side=tk.LEFT, padx=4)
    
    # Right buttons
    right_btns = tk.Frame(button_container, bg=COLORS['bg_dark'])
    right_btns.pack(side=tk.RIGHT, padx=20)
    
    close_btn = ModernButton(right_btns, "✕ Close", popup_window.withdraw, width=90)
    close_btn.pack(side=tk.RIGHT, padx=4)
    
    # Handle window close
    popup_window.protocol("WM_DELETE_WINDOW", popup_window.withdraw)
    
    # Start processing with the text passed in
    threading.Thread(target=lambda: run_and_display(text), daemon=True).start()

def run_and_display(text=""):
    """Run AI processing on the given text."""
    global is_processing
    
    # Force reset if stuck
    is_processing = False
    is_processing = True
    
    try:
        update_device_status()
        update_status("Processing...")
        
        # Use the text passed from hotkey - already read at press time
        clipboard_text = text.strip() if text else ""
        
        if not clipboard_text:
            update_popup("📋 Clipboard is empty\n\nCopy some text first, then press Ctrl+Space.")
            return
        
        preview = clipboard_text[:80] if len(clipboard_text) > 80 else clipboard_text
        update_popup(f"⏳ Processing...\n\n\"{preview}\"\n\nRunning on {DEVICE}...")
        
        # Pass the text directly to AI
        result = process_clipboard(clipboard_text)
        update_popup(result)
        update_status("Ready")
    except Exception as e:
        update_popup(f"❌ Error: {str(e)}")
        update_status("Error")
    finally:
        is_processing = False

def run_custom_action(action):
    """Run a custom action on clipboard content."""
    update_status(action + "...")
    clipboard_text = pyperclip.paste().strip()
    update_popup(f"⏳ {action}...\n\nProcessing on {DEVICE}...")
    result = process_clipboard(clipboard_text, custom_action=action)
    update_popup(result)
    update_status("Ready")

def update_popup(text):
    """Update output box safely from any thread."""
    if output_box is not None and popup_window is not None and popup_window.winfo_exists():
        def update():
            output_box.delete("1.0", tk.END)
            output_box.insert(tk.END, text)
        root.after(0, update)

def update_status(text):
    """Update status label safely from any thread."""
    if status_label is not None:
        root.after(0, lambda: status_label.config(text=text))

def update_device_status():
    """Update device label based on current state."""
    if device_label is not None:
        if is_loading:
            root.after(0, lambda: device_label.config(text="● Loading...", fg=COLORS['warning']))
        elif load_error:
            root.after(0, lambda: device_label.config(text="● Error", fg=COLORS['error']))
        else:
            root.after(0, lambda: device_label.config(text=f"● {DEVICE}", fg=COLORS['success']))

def copy_result():
    """Copy result to clipboard."""
    if output_box is not None:
        result = output_box.get("1.0", tk.END).strip()
        if "━━━" in result:
            result = result.split("━━━")[0].strip()
        pyperclip.copy(result)
        update_status("Copied!")
        root.after(1500, lambda: update_status("Ready"))

def show_window(text=""):
    """Show popup window with the given text to process."""
    if root:
        root.after(0, lambda: create_popup_window(text))

def on_hotkey():
    """Handle hotkey press - read clipboard IMMEDIATELY."""
    # Read clipboard RIGHT NOW before any threading/scheduling
    import time
    time.sleep(0.05)  # Small delay to ensure clipboard is ready
    text = pyperclip.paste().strip()
    show_window(text)

# --- 4. NOTIFICATION ---
def notify(title, message):
    """Show a notification."""
    print(f"[{title}] {message}")

# --- 5. SYSTEM TRAY ---
def create_tray_icon():
    """Load icon from image.png or create fallback."""
    try:
        if getattr(sys, 'frozen', False):
            exe_dir = Path(os.path.dirname(sys.executable))
            icon_path = exe_dir / "image.png"
        else:
            icon_path = Path("./image.png")
        
        if icon_path.exists():
            image = Image.open(icon_path)
            image = image.resize((64, 64), Image.Resampling.LANCZOS)
            return image
    except Exception as e:
        print(f"[ICON] Could not load image.png: {e}")
    
    # Fallback icon
    size = 64
    image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Ghost shape
    draw.ellipse([8, 8, 56, 48], fill=(0, 212, 255))
    draw.rectangle([8, 28, 56, 56], fill=(0, 212, 255))
    # Wavy bottom
    draw.ellipse([8, 46, 24, 62], fill=(10, 14, 26))
    draw.ellipse([24, 46, 40, 62], fill=(0, 212, 255))
    draw.ellipse([40, 46, 56, 62], fill=(10, 14, 26))
    # Eyes
    draw.ellipse([18, 20, 28, 34], fill=(10, 14, 26))
    draw.ellipse([36, 20, 46, 34], fill=(10, 14, 26))
    return image

def create_tray_menu():
    """Create system tray menu."""
    return pystray.Menu(
        pystray.MenuItem("Ghost Scribe", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Window", lambda: show_window()),
        pystray.MenuItem(f"Hotkey: {HOTKEY}", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("About", show_about),
        pystray.MenuItem("Exit", exit_app)
    )

def show_about():
    """Show about dialog."""
    def _show():
        messagebox.showinfo(
            "About Ghost Scribe",
            f"{APP_NAME} v{VERSION}\n\n"
            "Local AI Writing Assistant\n"
            "Powered by Intel NPU + OpenVINO\n\n"
            f"Hotkey: {HOTKEY}\n"
            f"Device: {DEVICE}\n\n"
            "© 2026 - Runs 100% Offline"
        )
    root.after(0, _show)

def exit_app():
    """Clean exit."""
    global icon
    print("[EXIT] Shutting down Ghost Scribe...")
    if icon:
        icon.stop()
    if root:
        root.quit()
    os._exit(0)

# --- 6. ENTRY POINT ---
def main():
    global root, icon
    
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║           👻 GHOST SCRIBE v{VERSION}               ║
    ║          Local AI Writing Assistant              ║
    ║           Powered by Intel NPU                   ║
    ╠══════════════════════════════════════════════════╣
    ║  Hotkey: {HOTKEY:<37}  ║
    ║  Model:  {str(MODEL_PATH)[:37]:<37}  ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Start model loading in background
    print("[INIT] Starting model load...")
    threading.Thread(target=load_model, daemon=True).start()
    
    # Register global hotkey
    print(f"[INIT] Registering hotkey: {HOTKEY}")
    keyboard.add_hotkey(HOTKEY, on_hotkey, suppress=True)
    
    # Create hidden root window
    root = tk.Tk()
    root.withdraw()
    root.title(APP_NAME)
    
    # Create system tray
    icon_image = create_tray_icon()
    icon = pystray.Icon(
        APP_NAME,
        icon_image,
        f"{APP_NAME} - Press {HOTKEY}",
        create_tray_menu()
    )
    
    # Run tray in separate thread
    threading.Thread(target=icon.run, daemon=True).start()
    
    print(f"\n✅ Ghost Scribe is running in the system tray!")
    print(f"   Press {HOTKEY} to process clipboard content.")
    print(f"   Right-click the tray icon for options.\n")
    
    # Start Tkinter loop
    root.mainloop()

if __name__ == "__main__":
    main()
