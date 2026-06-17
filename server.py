import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openvino_genai
from pathlib import Path

app = FastAPI(title="NPU Local Inference API")

# --- GLOBAL MODEL STATE ---
MODEL_PATH = Path("./tinyllama-model")
DEVICE = "NPU"
pipe = None

class Query(BaseModel):
    prompt: str
    max_tokens: int = 128

@app.on_event("startup")
async def load_model():
    global pipe
    print(f"Loading model to {DEVICE}...")
    try:
        # Load once at startup
        pipe = openvino_genai.LLMPipeline(str(MODEL_PATH), DEVICE)
        
        # Warmup pass to compile graph
        print("Warming up NPU...")
        config = openvino_genai.GenerationConfig()
        config.max_new_tokens = 10
        pipe.generate("Warmup", config)
        print("Model Loaded & Ready.")
    except Exception as e:
        print(f"FATAL: Could not load model: {e}")

@app.post("/generate")
async def generate_text(query: Query):
    if not pipe:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    
    # Configure generation
    config = openvino_genai.GenerationConfig()
    config.max_new_tokens = query.max_tokens
    config.do_sample = False # Deterministic/Fast
    
    # Run Inference
    response_text = pipe.generate(query.prompt, config)
    
    duration = time.time() - start
    
    return {
        "response": response_text,
        "metrics": {
            "device": DEVICE,
            "duration_seconds": round(duration, 2),
            "estimated_tps": round((len(response_text.split())*1.3) / duration, 2)
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Workers=1 is critical because NPU cannot handle multi-process access easily yet
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)