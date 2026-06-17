"""Debug script to test OpenVINO in bundled environment"""
import os
import sys
from pathlib import Path

print("=" * 60)
print("OpenVINO Bundled Environment Debug")
print("=" * 60)

# Check if we're frozen
frozen = getattr(sys, 'frozen', False)
print(f"Frozen: {frozen}")

if frozen:
    if hasattr(sys, '_MEIPASS'):
        base = Path(sys._MEIPASS)
    else:
        base = Path(os.path.dirname(sys.executable)) / "_internal"
    print(f"Base dir: {base}")
    
    ov_libs = base / "openvino" / "libs"
    print(f"OpenVINO libs: {ov_libs}")
    print(f"Exists: {ov_libs.exists()}")
    
    if ov_libs.exists():
        print(f"Contents:")
        for f in ov_libs.iterdir():
            print(f"  - {f.name}")

print(f"\nOPENVINO_LIB_PATH: {os.environ.get('OPENVINO_LIB_PATH', 'NOT SET')}")
print(f"PATH (first 500 chars): {os.environ.get('PATH', '')[:500]}")

print("\n--- Attempting to import openvino_genai ---")
try:
    import openvino_genai
    print("Import successful!")
    
    print("\n--- Attempting to create pipeline ---")
    # Find model path
    if frozen:
        exe_dir = Path(os.path.dirname(sys.executable))
        model_path = exe_dir / "tinyllama-model"
    else:
        model_path = Path("tinyllama-model")
    
    print(f"Model path: {model_path}")
    print(f"Model exists: {model_path.exists()}")
    
    pipe = openvino_genai.LLMPipeline(str(model_path), "CPU")
    print("Pipeline created!")
    
    result = pipe.generate("Hello", max_new_tokens=5)
    print(f"Generated: {result}")
    print("\n*** SUCCESS! ***")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

input("\nPress Enter to exit...")
