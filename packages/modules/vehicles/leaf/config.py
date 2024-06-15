from typing import Optional


class LeafConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None):
        self.user_id = user_id
        self.password = password


class LeafSoc:
    def __init__(self,
                 name: str = "Leaf",
                 type: str = "leaf",
                 configuration: LeafConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or LeafConfiguration()
