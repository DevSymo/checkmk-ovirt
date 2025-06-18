#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/lib.py
"""Helper functions for oVirt checks"""

# License: GNU General Public License v2

import json
from typing import Any
from collections.abc import Mapping
from cmk.agent_based.v2 import StringTable

Section = Mapping[str, Any]

def parse_json_section(string_table: StringTable) -> Section:
    """Parse JSON data from string table"""
    try:
        return json.loads(string_table[0][0])
    except (IndexError, json.decoder.JSONDecodeError):
        return {}