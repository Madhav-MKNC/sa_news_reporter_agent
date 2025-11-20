# writer.py
import json, glob, pathlib, requests

CANDS = pathlib.Path("data/candidates")

def llm_generate(summary):
    # TODO: Replace with groq/crewai SDK
    # Return list of 3 tweet variants
    return [
        {"text": f"Variant A: {summary[:120]}", "tags": ["#karnataka"], "score": 0.9},
        {"text": f"Variant B: {summary[:120]}", "tags": [], "score": 0.8},
        {"text": f"Variant C: {summary[:120]}", "tags": [], "score": 0.7},
    ]

def process():
    for f in glob.glob(str(CANDS/"*.json")):
        j = json.load(open(f, encoding="utf-8"))
        if j["tweet_variants"]:
            continue

        summary = j["cluster_summary"]
        j["tweet_variants"] = llm_generate(summary)
        json.dump(j, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("Updated:", j["id"])

if __name__ == "__main__":
    process()
