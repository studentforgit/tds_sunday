#/// <script>
# requires-python = ">=3.10"
# dependencies = [
#     "fastapi",
#     "uvicorn",
#     "requests",
#     "openai",
#     "httpx",
#     "json",
#     "re",
#     "os",
# ]
# ///

from fastapi import FastAPI, Response, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests, json, os, openai
from openai import OpenAI


app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def root():
    return {'message': 'Hello World from docker container'}

@app.post("/run")
def run_task(task: str = Query(..., description="Task description")):
    try:
        #task_code = parse_task(task)
        task_classification = classify_task(task)
        result = execute_task(task_classification, task)
        #return {"status": "success", "result": result}
        return result
    except ValueError as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

BASE_DIR = os.getcwd()  # Get the current working directory

@app.get("/read")
def read_file(path: str = Query(..., description="Relative file path")):
    
    if is_valid_path(path):
        # Convert to a relative path (prevent accessing files outside BASE_DIR)
        print(f"Checking file: {path}, {BASE_DIR}, {os.path.join(BASE_DIR, path)}")
        safe_path = os.path.abspath(os.path.join(BASE_DIR, path))
        safe_path = f'.{safe_path}'
        
        if not os.path.exists(safe_path):
            raise HTTPException(status_code=404, detail=f"File not found: {safe_path}")
        try:
            with open(safe_path, "r", encoding="utf-8") as file:
                content = file.read()
            return StreamingResponse(content, media_type="text/plain")
        except Exception as e:
            file_stream = open(safe_path, "rb")  # Open in binary mode
            return StreamingResponse(file_stream, media_type="application/octet-stream")
        
import os, json, re



