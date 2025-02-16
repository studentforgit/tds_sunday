# /// <script>
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi",
#     "uvicorn",
#     "requests",]
#/// </script>

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")

tools = [
    {
        "type": "function",
        "function": {
            "name": "script_runner",
            "description": "Run a Python script from a URL with arguments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_url": {"type": "string", "description": "URL of the script"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the script"},
                },
                "required": ["script_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command securely.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                },
                "required": ["command"],
            },
        },
    }
]

@app.get("/")
def home():
    return {"message": "Hello World"}

@app.post("/run")
def task_runner(task: str):
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
                You are an AI agent that can perform the following tasks. Use the appropriate tool for each task.

                - **A1:** Install `uv` (if required) and run `datagen.py` from 
                         [this URL](https://raw.githubusercontent.com/sanand0/tools-in-data-science-public/tds-2025-01/project-1/datagen.py) 
                         with `${21f3001993@ds.study.iitm.ac.in}` as the argument. → Use `script_runner`.
                - **A2:** Format `/data/format.md` using `prettier@3.4.2`, updating it in-place. → Use `execute_command` with 
                         `command="npx prettier@3.4.2 --write /data/format.md"`.
                - **A3:** Count the number of Wednesdays in a date file (/data/dates.txt) and write the count to /data/dates-wednesdays.txt.`.
                - **A4:** Sort contacts in `/data/contacts.json` by `last_name`, then `first_name`, and save to `/data/contacts-sorted.json`.
                - **A5:** Extract the first line of the 10 most recent `.log` files in `/data/logs/` and write them (most recent first) to `/data/logs-recent.txt`.
                - **A6:** Extract the first **H1 header** from each Markdown (`.md`) file in `/data/docs/` and create an index at `/data/docs/index.json`.
                - **A7:** Extract the sender’s email from `/data/email.txt` and write it to `/data/email-sender.txt`.
                - **A8:** Extract the credit card number from `/data/credit-card.png` and write it (without spaces) to `/data/credit-card.txt`.
                - **A9:** Find the most similar pair of comments in `/data/comments.txt` using embeddings and save them to `/data/comments-similar.txt`.
                - **A10:** Compute the total sales for **Gold** ticket types from `/data/ticket-sales.db` and write the number to `/data/ticket-sales-gold.txt`.
                - **B1:** Convert `/data/input.csv` to JSON and save as `/data/output.json`.
                - **B2:** Rename all `.txt` files in `/data/rename/` by appending `_backup` before the extension.
                - **B3:** Extract all unique email addresses from `/data/emails.log` and save them to `/data/emails-unique.txt`.
                - **B4:** Find the top 10 most common words in `/data/words.txt` and save them to `/data/words-top10.txt`.
                - **B5:** Replace all instances of `ERROR` with `WARNING` in `/data/logs/errors.log`, updating it in-place.
                - **B6:** Resize all `.png` images in `/data/images/` to 256x256 and save them in `/data/images-resized/`.
                - **B7:** Extract the text from `/data/document.pdf` and save it to `/data/document.txt`.
                - **B8:** Find the largest file in `/data/files/` and write its name to `/data/largest-file.txt`.
                - **B9:** Count the number of lines in each file in `/data/multifile/` and save the results to `/data/line-counts.txt`.
                - **B10:** Extract and save metadata from `/data/music.mp3` to `/data/music-metadata.json`
            """}
        ],
        "tools": tools,
        "tool_choice": "auto"
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def execute_command(command: str):
    """ Safely executes a shell command """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)