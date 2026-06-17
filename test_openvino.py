"""Test if OpenVINO works at all"""
import sys
print(f"Python: {sys.version}")

try:
    import openvino_genai
    print(f"openvino_genai imported OK")
    
    # Try to load model with CPU
    model_path = "tinyllama-model"
    print(f"Loading model from: {model_path}")
    
    pipe = openvino_genai.LLMPipeline(model_path, "CPU")
    print("Pipeline created!")
    
    # Test generation
    result = pipe.generate("Hello", max_new_tokens=5)
    print(f"Generated: {result}")
    print("\n*** OpenVINO is working! ***")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

input("\nPress Enter to exit...")
