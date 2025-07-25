import os
import time
import tiktoken
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not GROQ_API_KEY or not OPENROUTER_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY or OPENROUTER_API_KEY")

app = FastAPI()

# Serve frontend from /static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in prod
    allow_methods=["*"],
    allow_headers=["*"]
)

class PromptInput(BaseModel):
    prompt: str

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

@app.post("/compare")
async def compare_models(prompt_input: PromptInput):
    prompt = prompt_input.prompt
    emissions_per_token = 0.0002

    async with httpx.AsyncClient() as client:
        try:
            # GROQ
            groq_start = time.time()
            groq_resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            groq_json = groq_resp.json()
            print("GROQ JSON:", groq_json)
            groq_reply = groq_json["choices"][0]["message"]["content"]
            groq_tokens = count_tokens(groq_reply, "llama3-8b-8192")
            groq_emissions = round(groq_tokens * emissions_per_token, 4)
            groq_latency = int((time.time() - groq_start) * 1000)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"GROQ failed: {str(e)}"})

        try:
            # DEEPSEEK
            deepseek_start = time.time()
            deepseek_resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Prompare"
                },
                json={
                    "model": "deepseek/deepseek-r1",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            deepseek_json = deepseek_resp.json()
            print("DEEPSEEK JSON:", deepseek_json)
            deepseek_reply = deepseek_json["choices"][0]["message"]["content"]
            deepseek_tokens = count_tokens(deepseek_reply, "gpt-3.5-turbo")
            deepseek_emissions = round(deepseek_tokens * emissions_per_token, 4)
            deepseek_latency = int((time.time() - deepseek_start) * 1000)
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"DeepSeek failed: {str(e)}"})

    return {
        "groq": {
            "output": groq_reply,
            "tokens": groq_tokens,
            "emissions": groq_emissions,
            "latency": groq_latency
        },
        "deepseek": {
            "output": deepseek_reply,
            "tokens": deepseek_tokens,
            "emissions": deepseek_emissions,
            "latency": deepseek_latency
        }
    }
