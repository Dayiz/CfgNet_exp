# This file is part of the CfgNet module.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import pytest

from cfgnet.conflicts.conflict import (
    MissingArtifactConflict,
    MissingOptionConflict,
    ModifiedOptionConflict,
)
from cfgnet.conflicts.conflict_detector import ConflictDetector
from cfgnet.network.network import Network
from cfgnet.network.network import NetworkConfiguration
from tests.utility.temporary_repository import TemporaryRepository


@pytest.fixture(name="get_simple_networks")
def get_simple_networks():
    """Return the conflicts and the updated simple git repository."""
    repo = TemporaryRepository(
        "tests/test_repos/maven_docker/0001-Add-Docker-and-maven-file.patch"
    )
    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(repo.root),
        enable_static_blacklist=False,
        enable_internal_links=False,
        enable_all_conflicts=False,
    )
    ref_network = Network.init_network(cfg=network_configuration)

    repo.apply_patch(
        "tests/test_repos/maven_docker/0002-Provoke-two-conflicts.patch"
    )
    new_network = Network.init_network(cfg=network_configuration)

    return ref_network, new_network


@pytest.fixture(name="get_nodejs_networks")
def get_nodejs_networks():
    """Return the conflicts and the updated simple git repository."""
    repo = TemporaryRepository(
        "tests/test_repos/node_example/0001-Init-repository.patch"
    )
    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(repo.root),
        enable_static_blacklist=False,
        enable_internal_links=False,
        enable_all_conflicts=False,
    )
    ref_network = Network.init_network(cfg=network_configuration)

    repo.apply_patch(
        "tests/test_repos/node_example/0002-Remove-option-and-artifact.patch"
    )
    new_network = Network.init_network(cfg=network_configuration)

    return ref_network, new_network


@pytest.fixture(name="get_networks_equally_changed")
def get_networks_equally_changed():
    """Return the conflicts and the updated simple git repository."""
    repo = TemporaryRepository(
        "tests/test_repos/equal_values/0001-Add-two-package.json-files.patch"
    )
    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(repo.root),
        enable_static_blacklist=False,
        enable_internal_links=False,
        enable_all_conflicts=False,
    )
    ref_network = Network.init_network(cfg=network_configuration)

    repo.apply_patch(
        "tests/test_repos/equal_values/0002-Change-config-values-equally.patch"
    )
    new_network = Network.init_network(cfg=network_configuration)

    return ref_network, new_network


def test_detect_conflicts(get_simple_networks):
    ref_network = get_simple_networks[0]
    new_network = get_simple_networks[1]

    conflicts = ConflictDetector.detect(
        ref_network=ref_network, new_network=new_network, enable_all_conflicts=False
    )

    modified_option_conflict = list(
        filter(lambda x: isinstance(x, ModifiedOptionConflict), conflicts)
    )

    assert len(conflicts) == 2
    assert len(modified_option_conflict) == 2


def test_detect_all_conflicts(get_nodejs_networks):
    ref_network = get_nodejs_networks[0]
    new_network = get_nodejs_networks[1]

    conflicts = ConflictDetector.detect(
        ref_network=ref_network, new_network=new_network, enable_all_conflicts=True
    )

    missing_artifact_conflict = list(
        filter(lambda x: isinstance(x, MissingArtifactConflict), conflicts)
    )

    missing_option_conflict = list(
        filter(lambda x: isinstance(x, MissingOptionConflict), conflicts)
    )

    assert len(conflicts) == 2
    assert len(missing_artifact_conflict) == 1
    assert len(missing_option_conflict) == 1


def test_equally_changed_values(get_networks_equally_changed):
    ref_network = get_networks_equally_changed[0]
    new_network = get_networks_equally_changed[1]

    conflicts = ConflictDetector.detect(
        ref_network=ref_network, new_network=new_network, enable_all_conflicts=False
    )

    assert len(conflicts) == 0
