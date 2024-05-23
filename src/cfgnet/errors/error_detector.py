from cfgnet.errors.error import Error
from cfgnet.conflicts.conflict import Conflict, ModifiedOptionConflict, ConstraintViolationConflict
from typing import List, Set, Optional

class ErrorDetector:

    @staticmethod        
    def get_errors_from_conflicts(conflicts: set, replace_old: bool = False) -> Optional[Set[Error]]:
        """
        Detect errors with respect to the reference network.
        :return: Set of detected errors
        """
        errors: Set = set()

        for conflict in conflicts:
            created_error = ErrorDetector._create_error_from_conflict(conflict, replace_old)
            if created_error != None:
                errors.add(created_error)
                
        if len(errors) == 0:
            return None
        return errors
    
    @staticmethod    
    def _create_error_from_conflict(conflict: Conflict, replace_old: bool = False) -> Optional[List[Error]]:
        if type(conflict) == ModifiedOptionConflict:
            if not replace_old:
                line_number = conflict.option.location
                file_path = conflict.artifact.file_path
                wrong_value = str(conflict.value.name)[
                    str(conflict.value.name).find(":") + 1:]
                correct_value = str(conflict.old_value.name)[
                    str(conflict.old_value.name).find(":") + 1:]
                return Error(line_number, file_path, wrong_value, correct_value, conflict.id)
            else:
                errorlist = []
                for dependent_artifact, dependent_option in conflict.dependents:
                    line_number = dependent_option.location
                    file_path = dependent_artifact.file_path
                    wrong_value = str(conflict.old_value.name)[
                        str(conflict.old_value.name).find(":") + 1:]
                    correct_value = str(conflict.value.name)[
                        str(conflict.value.name).find(":") + 1:]
                    errorlist.append(Error(line_number, file_path, wrong_value, correct_value, conflict.id))
                return errorlist
        if type(conflict) == ConstraintViolationConflict:
            try:
                line_number = int(conflict.option.location)
            except:
                return None
            file_path = conflict.artifact.file_path
            wrong_value = conflict.new_value.name
            if(isinstance(conflict.old_value, str)):
                correct_value = conflict.old_value
            else:
                correct_value = conflict.old_value.name
            return Error(line_number, file_path, wrong_value, correct_value)