from typing import Optional


class LeafConfiguration:
    def __init__(self, user_id: Optional[str] = None, password: Optional[str] = None, region: Optional[str] = None):
        self.user_id = user_id
        self.password = password
        self.region = region


class LeafSoc:
    def __init__(self,
                 name: str = "Nissan Leaf/NV200 -05.2019 (experimental)",
                 type: str = "leaf",
                 configuration: LeafConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or LeafConfiguration()
