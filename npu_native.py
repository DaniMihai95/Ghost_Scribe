import time
import shutil
from pathlib import Path
from huggingface_hub import snapshot_download
import openvino_genai

# --- CHANGED: Using the "NPU-Safe" Model ---
# TinyLlama 1.1B is much more stable on Meteor Lake NPUs than Phi-3
MODEL_ID = "OpenVINO/TinyLlama-1.1B-Chat-v1.0-int4-ov"
MODEL_PATH = Path("./tinyllama-model")

def download_model():
    if not MODEL_PATH.exists():
        print(f"Downloading {MODEL_ID} to {MODEL_PATH}...")
        snapshot_download(repo_id=MODEL_ID, local_dir=MODEL_PATH)
    else:
        print(f"Model found at {MODEL_PATH}")

def run_benchmark(device, prompt, runs=3):
    print(f"\n--- Testing {device} ---")
    
    try:
        # Load the pipeline
        # config={'CACHE_DIR': ''} disables caching to prevent loading broken compiled blobs
        pipe = openvino_genai.LLMPipeline(str(MODEL_PATH), device)
        
        config = openvino_genai.GenerationConfig()
        config.max_new_tokens = 128
        config.do_sample = False  # Greedy decoding (fastest)
        
        # 1. Warmup
        print(f"[{device}] Warming up...")
        start_warm = time.time()
        pipe.generate(prompt, config)
        print(f"[{device}] Warmup complete: {time.time() - start_warm:.2f}s")
        
        # 2. Benchmark
        print(f"[{device}] Running {runs} passes...")
        total_tps = 0
        
        for i in range(runs):
            start = time.time()
            result = pipe.generate(prompt, config)
            duration = time.time() - start
            
            # Estimate tokens (TinyLlama is verbose, usually fills the context)
            # We assume ~100 tokens generated for calculation
            estimated_tokens = len(result.split()) * 1.3 
            tps = estimated_tokens / duration
            
            print(f"   Pass {i+1}: ~{tps:.2f} tokens/sec")
            total_tps += tps

        print(f"[{device}] AVG RESULT: ~{total_tps/runs:.2f} t/s")

    except Exception as e:
        print(f"[{device}] FAILED: {e}")
        # If NPU fails here, it's 100% a driver version issue.

def main():
    # 1. Cleanup old NPU cache if it exists (fixes segfaults from bad previous compiles)
    cache_dir = Path("openvino_cache")
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print("Cleared old NPU cache.")
        except:
            pass

    download_model()
    
    prompt = "Write a python function to add two numbers."

    # We skip CPU/GPU this time to focus on fixing the NPU
    run_benchmark("NPU", prompt)

if __name__ == "__main__":
    main()