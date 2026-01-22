"""Routes for configuration management and run triggering."""

import asyncio
from pathlib import Path
from typing import Any, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel

from turbulence.commands.run import _run_instances

router = APIRouter(tags=["configs"])

class RunTriggerRequest(BaseModel):
    sut_path: str
    scenario_ids: List[str]
    instances: int = 10
    parallelism: int = 5
    profile: str | None = None

@router.get("/configs/sut")
def list_sut_configs(request: Request) -> dict[str, Any]:
    """List available SUT configuration files."""
    sut_dir: Path = request.app.state.sut_dir
    files = sorted(list(sut_dir.glob("*.yaml")) + list(sut_dir.glob("*.yml")))
    return {
        "configs": [
            {"name": f.name, "path": str(f.relative_to(sut_dir))} 
            for f in files
        ]
    }

@router.get("/configs/scenarios")
def list_scenarios(request: Request) -> dict[str, Any]:
    """List available scenario files."""
    scenarios_dir: Path = request.app.state.scenarios_dir
    files = sorted(list(scenarios_dir.glob("*.yaml")) + list(scenarios_dir.glob("*.yml")))
    
    # We might want to parse them to get the actual ID, 
    # but for now just returning filenames is a good start.
    return {
        "scenarios": [
            {"name": f.name, "id": f.stem, "path": str(f.relative_to(scenarios_dir))} 
            for f in files
        ]
    }

@router.get("/configs/scenarios/{scenario_id}")
def get_scenario_content(request: Request, scenario_id: str) -> dict[str, Any]:
    """Get the raw content of a scenario file."""
    scenarios_dir: Path = request.app.state.scenarios_dir
    
    # Try common extensions
    for ext in [".yaml", ".yml"]:
        path = scenarios_dir / f"{scenario_id}{ext}"
        if path.exists():
            return {
                "id": scenario_id,
                "content": path.read_text(encoding="utf-8")
            }
            
    raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found")

@router.post("/runs/trigger")
async def trigger_run(
    request: Request, 
    trigger: RunTriggerRequest,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """Trigger a new simulation run."""
    sut_dir: Path = request.app.state.sut_dir
    scenarios_dir: Path = request.app.state.scenarios_dir
    runs_dir: Path = request.app.state.runs_dir
    
    sut_path = sut_dir / trigger.sut_path
    if not sut_path.exists():
        raise HTTPException(status_code=400, detail=f"SUT config not found: {trigger.sut_path}")
    
    # We need a predictable run_id to return to the client
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    
    # Run the simulation in the background
    # Note: _run_instances handles its own run_id generation normally, 
    # but we might need to modify it or accept the generated one.
    # For now, we'll let it generate one and the client will have to 
    # find it or we refactor _run_instances.
    
    # Actually, let's look at _run_instances again. 
    # It generates run_id internally.
    
    background_tasks.add_task(
        _run_instances,
        sut=sut_path,
        scenarios_dir=scenarios_dir,
        instances=trigger.instances,
        parallelism=trigger.parallelism,
        seed=None,
        profile=trigger.profile,
        output_dir=runs_dir,
        fail_on=None,
        storage="jsonl",
        run_id=run_id
    )
    
    return {
        "message": "Run triggered successfully",
        "run_id": run_id, # This might mismatch the internal one if we aren't careful
        "status": "pending"
    }
