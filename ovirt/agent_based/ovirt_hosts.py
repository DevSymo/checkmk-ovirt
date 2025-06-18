#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_hosts.py
"""Check for oVirt hosts"""

# License: GNU General Public License v2

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

agent_section_ovirt_hosts = AgentSection(
    name="ovirt_hosts",
    parse_function=parse_json_section,
)

def discovery_ovirt_hosts(section) -> DiscoveryResult:
    """Discover oVirt host service"""
    yield Service()

def check_ovirt_hosts(section) -> CheckResult:
    """Check oVirt host status"""
    try:
        status = section.get("status", "unknown")
        yield Result(state=State.OK, summary=f"Status: {status}")
    except (KeyError, AttributeError):
        pass
    
    try:
        host_type = section.get("type", "unknown")
        yield Result(state=State.OK, summary=f"Type: {host_type}")
    except (KeyError, AttributeError):
        pass
    
    try:
        version = section.get("version", {}).get("full_version", "unknown")
        yield Result(state=State.OK, summary=f"Version: {version}")
    except (KeyError, AttributeError):
        pass
    
    try:
        hosted_engine = section.get("hosted_engine", {})
        if hosted_engine.get("local_maintenance") == "true":
            yield Result(state=State.WARN, summary="Local maintenance active")
        else:
            yield Result(state=State.OK, summary="Local maintenance off")
    except (KeyError, AttributeError):
        pass
    
    yield Result(state=State.OK, notice="oVirt Host")

check_plugin_ovirt_hosts = CheckPlugin(
    name="ovirt_hosts",
    service_name="oVirt Host",
    discovery_function=discovery_ovirt_hosts,
    check_function=check_ovirt_hosts,
)