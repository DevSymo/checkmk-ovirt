#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_overview.py
"""Check for oVirt Engine overview"""

# License: GNU General Public License v2

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    HostLabel,
)
from cmk_addons.plugins.ovirt.lib import parse_json_section

agent_section_ovirt_overview = AgentSection(
    name="ovirt_overview",
    parse_function=parse_json_section,
    host_label_function=lambda section: [HostLabel(u'cmk/ovirt_object', u'engine')],
)

def discovery_ovirt_overview(section) -> DiscoveryResult:
    """Discover oVirt Engine service"""
    yield Service()

def check_ovirt_overview(section) -> CheckResult:
    """Check oVirt Engine status"""
    api = section.get("api", {})
    
    try:
        version = api.get("product_info", {}).get("version", {}).get("full_version", "unknown")
        yield Result(state=State.OK, summary=f"oVirt Engine {version}")
    except (KeyError, AttributeError):
        pass
    
    try:
        hosts = api.get("summary", {}).get("hosts", {})
        active_hosts = hosts.get("active", 0)
        total_hosts = hosts.get("total", 0)
        yield Result(state=State.OK, summary=f"{active_hosts} of {total_hosts} hosts active")
    except (KeyError, AttributeError):
        pass
    
    try:
        storage_domains = api.get("summary", {}).get("storage_domains", {})
        active_domains = storage_domains.get("active", 0)
        total_domains = storage_domains.get("total", 0)
        yield Result(state=State.OK, summary=f"{active_domains} of {total_domains} storage domains active")
    except (KeyError, AttributeError):
        pass
    
    try:
        vms = api.get("summary", {}).get("vms", {})
        active_vms = vms.get("active", 0)
        total_vms = vms.get("total", 0)
        yield Result(state=State.OK, summary=f"{active_vms} of {total_vms} VMs active")
    except (KeyError, AttributeError):
        pass
    
    try:
        if section.get("global_maintenance", False):
            yield Result(state=State.CRIT, summary="Global maintenance active")
        else:
            yield Result(state=State.OK, summary="Global maintenance off")
    except (KeyError, AttributeError):
        pass
    
    yield Result(state=State.OK, notice="oVirt Engine")

check_plugin_ovirt_overview = CheckPlugin(
    name="ovirt_overview",
    service_name="oVirt Engine",
    discovery_function=discovery_ovirt_overview,
    check_function=check_ovirt_overview,
)