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

import abc
import logging
import os
import re

from typing import List, Any, Optional

class Constraint(abc.ABC):

    def __init__(self,option_name: Optional[str] = None, value_type: Optional[str] = None,
                value_syntax: Optional[str] = None,
                value_range: Optional[list] = None,
                value_set: Optional[list] = None, can_be_list: bool = False,
                constraint_type: Optional[str] = None):
        self.option_name: Optional[str] = option_name
        self.value_type: Optional[str] = value_type
        self.value_syntax: Optional[str] = value_syntax
        self.value_range: Optional[List[int]] = value_range
        self.value_set: Optional[List[str]] = value_set
        self.can_be_list: bool = can_be_list
        self.constraint_type = constraint_type
        if can_be_list:
            self._convert_syntax_pattern_to_list()

    def overwrite_value(self, parameter: str, value: Any):
        if(parameter == "option_name"):
            self.option_name = value
        if(parameter == "value_type"):
            self.value_type = value
        if(parameter == "value_syntax"):
            self.value_syntax = value
        if(parameter == "value_range"):
            self.value_range = value
        if(parameter == "value_set"):
            self.value_set = value
        if(parameter == "can_be_list"):
            self.can_be_list = value
        if(parameter == "constraint_type"):
            self.constraint_type = value
        if(parameter == "can_be_list"):
            if value:
                self._convert_syntax_pattern_to_list()
        

    def _validate_type(self, value) -> bool:
        #TODO
        if self.value_type == "int":
            try:
                if isinstance(int(value), int):
                    return True
                else:
                    return False
            except:
                return False
        if self.value_type == "string":
            return isinstance(value, str)
        if self.value_type == "fraction":
            try:
                if isinstance(float(value), float):
                    return True
                else:
                    return False
            except:
                return False
        return True

    def _validate_syntax(self, value) -> bool:
        if(self.value_syntax == None):
            return True
        syntax_test = re.compile(self.value_syntax)
        if syntax_test.match(value):
            return True
        return False
    
    def _validate_range(self, value) -> bool:
        if(self.value_range == None or self.value_range == [None, None]):
                return True
        result = True
        if self.value_type == "int":
            try:
                value = int(value)
            except:
                return False
            #numerical_value_parts = re.findall(r"-{0,1}\d+", str(value))            
            #for num in numerical_value_parts:
            if(not isinstance(self.value_range[1], int) and isinstance(self.value_range[0], int)):
                return (int(value) >= self.value_range[0])
            if(not isinstance(self.value_range[0], int) and isinstance(self.value_range[1], int)):
                return (int(value) <= self.value_range[1])
            if(isinstance(self.value_range[0], int) and isinstance(self.value_range[1], int)):
                return (int(value) >= self.value_range[0] and
                                     int(value) <= self.value_range[1])
            else:
                result = True
        #TODO fractions
        if self.value_type == "fraction":
            numerical_value_parts = re.findall(r"[\d]+[.][\d]+", str(value))            
            for num in numerical_value_parts:            
                if(self.value_range[1] == None):
                    result = result and (float(num) >= self.value_range[0])
                if(self.value_range[0] == None):
                    result = result and (float(num) <= self.value_range[1])
                else:
                    result = result and (float(num) >= self.value_range[0] and
                                         float(num) <= self.value_range[1])
        return result
    
    def _validate_set(self, value) -> bool:
        if(self.value_set == None):
            return True 
        return (value in self.value_set)
    
    def _convert_syntax_pattern_to_list(self) -> None:        
        list_pattern = "^\[(\"|'){0,1}(" + self.value_syntax[1:-1] + ")(\"|'){0,1}(,[ ]{0,1}(\"|'){0,1}" + self.value_syntax[1:-1] + "(\"|'){0,1})*\]$"
        return list_pattern
    
    @abc.abstractmethod
    def validate_value(self, value: Any) -> bool:
        """
        validates the constraint

        return (self._validate_syntax(value) and self._validate_range(value) and
                self._validate_set(value) and 
                self._validate_special_constraints(value))
        """
    
    @abc.abstractmethod
    def _validate_special_constraints(self, value: Any) -> bool:
        """
        Helper method to include special constraints in the validate_constraint method
        """

class NumericalConstraint(Constraint):
    # validated by type and value range
    def validate_value(self, value: Any) -> bool:
        return (self._validate_range(value) and self._validate_type(value) 
                and self._validate_special_constraints(value))

class StringConstraint(Constraint):
    #validated by syntax
    def validate_value(self, value: Any) -> bool:
        return (self._validate_syntax(value) and self._validate_special_constraints(value))

class NumberAndStringConstraint(Constraint):
    #validated by syntax and value range
    def validate_value(self, value: Any) -> bool:
        return (self._validate_syntax(value) and self._validate_range(value)
                and self._validate_special_constraints(value))

