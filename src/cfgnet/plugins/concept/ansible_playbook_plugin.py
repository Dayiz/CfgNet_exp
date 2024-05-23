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
from cfgnet.plugins.file_type.yaml_plugin import YAMLPlugin
from cfgnet.config_types.config_types import ConfigType
from cfgnet.errors.error import Error

class AnsiblePlaybookPlugin(YAMLPlugin):
    def __init__(self):
        super().__init__("ansible-playbook")

    def is_responsible(self, abs_file_path) -> bool:
        if abs_file_path.endswith(
            ("site.yml", "playbook.yml", "site.yaml", "playbook.yaml")
        ):
            return True

        if "playbooks/" in abs_file_path and abs_file_path.endswith(
            (".yml", ".yaml")
        ):
            return True

        return False

    # pylint: disable=too-many-return-statements
    def get_config_type(self, option_name: str) -> ConfigType:
        """
        Find config type based on option name.

        :param option_name: name of option
        :return: config type
        """        
        if option_name.endswith(("become","force","underline")):
            return ConfigType.BOOLEAN

        if option_name.endswith(("delay","timeout")):
            return ConfigType.NUMBER
        
        if option_name == "name":
            return ConfigType.NAME

        if option_name.endswith(("size", "register", "group", "master", "type", "append", "label", "help")):
            return ConfigType.NAME

        if option_name.endswith(("local_action")):
            return ConfigType.COMMAND

        if option_name.endswith("hosts"): #DISPLAY_SKIPPED_HOSTS is bool
            return ConfigType.HOST

        if option_name.endswith("state"):
            return ConfigType.STATE

        if option_name.endswith("user"):
            return ConfigType.USERNAME

        if option_name.endswith(("src", "dest", "path", "interpreter")):
            return ConfigType.PATH

        if option_name.endswith("password"):
            return ConfigType.PASSWORD

        if option_name.endswith("mode"):
            return ConfigType.MODE

        if option_name.endswith(("network", "gateway", "dns4")):
            return ConfigType.IP_ADDRESS

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
