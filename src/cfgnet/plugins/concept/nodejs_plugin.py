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
from cfgnet.plugins.file_type.json_plugin import JsonPlugin
from cfgnet.config_types.config_types import ConfigType
from cfgnet.errors.error import Error

class NodejsPlugin(JsonPlugin):
    def __init__(self):
        super().__init__("nodejs")
        self.excluded_keys = [
            "keywords",
            "description",
            "author",
            "contributors",
        ]

    def is_responsible(self, abs_file_path: str) -> bool:
        if abs_file_path.endswith("package.json"):
            return True
        return False

    # pylint: disable=too-many-return-statements
    def get_config_type(self, option_name: str) -> ConfigType:
        """
        Find config type based on option name.

        :param option_name: name of option
        :return: config type
        """
        if option_name in (
            "version",
            "dependencies",#is dict?
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
            "engines",
        ):
            return ConfigType.VERSION_NUMBER
        if option_name in (
            "main",
            "files",
            "man",
            "directories",
            "workspaces",
        ):
            return ConfigType.PATH
        if (option_name.endswith("Width") or
            option_name.endswith("size")):
            return ConfigType.COUNT            
        if option_name in ("scripts", "bin"):
            return ConfigType.COMMAND
        if option_name in ("name", "bundledDependencies"):
            return ConfigType.NAME
        if option_name == "url" or option_name.endswith("package_url"):
            return ConfigType.URL
        if option_name.endswith("email"):
            return ConfigType.EMAIL
        if option_name in ("repository", "funding", "type"):
            return ConfigType.UNKNOWN
        if option_name == "license":
            return ConfigType.LICENSE
        if option_name == "private" or option_name == "has_sig":
            return ConfigType.BOOLEAN
        if option_name == "description":
            return ConfigType.MESSAGE
        return ConfigType.UNKNOWN

    @staticmethod
    def correct_error(error: Error) -> None:
        _file = open(error.file_path, 'r')
        all_lines = _file.readlines()
        _file.close()
        irr_lines = all_lines[0:error.line_number - 1]
        rel_lines = all_lines[error.line_number - 1:]
        for counter in range(len(rel_lines)):
            if str(error.wrong_value) in str(rel_lines[counter]):
                rel_lines[counter] = rel_lines[counter].replace(error.wrong_value, error.correct_value)
                break
        new_lines = irr_lines + rel_lines
        _file = open(error.file_path, 'w')
        _file.writelines(new_lines)
        _file.close()