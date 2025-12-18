from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import subprocess, os, json, uuid, sys

app = FastAPI(title="CourtDominion Backend (Hybrid)")

# Get the directory where this file lives (for finding legacy scripts)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/data/outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class ProjReq(BaseModel):
    players: list = []
    date: Optional[str] = None

@app.get("/health")
def health():
    return {"status":"ok","timestamp":datetime.utcnow().isoformat()}

@app.post("/v1/run_projections")
def run_projections(req: ProjReq):
    # Try to find simple_projections.py first (doesn't need database)
    # Fallback to dbb2_main.py if simple version not found
    
    entry = None
    
    # Look for simple_projections.py first
    simple_script = os.path.join(SCRIPT_DIR, "legacy", "simple_projections.py")
    if os.path.exists(simple_script):
        entry = simple_script
    else:
        # Fallback to dbb2_main.py
        for root, dirs, files in os.walk(os.path.join(SCRIPT_DIR, "legacy")):
            if "dbb2_main.py" in files:
                entry = os.path.join(root, "dbb2_main.py")
                break
    
    if not entry:
        raise HTTPException(status_code=500, detail="No projection runner found (looking for simple_projections.py or dbb2_main.py)")
    
    out_file = os.path.join(OUTPUT_DIR, f"projections_{uuid.uuid4().hex}.json")
    env = os.environ.copy()
    env["PROJECTIONS_OUTPUT"] = out_file
    if req.date:
        env["PROJECTIONS_DATE"] = req.date
    if req.players:
        players_path = os.path.join(OUTPUT_DIR, f"players_{uuid.uuid4().hex}.json")
        with open(players_path, "w") as pf:
            json.dump(req.players, pf)
        env["PROJECTIONS_PLAYERS_FILE"] = players_path
    try:
        proc = subprocess.run([sys.executable, entry], env=env, capture_output=True, text=True, timeout=600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail={"rc":proc.returncode, "stdout":proc.stdout, "stderr":proc.stderr})
    if os.path.exists(out_file):
        try:
            with open(out_file) as f:
                data = json.load(f)
        except Exception:
            data = {"note":"output not json-parsable"}
        return {"status":"ok","output_file":out_file,"preview":data}
    # fallback
    fallback = os.path.join(os.path.dirname(entry), "dbb2_output.json")
    if os.path.exists(fallback):
        try:
            with open(fallback) as f:
                data = json.load(f)
        except Exception:
            data = {"note":"fallback not json-parsable"}
        return {"status":"ok","output_file":fallback,"preview":data}
    raise HTTPException(status_code=500, detail="No output produced")
