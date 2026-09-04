from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArgIR:
    name: str
    type: str
    default: str | None
    description: str
    kind: str = "regular"


@dataclass
class ReturnIR:
    type: str
    description: str


@dataclass
class RaiseIR:
    exception: str
    description: str


@dataclass
class VarIR:
    name: str
    type: str
    value: str
    description: str


@dataclass
class DocstringIR:
    short_description: str
    long_description: str = ""
    examples: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class FunctionIR:
    name: str
    args: list[ArgIR]
    returns: ReturnIR | None
    raises: list[RaiseIR]
    decorators: list[str]
    docstring: DocstringIR
    is_async: bool
    source_file: str
    line_number: int
    kind: str = "function"


@dataclass
class ClassIR:
    name: str
    bases: list[str]
    decorators: list[str]
    docstring: DocstringIR
    methods: list[FunctionIR]
    class_vars: list[VarIR]
    inner_classes: list[ClassIR] = field(default_factory=list)
    source_file: str = ""
    line_number: int = 0


@dataclass
class ModuleIR:
    name: str
    docstring: DocstringIR
    classes: list[ClassIR]
    functions: list[FunctionIR]
    constants: list[VarIR]
    source_file: str
