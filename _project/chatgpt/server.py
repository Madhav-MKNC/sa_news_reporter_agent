# server.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import pathlib, glob, json

app = FastAPI()
BASE = pathlib.Path(".")
CANDS = BASE/"data/candidates"

app.mount("/ui", StaticFiles(directory="ui"), name="ui")

@app.get("/api/candidates")
def list_cands():
    files = sorted(glob.glob(str(CANDS/"*.json")), reverse=True)
    out = []
    for f in files:
        j = json.load(open(f, encoding="utf-8"))
        out.append({
            "id": j["id"],
            "headline": j["headline"],
            "variants": j["tweet_variants"],
            "created_at": j["created_at"]
        })
    return out

# run with:
# python -m uvicorn server:app --port 9000 --reload
