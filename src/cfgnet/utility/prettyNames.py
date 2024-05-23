class PrettyNames():
    def __init__(self) -> None:
        pass

    def gpn(self, concept_name, name):
        if(concept_name == "tsconfig" or concept_name == "nodejs"):
            if "http://" in name or "https://" in name:
                name_split = name.split(":")
                return str(name_split[-2]+":"+name_split[-1])
            if ":" in name:
                return name.split(":")[-1]
        if concept_name == "poetry":
            if "http" in name:
                return name.split(":")[-2] + ":" + name.split(":")[-1]
            return name
        if concept_name == "maven":
            if "http" in name:
                return name
            if ":" in name:
                return name.split(":")[-1]
            return name
        if concept_name == "":
            return name
        
        """
        if concept_name == "":
            return name
        if concept_name == "":
            return name
        if concept_name == "":
            return name
        if concept_name == "":
            return name
        if concept_name == "":
            return name
        """
        return name
        