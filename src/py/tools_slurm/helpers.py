"""
Common functions for tools-slurm scripts.
"""


from collections import defaultdict
from numbers import Integral
import subprocess
from typing import Dict, List, Optional
import yaml


def get_slurm_entity(entity: str, conditions: Optional[List[str]] = None
                     ) -> List[Dict[str, str]]:
    """
    Returns the parsed output of `scontrol show <entity>`.

    @param entity The slurm entity to return
    @param conditions Only return results that contain all condition
                      substrings, e.g. `["Licenses=W62F3", "JobState=RUNNING"]`
                      returns all running jobs for setup W62F3.
    """
    if conditions is None:
        conditions = []
    result = subprocess.run(f"scontrol show -oa {entity}", shell=True,
                            check=True, capture_output=True, text=True)
    return list(
        dict(x.split('=', 1) for x in line.split() if '=' in x)
        for line in result.stdout.splitlines()
        if all(c in line for c in conditions))


def get_licenses(slurm_entity: List[Dict[str, str]]) -> List[str]:
    """
    Get a list of mentioned licenses from parsed slurm entity. Removes any
    extension separated by a colon at the end.
    """
    out = []
    for entry in slurm_entity:
        out.extend(map(lambda x: x.split(":")[0],
                       entry.get("Licenses", "").split(",")))
    return out


def get_chip_licenses(chip_revision: Integral) -> List[str]:
    """
    Returns license strings of all chips of given revision (defaults to the
    latest chip revision).
    """

    with open("/wang/data/bss-hwdb/db.yaml", mode="r",
              encoding="utf-8") as db_file:
        database = db_file.read().split('---')
    cube_entries = map(yaml.safe_load,
                       filter(lambda x: 'hxcube_id' in x, database))
    cube_chips = defaultdict(list)
    for cube_entry in cube_entries:
        for fpga in cube_entry["fpgas"]:
            try:
                revision = fpga["chip_revision"]
            except KeyError:
                # fpga has no chip
                continue
            wafer_id = cube_entry['hxcube_id'] + 60
            cube_chips[revision].append(f"W{wafer_id}F{fpga['fpga']}")
    return cube_chips[chip_revision]


def get_idle_chips(chip_revision: Optional[Integral] = None) -> List[str]:
    """
    Returns licenses of all idle chips.

    @param chip_revision The desired chip revision (defaults to latest)
    """
    job_licenses = get_licenses(
        get_slurm_entity("jobs", ["Licenses=W", "JobState=RUNNING"]))
    chips = get_chip_licenses(chip_revision)

    available_chips = filter(
        lambda license: license not in job_licenses,
        chips
    )
    return list(available_chips)
