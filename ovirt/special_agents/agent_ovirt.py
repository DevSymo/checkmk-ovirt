#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/special_agents/agent_ovirt.py
"""oVirt special agent"""

# License: GNU General Public License v2

import argparse
import json
import logging
import os
import sys
import time
import functools
from pathlib import Path

import requests
import urllib3
from cmk.special_agents.v0_unstable.agent_common import SectionWriter
from cmk.utils import password_store

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

password_store.replace_passwords()

LOGGER = logging.getLogger(__name__)

# API endpoints to fetch
API_ENDPOINTS = [
    "/api",
    "/api/hosts?all_content=true",
    "/api/datacenters?follow=storage_domains",
    "/api/clusters",
    "/api/vms?follow=statistics",
    "/api/vms?follow=snapshots"
]

def parse_arguments(argv):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=__doc__)

    # flags
    parser.add_argument("-v", "--verbose", action="count", default=0, 
                        help="Increase verbosity (for even more output use -vvv)")
    parser.add_argument("--debug", action="store_true",
                        help="Debug mode: let Python exceptions come through")

    parser.add_argument("--engine-fqdn", help="oVirt Engine FQDN")
    parser.add_argument("--engine-url", required=True, help="oVirt Engine URL")
    parser.add_argument("-u", "--username", default="admin@internal", help="oVirt Engine username")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-p", "--password", help="oVirt Engine password from CMK password store")
    group.add_argument("-s", "--secret", help="oVirt Engine password manually entered")
    
    parser.add_argument("--certfile", help="Path to certificate file")
    parser.add_argument("--no-piggyback", action="store_true", 
                        help="Disable generation of piggyback data")

    args = parser.parse_args(argv)
    
    # Configure logging based on verbosity
    fmt = "%%(levelname)5s: %s%%(message)s"
    if args.verbose == 0:
        logging.getLogger().setLevel(logging.WARNING)
    elif args.verbose == 1:
        logging.basicConfig(level=logging.INFO, format=fmt % "")
    else:
        logging.basicConfig(level=logging.DEBUG, format=fmt % "(line %(lineno)3d) ")
    
    if args.verbose < 3:
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return args

def time_it(func):
    """Decorator to time the function"""
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        before = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            LOGGER.info("%r took %ss", func.__name__, time.time() - before)
    return wrapped

