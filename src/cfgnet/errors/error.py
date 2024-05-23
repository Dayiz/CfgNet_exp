from typing import Optional, Set, TYPE_CHECKING

class Error():
    def __init__(
        self,
        line_number : int,
        file_path : str,
        wrong_value : Optional[str] = None,
        correct_value : Optional[str] = None,
        conflict_id : Optional[str] = None
    ):
        self.line_number = line_number
        self.file_path = file_path
        self.wrong_value = wrong_value
        self.correct_value = correct_value
        self.conflict_id = conflict_id
    
