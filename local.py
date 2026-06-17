import time
import torch
import os
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer

# --- CONFIGURATION ---
MODEL_ID = "OpenVINO/Phi-3-mini-4k-instruct-int4-ov"
PROMPT = "Explain quantum computing in one sentence."

# STRICT LOCAL MODE (Set to True if you have downloaded it already)
LOCAL_ONLY = True 

def run_benchmark(device_name, model, tokenizer, runs=3):
    print(f"\n--- Testing {device_name} ---")
    
    # Tokenize input
    inputs = tokenizer(PROMPT, return_tensors="pt")
    input_length = inputs["input_ids"].shape[1]
    
    # 1. Warmup
    print(f"[{device_name}] Warming up (compiling kernels)...")
    start_warm = time.time()
    
    # For NPU with static shapes, we must ensure we don't exceed the reshaped size
    # We generate a small amount to trigger the compile
    try:
        model.generate(**inputs, max_new_tokens=10)
    except Exception as e:
        print(f"WARMUP ERROR: {e}")
        return 0.0
        
    print(f"[{device_name}] Warmup complete in {time.time() - start_warm:.2f}s")

    # 2. Speed Test
    total_tokens = 0
    total_duration = 0
    
    print(f"[{device_name}] Running {runs} generation passes...")
    for i in range(runs):
        start_gen = time.time()
        
        # Run generation
        output = model.generate(**inputs, max_new_tokens=64)
        end_gen = time.time()
        
        duration = end_gen - start_gen
        new_tokens = len(output[0]) - input_length
        
        tps = new_tokens / duration
        print(f"   Pass {i+1}: {tps:.2f} tokens/sec")
        
        total_tokens += new_tokens
        total_duration += duration

    avg_speed = total_tokens / total_duration
    print(f"[{device_name}] RESULT: {avg_speed:.2f} t/s")
    return avg_speed

def main():
    print(f"Loading Model: {MODEL_ID}")
    
    # Load tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=LOCAL_ONLY)
    except:
        # Fallback if local load fails
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=False)

    results = {}

    # --- DEVICE 1: CPU ---
    try:
        print("Loading Model to CPU...")
        model_cpu = OVModelForCausalLM.from_pretrained(MODEL_ID, device="CPU", local_files_only=LOCAL_ONLY)
        results["CPU"] = run_benchmark("CPU", model_cpu, tokenizer)
        del model_cpu
    except Exception as e:
        results["CPU"] = f"Error: {e}"

    # --- DEVICE 2: GPU ---
    try:
        print("\nLoading Model to GPU...")
        model_gpu = OVModelForCausalLM.from_pretrained(MODEL_ID, device="GPU", local_files_only=LOCAL_ONLY)
        results["GPU"] = run_benchmark("GPU", model_gpu, tokenizer)
        del model_gpu
    except Exception as e:
        results["GPU"] = f"Error: {e}"

    # --- DEVICE 3: NPU (FIXED) ---
    try:
        print("\nLoading Model to NPU...")
        ov_config = {"PERFORMANCE_HINT": "LATENCY"}
        
        # 1. Load model WITHOUT compiling immediately
        model_npu = OVModelForCausalLM.from_pretrained(
            MODEL_ID, 
            device="NPU", 
            ov_config=ov_config,
            local_files_only=LOCAL_ONLY,
            compile=False # <--- CRITICAL: Do not compile yet
        )
        
        # 2. FORCE STATIC SHAPE (The Fix)
        # We lock the NPU to: Batch Size=1, Sequence Length=128
        # This means prompt + answer cannot exceed 128 tokens total.
        # Increase '128' to '256' or '512' if you need longer answers, but it uses more RAM.
        print("[NPU] Reshaping to static (1, 128)...")
        model_npu.reshape(1, 128) 
        
        # 3. NOW Compile
        print("[NPU] Compiling graph (this takes ~30s)...")
        model_npu.compile()
        
        results["NPU"] = run_benchmark("NPU", model_npu, tokenizer)
        del model_npu
    except Exception as e:
        results["NPU"] = f"Error: {e}"

    # --- FINAL REPORT ---
    print("\n\n" + "="*30)
    print("FINAL RESULTS")
    print("="*30)
    for device, score in results.items():
        if isinstance(score, float):
            print(f"{device}: \t{score:.2f} t/s")
        else:
            print(f"{device}: \t{score}")

if __name__ == "__main__":
    main()