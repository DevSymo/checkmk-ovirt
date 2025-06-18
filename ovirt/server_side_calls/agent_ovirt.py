#!/usr/bin/env python3
# /local/lib/python3/cmk_addons/plugins/ovirt/server_side_calls/agent_ovirt.py
"""build special agent command line for oVirt monitoring"""

# License: GNU General Public License v2

from collections.abc import Iterator
from pydantic import BaseModel

from cmk.server_side_calls.v1 import (
    HostConfig,
    Secret,
    SpecialAgentCommand,
    SpecialAgentConfig,
)

class Params(BaseModel):
    """Parameters for the oVirt special agent"""
    
    engine_fqdn: str = ""
    engine_url: str
    username: str = "admin@internal"
    password: Secret
    certfile: str = ""
    no_piggyback: bool = False

def _agent_ovirt_arguments(
    params: Params, host_config: HostConfig
) -> Iterator[SpecialAgentCommand]:
    """build command line arguments for oVirt special agent"""
    command_arguments = []
    
    if params.engine_fqdn:
        command_arguments += ["--engine-fqdn", params.engine_fqdn]
    
    command_arguments += ["--engine-url", params.engine_url]
    
    if params.username:
        command_arguments += ["-u", params.username]
    
    if params.password:
        command_arguments += ["-p", params.password]
    
    if params.certfile:
        command_arguments += ["--certfile", params.certfile]
    
    if params.no_piggyback:
        command_arguments += ["--no-piggyback"]
    
    yield SpecialAgentCommand(command_arguments=command_arguments)

special_agent_ovirt = SpecialAgentConfig(
    name="ovirt",
    parameter_parser=Params.model_validate,
    commands_function=_agent_ovirt_arguments,
)