# Define the predefined task descriptions
function_definitions_llm = [
    {
        "name": "A1",
        "description": "Run a Python script from a given git URL, passing an email as the argument.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"https://raw.githubusercontent.com*\.py"},
                "targetfile": {"type": "string", "pattern": r".*/(.*\.py)"},
                "email": {"type": "string", "pattern": r"[\w\.-]+@[\w\.-]+\.\w+"}
            },
            "required": ["filename", "targetfile", "email"]
        }
    },
    {
        "name": "A2",
        "description": "Format a markdown file using Prettier.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.md)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.md)"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A3",
        "description": "Count the number of occurrences of a specific weekday in a date file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.txt)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.txt)"},
                "weekday": {"type": "integer", "description": "weekday as per python datetime module (0=Monday, 1=Tuesday, ..., 6=Sunday)"}
            },
            "required": ["filename", "targetfile", "weekday"]
        }
    },
    {
        "name": "A4",
        "description": "Sort data in a JSON file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.json)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.json)"},
                "sorting_fields": {"type": "array", "items": {"type": "string", "pattern": r"\w+"}}
            },
            "required": ["filename", "targetfile", "sorting_fields"]
        }
    },
    {
        "name": "A5",
        "description": "Extract the 'x' line(s) from 'n' log files.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/\w+"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.json)"},
                "num_files": {"type": "integer", "pattern": r"\d+"},
                "num_lines": {"type": "integer", "pattern": r"\d+", "default": 1},
                "order": {"type": "string", "pattern": r"(asc|desc)", "default": "desc"}
            },
            "required": ["filename", "targetfile", "num_files"]
        }
    },
    {
        "name": "A6",
        "description": "Extract specific elements from Markdown (.md) files from directory and generate an index mapping filenames to extracted content.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"^/data/\w+", "description": "Markdown directory path."},
                "targetfile": {"type": "string", "pattern": r"^/data/(.*\.json)"},
                "extract": {"type": "string", "pattern": r"(h1|h2|h3|h4|h5|h6)", "default": "h1"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A7",
        "description": "Extract the sender's email from an email file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.txt)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.txt)"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A8",
        "description": "Extract a credit card number from an image.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.(png|jpg|jpeg))"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.txt)"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A9",
        "description": "Find the most similar pair of comments.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.txt)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.txt)"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "A10",
        "description": "Compute total sales for a specific ticket type in an ^SQLite database.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/data/(.*\.db)"},
                "targetfile": {"type": "string", "pattern": r"/data/(.*\.txt)"},
                "expression": {"type": "string", "description": "complete SQL query."}
            },
            "required": ["filename", "targetfile", "expression"]
        }
    },
    {
        "name": "B3",
        "description": "Fetch data from an API and save it",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": "https://[^\\s]+/[^\\s]+(\\.json|/api/|/v[0-9]+/)"},
                "targetfile": {"type": "string", "pattern": r"/[\w\-/]+(?:\.\w+)?"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "B4",
        "description": "Clone a Git repository, change file and make a commit.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"https?://[\w./-]+\.git"},
                "targetfile": {"type": "string", "pattern": r"/[\w\-/]+\.\w+", "description": "File to change in the repository."},
            },
            "required": ["filename"]
        }
    },
    {
        "name": "B5",
        "description": "Run a SQL query on a SQLite or DuckDB database and write the result to a target file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/[\w\-/]+\.db|/[\w\-/]+\.duckdb"},
                "targetfile": {"type": "string", "pattern": r"/[\w\-/]+\.\w+"},
                "query": {"type": "string", "pattern": r".*"}
            },
            "required": ["filename", "targetfile", "query"]
        }
    },
    {
        "name": "B6",
        "description": "Extract data/scrape data from a website",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": { "type": "string", "pattern": "https?://[^\\s]+"},
                "targetfile": { "type": "string", "pattern": "^/data/[\\w\\-/]+\\.(json|csv|txt)", "description": "Path where the scraped data should be saved"},
                "selectors": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "pattern": ".*",
                        "description": "specific CSS selectors or XPath expressions for extracting specific elements"
                    },
                    "description": "List of selectors to extract specific elements from the page"
                },
                "paginate": {"type": "boolean", "default": False}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "B7",
        "description": "Compress or resize an image and save it to output path.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"^/[\w\-/]+\.(jpg|jpeg|png|webp)"},
                "targetfile": {"type": "string", "pattern": r"^/[\w\-/]+\.(jpg|jpeg|png|webp)"},
                "resize": 
                    {"type": "object", "properties": 
                        {"width": {"type": "integer", "pattern": r"\d+"}, "height": {"type": "integer", "pattern": r"\d+"}}
                    },
                "quality": {"type": "integer", "pattern": r"\d+", "default": 100}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "B8",
        "description": "Transcribe audio from an MP3 file",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"^/[\w\-/]+\.(mp3|wav)", "description": "Path to the audio file"},
                "targetfile": {"type": "string", "pattern": r"^/[\w\-/]+\.txt", "description": "Path to save the transcription"}
            },
            "required": ["filename"]
        }
    },
    {
        "name": "B9",
        "description": "Convert a Markdown (.md) file to an HTML (.html) file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/[\w\-/]+\.md"},
                "targetfile": {"type": "string", "pattern": r"/[\w\-/]+\.html"}
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "B10",
        "description": "API endpoint that filters a CSV file and returns JSON data",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "pattern": r"/[\w\-/]+\.csv"},
                "targetfile": {"type": "string", "pattern": r"/[\w\-/]+\.json"},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "pattern": r"\w+"},
                            "value": {"type": "string", "pattern": r"\w+"}
                        },
                        "required": ["column", "value"]
                    }
                }
            },
            "required": ["filename", "targetfile"]
        }
    },
    {
        "name": "FALLBACK",
        "description": "Handle general queries or automation tasks that do not match predefined tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "return the actions steps to perform the task"}
            },
            "required": ["query"]
        }
    }]


def classify_task(task_description):
    json_data = {
                    "model": "gpt-4o-mini", 
                    "messages": [
                                    {"role": "system", "content": "You are a function classifier that extracts structured parameters from queries."},
                                    {"role": "user", "content": task_description}
                                ],
                    "tools": [
                                {
                                    "type": "function",
                                    "function": function
                                } for function in function_definitions_llm
                            ],
                    "tool_choice": "auto"
                }
    
    try:
        result = get_tool_completions(json_data)
        return result
    except json.JSONDecodeError:
        return {"code": "UNKNOWN", "filename": None, "targetfile": None}
