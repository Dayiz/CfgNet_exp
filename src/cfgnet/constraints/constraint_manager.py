from typing import List, Set, Optional

from cfgnet.constraints.constraint_detector import ConstraintDetector
from cfgnet.network.nodes import ArtifactNode
from cfgnet.plugins.plugin_manager import PluginManager
from cfgnet.constraints.constraint import *
from cfgnet.conflicts.conflict import ConstraintViolationConflict
#from cfgnet.constraints.constraint_types import *

class ConstraintManager():

    def _get_responsible_concept(self, artifact_node: ArtifactNode):
        plugins = PluginManager.get_plugins()
        plugin = PluginManager.get_responsible_plugin(
                plugins, artifact_node.file_path
            )
        if plugin:
            return plugin.concept_name
        return None

    def check_constraints(self, artifact_node):
        cd = ConstraintDetector()
        return cd.check_constraints(artifact_node)
    
    def compare_constraints(self, old_constraints: set, new_constraints:set):
        conflicts = old_constraints.difference(new_constraints)
        return conflicts
    
    def get_option_constraint_type(self, network):                
        artifact_node_list = network.get_nodes(ArtifactNode)
        if (len(artifact_node_list) < 1):
            return
        #if nodelist exist, get the pairs for each artifact
        return_set: Set = set()
        for artifact_node in artifact_node_list:
            cd = ConstraintDetector()
            result_set = cd.find_constraint_types(artifact_node)
            for result in result_set:
                return_set.add(result)
        return return_set
    
    def convert_templates_to_conflicts(self, old_templates: set, new_templates: set):
        difference = old_templates.difference(new_templates)
        conflict_set = set()
        for diff in difference:
            artifact = diff.artifact
            old_value = diff.value
            old_constraint = str(diff.value.config_type).split(".")[-1]
            value_created = False
            for elem in new_templates:
                if (str(diff.artifact.file_path) + str (diff.option.display_option_id)) == (str(elem.artifact.file_path) + str (elem.option.display_option_id)):
                    option = elem.option
                    new_value = elem.value
                    new_constraint = elem.constraint_type
                    conflict_set.add(ConstraintViolationConflict(artifact, option, new_value, new_constraint, True, old_value, old_constraint))
                    value_created = True
                    break
            if not value_created:
                logging.error(f"Error while creating ConstraintViolationConflict for {diff}")
            
        return conflict_set