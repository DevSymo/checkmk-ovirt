#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_vmstats.py
"""Check for oVirt VM statistics"""

# License: GNU General Public License v2

from cmk.agent_based.v2 import (
    AgentSection,
    CheckPlugin,
    CheckResult,
    DiscoveryResult,
    Result,
    Service,
    State,
    Metric,
)
from cmk_addons.plugins.ovirt.lib import parse_json_section

agent_section_ovirt_vmstats = AgentSection(
    name="ovirt_vmstats",
    parse_function=parse_json_section,
)

def discovery_ovirt_vmstats(section) -> DiscoveryResult:
    """Discover oVirt VM statistics service"""
    if "statistics" in section:
        yield Service()

def check_ovirt_vmstats(section) -> CheckResult:
    """Check oVirt VM statistics"""
    vm_name = section.get("name", "Unknown VM")
    vm_type = section.get("type", "Unknown")
    
    yield Result(state=State.OK, summary=f"VM: {vm_name}, Type: {vm_type}")
    
    stats = section.get("statistics", [])
    
    for stat in stats:
        stat_name = stat.get("name", "unknown")
        stat_value = stat.get("value", "0")
        stat_unit = stat.get("unit", "")
        stat_desc = stat.get("description", stat_name)
        
        try:
            value = float(stat_value)
        except (ValueError, TypeError):
            value = 0
        
        # Format display based on the type of statistic
        if stat_name == "cpu.current.total":
            # CPU usage is usually in percentage
            yield Result(
                state=State.OK,
                summary=f"CPU usage: {value:.1f}%"
            )
            yield Metric("cpu_usage", value)
        
        elif stat_name == "memory.installed":
            # Memory is typically in bytes, convert to MB for display
            memory_mb = value / (1024 * 1024)
            yield Result(
                state=State.OK,
                summary=f"Memory installed: {memory_mb:.1f} MB"
            )
            yield Metric("memory_installed", value)
        
        elif stat_name == "network.current.total":
            # Network usage, typically in bytes/sec
            network_kb = value / 1024
            yield Result(
                state=State.OK,
                summary=f"Network usage: {network_kb:.1f} KB/s"
            )
            yield Metric("network_usage", value)
        
        elif stat_name == "cpu.current.hypervisor":
            yield Result(
                state=State.OK,
                summary=f"CPU hypervisor: {value:.1f}%"
            )
            yield Metric("cpu_hypervisor", value)
        
        elif stat_name == "cpu.current.guest":
            yield Result(
                state=State.OK,
                summary=f"CPU guest: {value:.1f}%"
            )
            yield Metric("cpu_guest", value)
        
        else:
            # Generic handling for other statistics
            yield Result(
                state=State.OK,
                summary=f"{stat_desc}: {value} {stat_unit}"
            )
            # Create a sanitized metric name
            metric_name = stat_name.replace(".", "_")
            yield Metric(metric_name, value)

check_plugin_ovirt_vmstats = CheckPlugin(
    name="ovirt_vmstats",
    service_name="oVirt VM Statistics",
    discovery_function=discovery_ovirt_vmstats,
    check_function=check_ovirt_vmstats,
)