import os, httpx, json
#openai_api_base = os.getenv("OPENAI_API_BASE", "https://aiproxy.sanand.workers.dev/openai/v1")
#openai_api_base  = "https://api.openai.com/v1" # for testing
openai_api_base = "https://aiproxy.sanand.workers.dev/openai/v1"

openai_api_key = os.getenv("AIPROXY_TOKEN", "no-key")

headers = {
    "Authorization": f"Bearer {openai_api_key}",
    "Content-Type": "application/json",
}

def get_completions(messages):
    #print(messages)
    #print(f"openai_api_base: {openai_api_base}")
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{openai_api_base}/chat/completions",
            headers=headers,
            json=
                {"model": "gpt-4o-mini", 
                 "messages": messages
                },
        )
    return response.json()["choices"][0]["message"]["content"]

def get_tool_completions(json_data):
    #print(messages)
    #print(f"openai_api_base: {openai_api_base}")
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{openai_api_base}/chat/completions",
            headers=headers,
            json= json_data
        )
    #print(response.json())
    return response.json()["choices"][0]["message"]["tool_calls"][0]["function"]

def is_valid_path(filepath, base_dir="/data"):
    """Check if a file is inside the /data directory."""
    abs_filepath = os.path.abspath(filepath)
    abs_base_dir = os.path.abspath(base_dir)
    if not abs_filepath.startswith(abs_base_dir):
        raise HTTPException(status_code=403, detail=f"Access to this file: {filepath} is forbidden")
    else:
        return True

def execute_task(task_classification, task_query: str) -> str:
    """ Execute the task based on the task code. """
    
    #print(task_classification)
    #task_classification = json.loads(task_classification)
    #print(task_classification)
    
    task_code = task_classification["name"]
    arguments = json.loads(task_classification["arguments"])
    print(arguments)
    # if "filename" in arguments:
    #     arguments["filename"] = f"./{arguments["filename"]}"
    # if "targetfile" in arguments:
    #     arguments["targetfile"] = f"./{arguments["targetfile"]}"
        
    # print(f"Task code: {task_code} | Filename: {arguments.get("filename")} | Targetfile: {arguments.get("targetfile")}")
    
    if task_code == "A1":
        arguments = json.loads(task_classification["arguments"])
        def execute_task(filename: str, targetfile: str, email: str) -> str:
            install_uv()
            url = filename
            script_path = targetfile
            user_email = email
            download_script(url, script_path)
            clean_output_directory(output_path)
            run_script(script_path, user_email, output_path)
            return f"Data generation at {output_path} from { targetfile } complete."

        
        def install_uv():
            """Check if `uv` is installed, and install it if necessary."""
            print("🚀 Checking if uv is installed...")
            try:
                subprocess.run(["uv", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("✅ uv is already installed.")
            except subprocess.CalledProcessError:
                print("🚀 Installing uv...")
                subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
                print("✅ uv installed successfully.")
            except FileNotFoundError:
                print("🚀 Installing uv...")
                subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
                print("✅ uv installed successfully.")

        def download_script(url, script_path):
            """Download a script from a given URL."""
            if os.path.exists(script_path):
                os.remove(script_path)
            print(f"⬇️ Downloading {script_path}...")
            try:
                urllib.request.urlretrieve(url, script_path)
                print("✅ Download complete.")
            except Exception as e:
                print(f"❌ Error downloading script: {e}")

        def clean_output_directory(output_path):
            """Remove the specified output directory."""
            print(f"🚀 Cleaning the output directory: {output_path}")
            subprocess.run(["rm", "-rf", output_path], check=True)

        def run_script(script_path, user_email, output_path):
            """Run the downloaded script with the given email and output path."""
            print(f"🚀 Running {script_path} with arguments: Email='{user_email}', Path='{output_path}'")
            subprocess.run([sys.executable, script_path, user_email, "--root", output_path], check=True)
            print("✅ Data generation complete.")
            # elif task_code == "A2":
    #     
    # else:
    #     raise ValueError("Unknown task code")
    


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
