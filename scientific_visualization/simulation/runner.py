from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
from typing import Sequence

@dataclass
class SimulationRun:
    command: Sequence[str]
    working_directory: str | None = None
    output: str = ""
    return_code: int | None = None

class SimulationRunner:
    """Safe handoff point from active learning recommendations to a simulation code.

    Commands are explicit argument lists rather than shell strings. This avoids shell
    interpolation and allows Simulation or another simulator to be integrated later.
    """
    def run(self, command: Sequence[str], working_directory: str | Path | None = None, timeout: float | None = None) -> SimulationRun:
        wd = str(working_directory) if working_directory is not None else None
        proc = subprocess.run(list(command), cwd=wd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return SimulationRun(command=list(command), working_directory=wd, output=proc.stdout, return_code=proc.returncode)
