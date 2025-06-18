#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_snapshots.py
"""Check for oVirt VM snapshots"""

# License: GNU General Public License v2

import re
from typing import Dict, Any, List

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
)
from cmk_addons.plugins.ovirt.lib import parse_json_section

agent_section_ovirt_snapshots = AgentSection(
    name="ovirt_snapshots",
    parse_function=parse_json_section,
)

agent_section_ovirt_snapshots_engine = AgentSection(
    name="ovirt_snapshots_engine",
    parse_function=parse_json_section,
)

def discovery_ovirt_snapshots(section) -> DiscoveryResult:
    """Discover oVirt VM snapshots service"""
    if "snapshots" in section:
        yield Service()

def discovery_ovirt_snapshots_engine(section) -> DiscoveryResult:
    """Discover oVirt engine-wide snapshots service"""
    yield Service()

def check_ovirt_snapshots(params: Dict[str, Any], section) -> CheckResult:
    """Check oVirt VM snapshots"""
    snapshots = section.get("snapshots", [])
    
    if not snapshots:
        yield Result(state=State.OK, summary="No snapshots found")
        return
    
    # Get parameters
    state = params.get("state", 1)  # Default to WARNING
    allow_patterns = params.get("allow", [])
    ignore_patterns = params.get("ignore", [])
    
    # Compile patterns
    allow_regexes = [re.compile(pattern) for pattern in allow_patterns]
    ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
    
    snapshot_count = 0
    ignored_count = 0
    allowed_count = 0
    
    for snapshot in snapshots:
        description = snapshot.get("description", "")
        
        # Check if snapshot should be ignored
        if any(regex.search(description) for regex in ignore_regexes):
            # But check if it's in the allowed list which overrides ignore
            if any(regex.search(description) for regex in allow_regexes):
                allowed_count += 1
                snapshot_count += 1
            else:
                ignored_count += 1
        else:
            snapshot_count += 1
    
    if snapshot_count > 0:
        yield Result(
            state=State(state),
            summary=f"Found {snapshot_count} snapshots"
        )
    else:
        yield Result(state=State.OK, summary="No snapshots found")
    
    if ignored_count > 0:
        yield Result(
            state=State.OK,
            notice=f"Ignored {ignored_count} snapshots based on configured patterns"
        )
    
    if allowed_count > 0:
        yield Result(
            state=State.OK,
            notice=f"Allowed {allowed_count} snapshots that would otherwise be ignored"
        )

def check_ovirt_snapshots_engine(params: Dict[str, Any], section) -> CheckResult:
    """Check oVirt engine-wide snapshots"""
    vm_count = 0
    snapshot_count = 0
    vms_with_snapshots = []
    
    for vm in section:
        if "snapshots" in vm and vm["snapshots"]:
            vm_count += 1
            snapshot_count += len(vm["snapshots"])
            vms_with_snapshots.append(vm.get("name", "unknown"))
    
    # Get parameters
    state = params.get("state", 1)  # Default to WARNING
    
    if snapshot_count > 0:
        yield Result(
            state=State(state),
            summary=f"Found {snapshot_count} snapshots across {vm_count} VMs"
        )
        
        # List VMs with snapshots as details
        if vms_with_snapshots:
            yield Result(
                state=State.OK,
                notice=f"VMs with snapshots: {', '.join(vms_with_snapshots)}"
            )
    else:
        yield Result(state=State.OK, summary="No snapshots found")

check_plugin_ovirt_snapshots = CheckPlugin(
    name="ovirt_snapshots",
    service_name="oVirt VM Snapshots",
    discovery_function=discovery_ovirt_snapshots,
    check_function=check_ovirt_snapshots,
    check_default_parameters={
        "state": 1,  # WARNING
        "allow": [],
        "ignore": [],
    },
    check_ruleset_name="ovirt_snapshots",
)

check_plugin_ovirt_snapshots_engine = CheckPlugin(
    name="ovirt_snapshots_engine",
    service_name="oVirt Engine Snapshots",
    discovery_function=discovery_ovirt_snapshots_engine,
    check_function=check_ovirt_snapshots_engine,
    check_default_parameters={
        "state": 1,  # WARNING
    },
    check_ruleset_name="ovirt_snapshots",
)