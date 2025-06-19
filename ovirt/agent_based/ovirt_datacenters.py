#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_datacenters.py
"""Check for oVirt data centers"""

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

agent_section_ovirt_datacenters = AgentSection(
    name="ovirt_datacenters",
    parse_function=parse_json_section,
)

def discovery_ovirt_datacenters(section) -> DiscoveryResult:
    """Discover oVirt data center services"""
    for datacenter in section.get("datacenters", []):
        yield Service(item=datacenter.get("name", "unknown"))

def check_ovirt_datacenters(item, section) -> CheckResult:
    """Check oVirt data center status"""
    for datacenter in section.get("datacenters", []):
        if datacenter.get("name") == item:
            # Basic data center information
            dc_id = datacenter.get("id", "unknown")
            yield Result(state=State.OK, summary=f"Data Center ID: {dc_id}")
            
            # Status information
            status = datacenter.get("status", "unknown")
            if status == "up":
                state = State.OK
            elif status == "maintenance":
                state = State.WARN
            else:
                state = State.CRIT
            yield Result(state=state, summary=f"Status: {status}")
            
            # Version information
            if "version" in datacenter:
                version = datacenter.get("version", {})
                major = version.get("major", "unknown")
                minor = version.get("minor", "unknown")
                yield Result(state=State.OK, summary=f"Version: {major}.{minor}")
            
            # Supported versions if available
            if "supported_versions" in datacenter and datacenter["supported_versions"]:
                supported = []
                for version in datacenter["supported_versions"].get("version", []):
                    major = version.get("major", "?")
                    minor = version.get("minor", "?")
                    supported.append(f"{major}.{minor}")
                
                if supported:
                    yield Result(state=State.OK, notice=f"Supported versions: {', '.join(supported)}")
            
            # Description if available
            if "description" in datacenter and datacenter["description"]:
                yield Result(state=State.OK, notice=f"Description: {datacenter['description']}")
            
            return
    
    yield Result(state=State.UNKNOWN, summary=f"Data Center {item} not found")

check_plugin_ovirt_datacenters = CheckPlugin(
    name="ovirt_datacenters",
    service_name="oVirt Data Center %s",
    discovery_function=discovery_ovirt_datacenters,
    check_function=check_ovirt_datacenters,
)