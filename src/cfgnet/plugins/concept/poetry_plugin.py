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
from cfgnet.plugins.file_type.toml_plugin import TomlPlugin
from cfgnet.config_types.config_types import ConfigType
from cfgnet.errors.error import Error

class PoetryPlugin(TomlPlugin):
    def __init__(self):
        super().__init__("poetry")
        self.excluded_keys = [
            "description",
            "authors",
            "maintainers",
            "readme",
            "keywords",
            "classifiers",
        ]

    def is_responsible(self, abs_file_path: str) -> bool:
        if abs_file_path.endswith("pyproject.toml"):
            return True
        return False

    # pylint: disable=too-many-return-statements
    @staticmethod
    def get_config_type(option_name: str) -> ConfigType:
        """
        Find config type based on option name.

        :param option_name: name of option
        :return: config type
        """
        if option_name.endswith("length"):
            return ConfigType.COUNT
        if (option_name.endswith("skip_empty") or 
            option_name.endswith("optional") or 
            option_name.endswith("allows-prereleases") or
            option_name.endswith("balanced_wrapping") or
            option_name.endswith("combine_as_imports")):
            return ConfigType.BOOLEAN
        if option_name == "name":
            return ConfigType.PEPNAME
        if option_name == "license":
            return ConfigType.LICENSE
        if option_name in (
            "homepage",
            "repository",
            "documentation",
            "urls",
            "url",
        ):
            return ConfigType.URL
        if option_name.endswith("extras"):
            return ConfigType.NAME
        if option_name.endswith("path"):
            return ConfigType.PATH
        if option_name in ("include", "exclude"):
            return ConfigType.PATH
        if option_name.endswith("version"):
            return ConfigType.VERSION_NUMBER
        if option_name in ("version", "dependencies", "dev-dependencies"):
            return ConfigType.VERSION_NUMBER
        if option_name == "scripts":
            return ConfigType.COMMAND
        return ConfigType.UNKNOWN

    @staticmethod
    def correct_error(error: Error) -> None:
        _file = open(error.file_path, 'r')
        all_lines = _file.readlines()
        _file.close()
        irr_lines = all_lines[:int(error.line_number) - 1]
        rel_lines = all_lines[int(error.line_number) - 1:]
        for counter in range(len(rel_lines)):
            if str(error.wrong_value) in str(rel_lines[counter]):
                rel_lines[counter] = rel_lines[counter].replace(error.wrong_value, error.correct_value)
                break
        new_lines = irr_lines + rel_lines
        _file = open(error.file_path, 'w')
        _file.writelines(new_lines)
        _file.close()