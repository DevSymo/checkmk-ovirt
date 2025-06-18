#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/rulesets/ovirt_snapshots.py
"""Ruleset for oVirt snapshots check"""

# License: GNU General Public License v2

from cmk.rulesets.v1 import Title
from cmk.rulesets.v1.form_specs import (
    Dictionary,
    DictElement,
    MonitoringState,
    ListOfStrings,
)
from cmk.rulesets.v1.rule_specs import CheckPlugins

def _valuespec_ovirt_snapshots():
    return Dictionary(
        elements={
            "state": DictElement(
                parameter_form=MonitoringState(
                    title=Title("State if snapshots are found"),
                    default_value=1,  # WARNING
                ),
                required=False,
            ),
            "allow": DictElement(
                parameter_form=ListOfStrings(
                    title=Title("Regular expressions for snapshots to allow even if ignored"),
                    help_text="List of regular expressions that match snapshot descriptions to allow, even if they match the ignore patterns.",
                ),
                required=False,
            ),
            "ignore": DictElement(
                parameter_form=ListOfStrings(
                    title=Title("Regular expressions for snapshots to ignore"),
                    help_text="List of regular expressions that match snapshot descriptions to ignore.",
                ),
                required=False,
            ),
        },
    )

rule_spec_ovirt_snapshots = CheckPlugins(
    name="ovirt_snapshots",
    title=Title("oVirt VM snapshots"),
    parameter_form=_valuespec_ovirt_snapshots,
)