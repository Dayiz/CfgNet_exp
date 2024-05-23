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

from yaml.nodes import MappingNode, ScalarNode

from cfgnet.network.nodes import OptionNode
from cfgnet.plugins.file_type.yaml_plugin import YAMLPlugin
from cfgnet.config_types.config_types import ConfigType
from cfgnet.errors.error import Error

class TravisPlugin(YAMLPlugin):
    def __init__(self):
        super().__init__("travis")

    def is_responsible(self, abs_file_path):
        if abs_file_path.endswith(".travis.yml"):
            return True
        return False

    def _parse_sequence_node(self, node, parent):
        for child in node.value:
            if isinstance(child, MappingNode):
                virtual_option = TravisPlugin._create_virtual_option(child)

                if virtual_option:
                    parent.add_child(virtual_option)
                    self._iter_tree(child, virtual_option)
            else:
                self._iter_tree(child, parent)

    @staticmethod
    def _create_virtual_option(node):
        key = node.value[0]
        if isinstance(key, tuple):
            if isinstance(key[0], ScalarNode) and isinstance(
                key[1], ScalarNode
            ):
                option_name = key[0].value + "/" + key[1].value
                virtual_option = OptionNode(
                    name=option_name, location=key[0].start_mark.line + 1
                )
                return virtual_option

        return None

    # pylint: disable=too-many-return-statements
    def get_config_type(self, option_name: str) -> ConfigType:
        """
        Find config type based on option name.

        :param option_name: name of option
        :return: config type
        """
        if option_name in (
            "before_install",
            "before_script",
            "script",
            "before_script",
            "install",
            "before_cache",
            "after_success",
            "after_failure",
            "before_deploy",
            "after_deploy",
            "after_script",
        ):
            return ConfigType.COMMAND
        
        if option_name.endswith("language"):
            return ConfigType.LANGUAGE

        if option_name in ("submodules", "quiet", "lfs_skip_smudge"):
            return ConfigType.BOOLEAN

        if option_name.endswith(("hosts", "URL", "url", "Url")):
            return ConfigType.URL

        if option_name in ("os", "arch"):
            return ConfigType.PLATFORM
        
        if option_name.endswith("version"):
            return ConfigType.VERSION_NUMBER

        if option_name in ("name", "services", "hostname", "dist", "compiler"):
            return ConfigType.NAME

        if option_name == "env":
            return ConfigType.ENVIRONMENT

        if any(
            x in option_name
            for x in ["file", "File", "FILE", "folder", "FOLDER"]
        ):
            return ConfigType.PATH
        if option_name in (
            "version",
            "firefox",
            "mariadb",
            "postgresql",
            "rethinkdb",
            "python",
            "php"
        ):
            return ConfigType.VERSION_NUMBER

        if option_name == "depth":
            return ConfigType.NUMBER
        if option_name.endswith(".username"):
            return ConfigType.USERNAME
        

        return ConfigType.UNKNOWN

    @staticmethod
    def correct_error(error: Error) -> None:
        _file = open(error.file_path, 'r')
        all_lines = _file.readlines()
        _file.close()
        irr_lines = all_lines[:error.line_number - 1]
        rel_lines = all_lines[error.line_number - 1:]
        for counter in range(len(rel_lines)):
            if str(error.wrong_value) in str(rel_lines[counter]):
                rel_lines[counter] = rel_lines[counter].replace(error.wrong_value, error.correct_value)
                break
        new_lines = irr_lines + rel_lines
        _file = open(error.file_path, 'w')
        _file.writelines(new_lines)
        _file.close()