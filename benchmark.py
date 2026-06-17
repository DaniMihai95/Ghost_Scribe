import time
import platform
from llama_cpp import Llama

# --- CONFIGURATION ---
# Use the Q8 path for BOTH laptops as you requested
MODEL_PATH = "./Meta-Llama-3-8B-Instruct-Q8_0.gguf" 

# --- SYSTEM INFO ---
print(f"Running on: {platform.node()} ({platform.system()} {platform.release()})")
print(f"Model:      {MODEL_PATH}")

# --- LOAD MODEL ---
print("\n[1/3] Loading Model... (this maps the file to RAM/VRAM)")
t0 = time.time()

# n_gpu_layers=-1 means "Put as much as possible on GPU"
# On Laptop A (RTX 4080): This puts 100% of layers on VRAM.
# On Laptop B (Intel): This gracefully falls back to CPU (0 layers on GPU) 
# unless you compiled with Vulkan support.
llm = Llama(
    model_path=MODEL_PATH,
    n_gpu_layers=-1, 
    n_ctx=4096,
    verbose=False
)
print(f"Model Loaded in {time.time() - t0:.2f} seconds.")

# --- THE PROMPT ---
prompt = "Explain the detailed differences between Zero-Trust and Traditional VPN architectures."
formatted_prompt = f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"

# --- WARMUP ---
# We run a tiny generation first to allocate buffers and wake up the hardware
print("[2/3] Warming up hardware...")
llm(formatted_prompt, max_tokens=5, echo=False)

# --- BENCHMARK ---
print("[3/3] Running Benchmark (Generating 200 tokens)...")
start_time = time.perf_counter()

output = llm(
    formatted_prompt, 
    max_tokens=200, 
    echo=False # Don't print the text yet, just measure speed
)

end_time = time.perf_counter()

# --- METRICS ---
stats = output['usage']
tokens_generated = stats['completion_tokens']
duration = end_time - start_time
tps = tokens_generated / duration

print("\n" + "="*40)
print(f"BENCHMARK RESULTS: {platform.node()}")
print("="*40)
print(f"Speed:            {tps:.2f} tokens/sec")
print(f"Total Time:       {duration:.2f} seconds")
print(f"Tokens Generated: {tokens_generated}")
print("="*40)

# Optional: Print the output to prove it worked
# print("\nGenerated Text:\n", output['choices'][0]['text'])
