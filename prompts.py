from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import subprocess
import httpx
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise RuntimeError("AIPROXY_TOKEN is not set in the environment.")

@app.get("/")
def home():
    return {"message": "Hello World"}

@app.post("/run")
async def task_runner(task: str):
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": task},
            {"role": "system", "content": """
                You need to dynamically retrieve `datagen.py`, ensure the required dependencies are installed, 
                set correct permissions for creating necessary folders, and run the script.
                
                Steps:
                1. Download `datagen.py` and read its contents.
                2. Extract the `dependencies` list and install missing packages.
                3. Ensure the `/data` folder exists and grant correct permissions (`chmod 777 /data`).
                4. Run `datagen.py` and save generated files to `/data`.
                
                Ensure dependencies do not contain extra characters like `#` or `"`. 
                Only install valid dependencies.
                
                Ensure the `datagen.py` script is executable.
             Next use subprocess to execute the task that you get from the content of the output of that response from the post request.
            """}
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