class OvirtClient:
    """Client for oVirt API"""
    
    HEADERS = {'Accept': 'application/json', 'Version': '4'}
    
    def __init__(self, engine_url, username, password, certfile=None):
        self._engine_url = engine_url
        self._auth = (username, password)
        self._certfile = certfile
        self._verify = certfile if certfile else False
        
    def get_data(self, url):
        """Fetch data from API endpoint"""
        try:
            r = requests.get(
                self._engine_url + url,
                auth=self._auth, 
                verify=self._verify, 
                headers=self.HEADERS
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            LOGGER.error("Error fetching %s: %s", url, e)
            return {}

def process_hosts_data(hosts_data, generate_piggyback=True):
    """Process hosts data and create piggyback data if needed"""
    if not hosts_data or "host" not in hosts_data:
        return
    
    # Create piggyback data for each host
    if generate_piggyback:
        for host in hosts_data["host"]:
            host_obj = {}
            for key in ["version", "status", "summary", "type", "name", "libvirt_version", "hosted_engine"]:
                if host and key in host:
                    host_obj[key] = host[key]
            
            with SectionWriter(f"ovirt_hosts", piggytarget=host_obj["name"]) as w:
                w.append_json(host_obj)

def process_vms_stats(vms_data, generate_piggyback=True):
    """Process VM statistics data and create piggyback data if needed"""
    if not generate_piggyback or not vms_data or "vm" not in vms_data:
        return
    
    for vm in vms_data['vm']:
        vm_obj = {}
        
        for key in ["name", "type"]:
            if vm and key in vm:
                vm_obj[key] = vm[key]
        
        if "statistics" in vm and "statistic" in vm["statistics"]:
            for stat in vm["statistics"]["statistic"]:
                if stat["name"] not in ["network.current.total", "cpu.current.total", 
                                       "cpu.current.hypervisor", "cpu.current.guest", 
                                       "memory.installed"]:
                    continue
                stat_obj = {k: v for k, v in stat.items() if k in [
                    "name", "type", "unit", "description"]}
                for _, value in stat["values"]["value"][0].items():
                    stat_obj["value"] = str(value)
                vm_obj.setdefault("statistics", []).append(stat_obj)
        
        with SectionWriter(f"ovirt_vmstats", piggytarget=vm_obj["name"]) as w:
            w.append_json(vm_obj)

def process_vms_snapshots(vms_data, generate_piggyback=True):
    """Process VM snapshots data and create piggyback data if needed"""
    if not vms_data or "vm" not in vms_data:
        return
    
    # Create main section for all snapshots
    snapshots_data = []
    
    for vm in vms_data['vm']:
        vm_obj = {}
        
        for key in ["name", "type"]:
            if vm and key in vm:
                vm_obj[key] = vm[key]
        
        if "snapshots" in vm and "snapshot" in vm["snapshots"]:
            for snap in vm["snapshots"]["snapshot"]:
                vm_obj.setdefault("snapshots", []).append({k: v for k, v in snap.items() if k in [
                    "snapshot_status", "snapshot_type", "description", "date", "id"]})
        
        snapshots_data.append(vm_obj)
        
        # Create piggyback data for each VM
        if generate_piggyback and "name" in vm_obj:
            with SectionWriter(f"ovirt_snapshots", piggytarget=vm_obj["name"]) as w:
                w.append_json(vm_obj)
    
    # Write the main section with all snapshots
    with SectionWriter(f"ovirt_snapshots_engine") as w:
        w.append_json(snapshots_data)

def main(argv=None):
    """Main function to fetch data from oVirt API"""
    args = parse_arguments(argv or sys.argv[1:])
    
    try:
        # Get password from store or command line
        if args.password:
            pw_id, pw_path = args.password.split(":")
            password = password_store.lookup(Path(pw_path), pw_id)
        else:
            password = args.secret
        
        # Create oVirt client
        client = OvirtClient(
            engine_url=args.engine_url,
            username=args.username,
            password=password,
            certfile=args.certfile
        )
        
        # Version info to include in all sections
        version_info = {'PluginVersion': '1.0.6'}
        
        # Fetch API data
        api_data = client.get_data("/api")
        
        # Write overview section
        overview_data = {}
        for key in ["product_info", "summary"]:
            if api_data and key in api_data:
                overview_data.setdefault("api", {})[key] = api_data[key]
        
        # Fetch hosts data
        hosts_data = client.get_data("/api/hosts?all_content=true")
        
        # Check for global maintenance
        overview_data["global_maintenance"] = False
        if hosts_data and "host" in hosts_data:
            for host in hosts_data["host"]:
                if ("hosted_engine" in host and host["hosted_engine"] and 
                    "global_maintenance" in host["hosted_engine"] and 
                    host["hosted_engine"]["global_maintenance"] == "true"):
                    overview_data["global_maintenance"] = True
                    break
        
        with SectionWriter("ovirt_overview") as w:
            w.append_json(overview_data)
        
        # Process hosts data
        process_hosts_data(hosts_data, not args.no_piggyback)
        
        # Fetch and process datacenters and storage domains
        datacenters_data = client.get_data("/api/datacenters?follow=storage_domains")
        
        # Process datacenters data
        data_center_result = {"datacenters": []}
        storage_domain_result = {"storage_domains": []}
        
        if datacenters_data and "data_center" in datacenters_data:
            for datacenter in datacenters_data["data_center"]:
                if not datacenter:
                    continue
                
                datacenter_obj = {}
                for key in ["id", "version", "status", "description", "name", "supported_versions"]:
                    if key in datacenter:
                        datacenter_obj[key] = datacenter[key]
                
                data_center_result["datacenters"].append(datacenter_obj)
                
                for storage_domain in datacenter.get("storage_domains", {}).get("storage_domain", []):
                    if not storage_domain:
                        continue
                    
                    storage_domain_obj = {}
                    storage_domain_obj.setdefault("data_center", {})["name"] = datacenter["name"]
                    storage_domain_obj.setdefault("data_center", {})["id"] = datacenter["id"]
                    
                    for key in ["status", "name", "id", "external_status", "description", 
                               "committed", "available", "used", "warning_low_space_indicator"]:
                        if key in storage_domain:
                            storage_domain_obj[key] = storage_domain[key]
                    
                    storage_domain_result["storage_domains"].append(storage_domain_obj)
        
        with SectionWriter("ovirt_datacenters") as w:
            w.append_json(data_center_result)
        
        with SectionWriter("ovirt_storage_domains") as w:
            w.append_json(storage_domain_result)
        
        # Fetch and process clusters
        clusters_data = client.get_data("/api/clusters")
        cluster_result = {"cluster": []}
        
        if clusters_data and "cluster" in clusters_data:
            for cluster in clusters_data["cluster"]:
                if not cluster:
                    continue
                
                cluster_obj = {}
                for key in ["id", "version", "description", "name"]:
                    if key in cluster:
                        cluster_obj[key] = cluster[key]
                
                cluster_obj.setdefault("data_center", {})["id"] = cluster.get(
                    "data_center", {}).get("id", None)
                
                cluster_result["cluster"].append(cluster_obj)
        
        with SectionWriter("ovirt_clusters") as w:
            w.append_json(cluster_result)
        
        # Fetch and process VM stats
        vms_stats_data = client.get_data("/api/vms?follow=statistics")
        process_vms_stats(vms_stats_data, not args.no_piggyback)
        
        # Fetch and process VM snapshots
        vms_snapshots_data = client.get_data("/api/vms?follow=snapshots")
        process_vms_snapshots(vms_snapshots_data, not args.no_piggyback)
        
        # Write compatibility information
        compatibility_result = {}
        if api_data and "product_info" in api_data:
            compatibility_result["engine"] = api_data["product_info"]
        
        compatibility_result["datacenters"] = data_center_result.get("datacenters", [])
        compatibility_result["cluster"] = cluster_result.get("cluster", [])
        
        with SectionWriter("ovirt_compatibility") as w:
            w.append_json(compatibility_result)
        
        return 0
    
    except Exception as e:
        if args.debug:
            raise
        LOGGER.error("Error: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())