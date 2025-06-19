#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/agent_based/ovirt_clusters.py
"""Check for oVirt clusters"""

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

agent_section_ovirt_clusters = AgentSection(
    name="ovirt_clusters",
    parse_function=parse_json_section,
)

def discovery_ovirt_clusters(section) -> DiscoveryResult:
    """Discover oVirt cluster services"""
    for cluster in section.get("cluster", []):
        yield Service(item=cluster.get("name", "unknown"))

def check_ovirt_clusters(item, section) -> CheckResult:
    """Check oVirt cluster status"""
    for cluster in section.get("cluster", []):
        if cluster.get("name") == item:
            # Basic cluster information
            cluster_id = cluster.get("id", "unknown")
            yield Result(state=State.OK, summary=f"Cluster ID: {cluster_id}")
            
            # Version information
            if "version" in cluster:
                version = cluster.get("version", {})
                major = version.get("major", "unknown")
                minor = version.get("minor", "unknown")
                yield Result(state=State.OK, summary=f"Version: {major}.{minor}")
            
            # Data center information
            if "data_center" in cluster and "id" in cluster["data_center"]:
                dc_id = cluster["data_center"]["id"]
                yield Result(state=State.OK, summary=f"Data Center ID: {dc_id}")
            
            # Description if available
            if "description" in cluster and cluster["description"]:
                yield Result(state=State.OK, notice=f"Description: {cluster['description']}")
            
            return
    
    yield Result(state=State.UNKNOWN, summary=f"Cluster {item} not found")

check_plugin_ovirt_clusters = CheckPlugin(
    name="ovirt_clusters",
    service_name="oVirt Cluster %s",
    discovery_function=discovery_ovirt_clusters,
    check_function=check_ovirt_clusters,
)