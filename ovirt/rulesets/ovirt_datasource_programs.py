#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/rulesets/ovirt_datasource_programs.py
"""oVirt datasource program settings"""

# License: GNU General Public License v2

from cmk.rulesets.v1 import Title, Label
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    DictElement,
    Dictionary,
    String,
    Password,
    validators,
    migrate_to_password,
)
from cmk.rulesets.v1.rule_specs import Topic, SpecialAgent

def _valuespec_special_agents_ovirt():
    return Dictionary(
        elements={
            "engine_fqdn": DictElement(
                parameter_form=String(
                    title=Title("oVirt Engine FQDN"),
                ),
                required=False,
            ),
            "engine_url": DictElement(
                parameter_form=String(
                    title=Title("oVirt Engine URL"),
                    help_text="The URL to the oVirt Engine API, e.g. https://ovirt.example.com/ovirt-engine",
                ),
                required=True,
            ),
            "username": DictElement(
                parameter_form=String(
                    title=Title("Username"),
                    #default_value="admin@internal",
                ),
                required=False,
            ),
            "password": DictElement(
                parameter_form=Password(
                    title=Title("Password"),
                    custom_validate=(validators.LengthInRange(min_value=1),),
                    migrate=migrate_to_password,
                ),
                required=True,
            ),
            "certfile": DictElement(
                parameter_form=String(
                    title=Title("Certificate file path"),
                    help_text="Path to the certificate file for SSL verification",
                ),
                required=False,
            ),
            "no_piggyback": DictElement(
                parameter_form=BooleanChoice(
                    label=Label("Disable piggyback data generation"),
                    help_text="If enabled, no piggyback data will be generated for hosts and VMs",
                ),
                required=False,
            ),
        },
    )

rule_spec_ovirt = SpecialAgent(
    name="ovirt",
    title=Title("oVirt/RHV Virtualization Platform"),
    topic=Topic.VIRTUALIZATION,
    parameter_form=_valuespec_special_agents_ovirt,
)