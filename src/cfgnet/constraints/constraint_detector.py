import json
import os
import logging
import re

from cfgnet.network.nodes import ArtifactNode
from pathlib import Path
from cfgnet.constraints.constraint import *
from cfgnet.constraints.constraint_template import ConstraintTemplate
from cfgnet.utility.prettyNames import PrettyNames
from cfgnet.conflicts.conflict import ConstraintViolationConflict

class ConstraintDetector():

    def get_responsible_constraint_type(self, value_type_enum) -> Optional[Constraint]: 
        value_type = str(value_type_enum)
        if value_type == "TIME":
            return TimeConstraint()
        if value_type == "PORT":
            return PortConstraint()
        if value_type == "VERSION_NUMBER":
            return VersionNumberConstraint()
        if value_type == "FRACTION":
            return FractionConstraint()
        if value_type == "SPEED":
            return SpeedConstraint()
        if value_type == "PERMISSION":
            return PermissionConstraint()
        if value_type == "COUNT":
            return CountConstraint()
        if value_type == "SIZE":
            return SizeConstraint()
        if value_type == "IP_ADDRESS":
            return IpAddressConstraint()
        if value_type == "ID":
            return None
        if value_type == "NAME":
            return NameConstraint()
        if value_type == "USERNAME":
            return UsernameConstraint()
        if value_type == "PASSWORD":
            return PasswordConstraint()
        if value_type == "URL":
            return UrlConstraint()
        if value_type == "EMAIL":
            return EmailConstraint()
        if value_type == "DOMAIN_NAME":
            return DomainNameConstraint()
        if value_type == "PROTOCOL":
            return None
        if value_type == "IMAGE":
            return None
        if value_type == "PATH":
            return PathConstraint()
        if value_type == "COMMAND":
            return None
        if value_type == "LICENSE":
            return None
        if value_type == "ENVIRONMENT":
            return None
        if value_type == "PATTERN":
            return PatternConstraint()
        if value_type == "PLATFORM":
            return None
        if value_type == "LANGUAGE":
            return LanguageConstraint()
        if value_type == "TYPE":
            return None
        if value_type == "MIME":
            return MimeConstraint()
        if value_type == "HOST":
            return None
        if value_type == "STATE":
            return None
        if value_type == "CLASS":
            return ClassConstraint()
        if value_type == "BOOLEAN":
            return BooleanConstraint()
        if value_type == "MODE":
            return None
        if value_type == "NUMBER":
            return NumberConstraint()
        if value_type == "MESSAGE":
            return MessageConstraint()
        if value_type == "PEPNAME":
            return PEPNameConstraint()
        if value_type == "USERNAME":
            return UsernameConstraint()
        if value_type == "PASSWORD":
            return PasswordConstraint()
        if value_type == "MESSAGE":
            return MessageConstraint()
        if value_type == "PATTERN":
            return PatternConstraint()
        if value_type == "PEPNAME":
            return PEPNameConstraint()
        return None


    def check_constraints(self, artifact_node: ArtifactNode):
        """Validate Constraints by analyzing each config option if their values violate their constraints"""
        detected_constraint_dicts = self._get_constraint_dicts()        
        overwrite_values = None
        special_constraints: List[Optional[UserDefConstraint]] = []
        pn = PrettyNames()
        #Check if override is available        
        if artifact_node.concept_name and len(detected_constraint_dicts) > 0:
            for constraint_dict in detected_constraint_dicts:
                if constraint_dict["concept"] == artifact_node.concept_name:
                    overwrite_values = constraint_dict
                    special_constraints = self._init_special_constraint(overwrite_values)
        
        detected_conflicts = []
        value_nodes = artifact_node.get_nodes()
        for node in value_nodes:
            option_name = node.get_options()
            option_value = pn.gpn(artifact_node.concept_name, node.name)
            option_node = node.parent
            option_type = str(node.parent.config_type).split(".")[-1]

            constraint = self.get_responsible_constraint_type(option_type)
            for special_constraint in special_constraints:
                if special_constraint.is_responsible(option_name):
                    constraint = special_constraint
                    break
            if constraint == None:
                continue
            if overwrite_values:
                self._overwrite_values(constraint, overwrite_values)
            if constraint.validate_value(option_value):
                continue
            if isinstance(constraint, SizeConstraint) or isinstance(constraint, TimeConstraint) or isinstance(constraint, SpeedConstraint):
                num_constraint = NumberConstraint()
                if num_constraint.validate_value(option_value):
                    detected_conflicts.append(ConstraintViolationConflict(artifact_node,option_node, node, num_constraint.constraint_type, False))
            else:
                detected_conflicts.append(ConstraintViolationConflict(artifact_node,option_node, node, constraint.constraint_type, False))

        return detected_conflicts
    
    def find_constraint_types(self, artifact_node: ArtifactNode):
        detected_constraint_dicts = self._get_constraint_dicts()        
        overwrite_values = None
        special_constraints: List[Optional[UserDefConstraint]] = []
        pn = PrettyNames()
        artifact_node.concept_name
        #Check if override is available
        if artifact_node.concept_name and len(detected_constraint_dicts) > 0:
            for constraint_dict in detected_constraint_dicts:
                if constraint_dict["concept"] == artifact_node.concept_name:
                    overwrite_values = constraint_dict
                    special_constraints = self._init_special_constraint(overwrite_values)
        constraints_templates = set()
        value_nodes = artifact_node.get_nodes()
        for node in value_nodes:
            option_name = node.get_options()
            option_value = pn.gpn(artifact_node.concept_name, node.name)
            option_node = node.parent
            option_type = str(node.parent.config_type).split(".")[-1]

            constraint = self.get_responsible_constraint_type(option_type)
            for special_constraint in special_constraints:
                if special_constraint.is_responsible(option_name):
                    constraint = special_constraint
                    break
            if constraint == None:
                continue
            if overwrite_values:
                self._overwrite_values(constraint, overwrite_values)
            if constraint.validate_value(option_value):
                constraints_templates.add(ConstraintTemplate(artifact_node, option_node, node, constraint.constraint_type))
                continue
            if isinstance(constraint, SizeConstraint) or isinstance(constraint, TimeConstraint) or isinstance(constraint, SpeedConstraint):
                num_constraint = NumberConstraint()
                if num_constraint.validate_value(option_value):
                    constraints_templates.add(ConstraintTemplate(artifact_node, option_node, node, num_constraint.constraint_type))   
            else:
                constraints_templates.add(ConstraintTemplate(artifact_node, option_node, node, "UNKNOWN"))
        return constraints_templates
        
    def _get_constraint_dicts(self):
        dictionarys = []
        path = Path(
            __file__).parent / "../constraints/constraint_dicts/"
        for constraint_dict in os.listdir(path):
            if constraint_dict.endswith(".json"):
                with open(path / constraint_dict, "r") as constraint_dict_file:
                    dictionarys.append(json.load(constraint_dict_file))
        return dictionarys
    
    def _overwrite_values(self, constraint: Constraint, overwrite_values: dict):
        types_to_overwrite = overwrite_values["constraint_types"]
        for constraint_type in types_to_overwrite.keys():
            if constraint.constraint_type == constraint_type:
                for value_option in types_to_overwrite[constraint_type]:                    
                    option = value_option
                    value = types_to_overwrite[constraint_type][value_option]
                    constraint.overwrite_value(option, value)

    def _init_special_constraint(self, overwrite_values):
        special_constraints = []
        if "special_type" in overwrite_values.keys():
            special_type_keys = overwrite_values["special_type"].keys()
            for special_type in special_type_keys:
                special_constraint = UserDefConstraint()
                special_type_attributes = overwrite_values["special_type"][special_type].keys()
                for attribut in special_type_attributes:
                    special_constraint.overwrite_value(attribut, overwrite_values["special_type"][special_type][attribut])
                special_constraints.append(special_constraint)
                
        return special_constraints