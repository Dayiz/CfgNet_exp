#from cfgnet.network.nodes import ArtifactNode, OptionNode, ValueNode

class ConstraintTemplate:
    def __init__(self, 
                artifact,
                option,
                value,
                constraint_type:str
    ) -> None:
        self.artifact = artifact
        self.option = option
        self.value = value
        self.constraint_type = constraint_type

    def __hash__(self):
        if hasattr(self, 'artifact') and hasattr(self, 'option') and hasattr(self, 'constraint_type'): 
            if hasattr(self.artifact, 'file_path') and hasattr(self.option, 'display_option_id'):
                obj_hash = hash("|".join([self.artifact.file_path,self.option.display_option_id,self.constraint_type]))
                return obj_hash
            obj_hash = hash("|".join([str(id(self.artifact)),str(id(self.option)),str(id(self.constraint_type))]))
            return obj_hash
        else:
            obj_hash = hash(id(self))
            return obj_hash

    def __str__(self) -> str:
        return f"File: {self.artifact.rel_file_path}\nConstraint Change for Option '{self.option.display_option_id}', Value used to be {self.value.name} and satisfied {self.constraint_type}-type."

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

    