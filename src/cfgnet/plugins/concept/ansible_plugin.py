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
from cfgnet.plugins.file_type.configparser_plugin import ConfigParserPlugin
from cfgnet.errors.error import Error

class AnsiblePlugin(ConfigParserPlugin):
    def __init__(self):
        super().__init__("ansible")

    def is_responsible(self, abs_file_path):
        if abs_file_path.endswith("ansible.cfg"):
            return True
        return False

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