#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_storage_domains.py
"""Check for oVirt storage domains"""

# License: GNU General Public License v2

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    get_value_store,
)
from cmk.plugins.lib.df import df_check_filesystem_single
from cmk_addons.plugins.ovirt.lib import parse_json_section

agent_section_ovirt_storage_domains = AgentSection(
    name="ovirt_storage_domains",
    parse_function=parse_json_section,
)

def discovery_ovirt_storage_domains(section) -> DiscoveryResult:
    """Discover oVirt storage domain services"""
    for domain in section.get("storage_domains", []):
        if domain.get("status", "") == "inactive":
            continue
        yield Service(item=f"{domain['name']} id {domain['id']}")

def check_ovirt_storage_domains(item, params, section) -> CheckResult:
    """Check oVirt storage domain status and capacity"""
    for domain in section.get("storage_domains", []):
        if f"{domain['name']} id {domain['id']}" != item:
            continue
            
        if domain.get("status") == "inactive":
            yield Result(state=State.UNKNOWN, summary="Storage Domain inactive")
            return
            
        mib = 1024.0**2
        committed_bytes = float(domain.get("committed", 0))
        available_bytes = float(domain.get("available", 0))
        used_bytes = float(domain.get("used", 0))
        size_bytes = available_bytes + used_bytes
            
        if size_bytes == 0 or available_bytes is None:
            yield Result(state=State.UNKNOWN, summary="Size of Storage Domain not available")
            return
            
        yield from df_check_filesystem_single(
            get_value_store(),
            item,
            size_bytes / mib,
            available_bytes / mib,
            0,
            None,
            None,
            params=params
        )

check_plugin_ovirt_storage_domains = CheckPlugin(
    name="ovirt_storage_domains",
    service_name="oVirt Storage Domain %s",
    discovery_function=discovery_ovirt_storage_domains,
    check_function=check_ovirt_storage_domains,
    check_ruleset_name="filesystem",
)