class EnumConstraint(Constraint):
    #validated by value set
    def validate_value(self, value: Any) -> bool:
        return (self._validate_set(value) and self._validate_special_constraints(value))

class DictConstraint(Constraint):
    pass

class UserDefConstraint(Constraint):
    def __init__(self):
        super().__init__(
            constraint_type = "special"
            )
        self.prefix = None,
        self.stem = None,
        self.sufix = None,     
    
    def validate_value(self, value: Any) -> bool:
        result = True
        if self.value_type != None:
            result = result and self._validate_type(value)
        if self.value_syntax != None:
            result = result and self._validate_syntax(value)
        if self.value_range != None:
            result = result and self._validate_range(value)
        if self.value_set != None:
            result = result and self._validate_set(value)
        return result
    
    def overwrite_value(self, parameter: str, value: Any):
        if(parameter == "value_type"):
            self.value_type = value
        if(parameter == "value_syntax"):
            self.value_syntax = value
        if(parameter == "value_range"):
            self.value_range = value
        if(parameter == "value_set"):
            self.value_set = value
        if(parameter == "sufix"):
            self.sufix = value
        if(parameter == "prefix"):
            self.prefix = value
        if(parameter == "stem"):
            self.stem = value
        if(parameter == "constraint_type"):
            self.constraint_type = value

    def is_responsible(self, option_name: str) -> bool:
        result = False
        if self.prefix == None and self.sufix == None and self.stem == None:
            return False
        if self.prefix != None and isinstance(str(self.prefix), str):
            result = result and option_name.startswith(str(self.prefix))
        if self.sufix != None and isinstance(str(self.sufix), str):
            result = result and option_name.endswith(str(self.sufix))
        if self.stem != None and isinstance(str(self.stem), str):
            result = result and (str(self.stem) in option_name)
        return result

    def _validate_special_constraints(self, value: Any) -> bool:
        return True

# Numbers
class PortConstraint(NumericalConstraint):
    def __init__(self):
        super().__init__(
            value_type = "int",
            value_range = [0,65535],
            constraint_type = "port"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True

class FractionConstraint(NumericalConstraint):
    def __init__(self):
        super().__init__(
            value_type = "fraction",
            value_range = [0,None],
            constraint_type = "fraction"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True

class CountConstraint(NumericalConstraint):
    def __init__(self):
        super().__init__(
            value_type = "int",
            value_range = [0,None],
            constraint_type = "count"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True
    
class NumberConstraint(NumericalConstraint):
    def __init__(self):
        super().__init__(
            value_type = "int",
            value_range = [None,None],
            constraint_type = "number"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True


#no proper constraints found
class IdConstraint(NumericalConstraint):
    def __init__(self):
        super.__init__(
            value_type = "int",
            value_range = (0,65535),
            constraint_type = "id"
            )
        
    def _validate_special_constraints(value):
        return True


# Strings

class NameConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^([a-zA-Z0-9#,;()._|/+{}$ -]+)$",
            constraint_type = "name"
            )
        self.length = length
    
    #maximum length of name
    def _validate_special_constraints(self, value: Any):
        if self.length == None:
            return True
        if len(value) > self.length:
            return False
        return True
    
#pep508 naming
class PEPNameConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9._\-]*[a-zA-Z0-9])$",
            constraint_type = "pepname"
            )
        self.length = length
    
    #maximum length of name
    def _validate_special_constraints(self, value: Any):
        if self.length == None:
            return True
        if len(value) > self.length:
            return False
        return True

class MessageConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^([a-zA-Z0-9][a-zA-Z0-9. _!?-]*[a-zA-Z0-9!?.])$",
            constraint_type = "message"
            )
        self.length = length
    
    #maximum length of name
    def _validate_special_constraints(self, value: Any):
        if self.length == None:
            return True
        if len(value) > self.length:
            return False
        return True

class UsernameConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^[a-zA-Z][a-zA-Z0-9]*$",
            constraint_type = "username"
            )
        self.length = length
    
    #maximum length of name
    def _validate_special_constraints(self, value: Any):
        if self.length == None:
            return True
        if len(value) > self.length:
            return False
        return True


class PasswordConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r".*",
            constraint_type = "password"
            )
        self.length = length
    
    #maximum length of name
    def _validate_special_constraints(self, value: Any):
        if self.length == None:
            return True
        if len(value) > self.length:
            return False
        return True


class UrlConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^((http(s)?)://)?((www|api|smtp|files).)?([a-zA-Z0-9][a-zA-Z0-9-]){1,61}[a-zA-Z0-9](.[a-z]{2,3}){1,2}(/[a-zA-Z0-9\-_.]{2,})*([/]|.[a-zA-Z]{1,})?$",
            constraint_type = "url"
            )
    
    def _validate_special_constraints(self, value: Any) -> bool:
        return True


class EmailConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])",
            constraint_type = "email"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        return True

    
class DomainNameConstraint(StringConstraint):
    def __init__(self, length = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^([a-zA-Z0-9-:]{1,61}[.])+(.[a-z]{2,3}){1,2}(/[a-zA-Z0-9\-]{2,})*([/]|.[a-zA-Z]{1,})?$",
            constraint_type = "domainmame"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        return True


class PathConstraint(StringConstraint):
    #TODO include partial and directory path
    def __init__(self, file_format = None):
        super().__init__(
            value_type = "string",
            value_syntax = r"^(([A-Z]:){0,1}[/]{0,1}([a-zA-Z0-9._${}~!&'()+,;=@ -])+|[/]|[.][.][/])+$",
            #value_syntax = r".*",
            constraint_type = "path"
            )
        self.file_format = file_format

    def _validate_special_constraints(self, value) -> bool:
        if self.file_format == None:
            return True
        return str(value).endswith("file_format_length")


class PatternConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r".*",
            constraint_type = "pattern"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        is_valid_regex = True
        try:
            re.compile(value)
        except re.error:
            is_valid_regex = False
        return is_valid_regex


class LanguageConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r"[a-z]{2}([_][A-Z]{2}){0,1}",
            constraint_type = "language"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        return True

    
#RFC6838
class MimeConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r"^([a-zA-Z0-9][\w!#$&^\-_]*/[a-zA-Z0-9][\w!#$&^\-._]+)$",
            constraint_type = "mime"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        return True

#django exlusive, python class names
class ClassConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r"^[\w]+(.[\w]+)*$",
            constraint_type = "class"
            )
        
    def _validate_special_constraints(self, value: Any) -> bool:
        return True


class PermissionConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r"^(0o){0,1}[\d]{1-5}$",
            constraint_type = "permission"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True
    

class VersionNumberConstraint(StringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "string",
            value_syntax = r"^(\^|<|>|<=|>=|v|=){0,1}[ ]{0,1}[\d]+(.[\d\w-]+)*$",
            can_be_list = True,
            constraint_type = "versionnumber"
            )
        
    def _validate_special_constraints(self, value: Any):
        return True

# Mixed
class TimeConstraint(NumberAndStringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "fraction",
            value_syntax = r"^[\d]+([.][\d]+){0,1}(s|S|m|M|h|H|d|D|ms|MS|min|Min)$",
            value_range = [0,None],
            constraint_type = "time"
            )
    def _validate_special_constraints(self, value: Any):
        return True


class SpeedConstraint(NumberAndStringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "fraction",
            value_syntax = r"[\d]+([.][\d]+){0,1}(bps|Kbps|Mbps)",
            value_range = [0,None],
            constraint_type = "speed"
            )
    def _validate_special_constraints(self, value: Any):
        return True


class SizeConstraint(NumberAndStringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "fraction",
            value_syntax = r"[\d]+([.][\d]+){0,1}(K|M|k|m|km|KM|g|G|t|T|kb|KB|mb|MB|gb|GB|tb|TB|b|B)",
            value_range = [0,None],
            constraint_type = "size"
            )
    def _validate_special_constraints(self, value: Any):
        return True


class IpAddressConstraint(NumberAndStringConstraint):
    def __init__(self):
        super().__init__(
            value_type = "int",
            value_syntax = "[\d]{1,3}.[\d]{1,3}.[\d]{1,3}.[\d]{1,3}",
            value_range = (0,255),
            constraint_type = "ipaddress"
            )
    def _validate_special_constraints(self, value: Any):
        return True

#Booleans
class BooleanConstraint(EnumConstraint):
    def __init__(self):
        super().__init__(
            value_set = ["True", "true", "False", "false", "on", "off"],
            constraint_type = "boolean"
        )
    def _validate_special_constraints(self, value: Any):
        return True

#Technology Specific (even option name specific)->user userdef constraint
class ModeConstraint(EnumConstraint):
    pass

#check if valid command? which command syntax?
class CommandConstraint(Constraint):
    pass
#what is a valid license?
class LicenseConstraint(Constraint):
    pass
#what is a valid environment?
class EnvironmentConstraint(Constraint):
    pass
#inconclusive
class TypeConstraint(Constraint):
    pass    
#Django exclusive
class HostConstraint(Constraint):
    pass
#nothing found
class StateConstraint(Constraint):
    pass

class PlatformConstraint(EnumConstraint):
    pass
#inconclusive. is value set?
class ProtocolConstraint(Constraint):
    pass
#currently docker specific
class ImageConstraint(Constraint):
    pass