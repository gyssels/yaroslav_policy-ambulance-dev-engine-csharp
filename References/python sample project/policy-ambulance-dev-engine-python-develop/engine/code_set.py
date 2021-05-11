from typing import Set

class CodeSet:
    def __init__(self, name: str, codes: Set[str]):
        self.name = name
        self.codes = codes

class TransportKind:
    def __init__(self, transport_code_set: CodeSet, mileage_code: str, transport_title: str):
        self.transport_code_set = transport_code_set
        self.mileage_code = mileage_code
        self.transport_title = transport_title
