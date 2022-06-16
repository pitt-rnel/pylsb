import re
import ctypes
import ast
from typing import List
from collections import defaultdict
from .internal_types import RTMA, __msg_data_print__


type_map = {
    "char": ctypes.c_char,
    "unsigned char": ctypes.c_ubyte,
    "byte": ctypes.c_char,
    "int": ctypes.c_int,
    "signed int": ctypes.c_uint,
    "unsigned int": ctypes.c_uint,
    "short": ctypes.c_short,
    "signed short": ctypes.c_short,
    "unsigned short": ctypes.c_ushort,
    "long": ctypes.c_long,
    "signed long": ctypes.c_long,
    "unsigned long": ctypes.c_ulong,
    "long long": ctypes.c_longlong,
    "signed long long": ctypes.c_longlong,
    "unsigned long long": ctypes.c_ulonglong,
    "float": ctypes.c_float,
    "double": ctypes.c_double,
}


def camelcase(name):
    name = re.sub(r"_", " ", name)
    pieces = [s.title() for s in name.split(sep=" ")]
    return "".join(pieces)


def expand(token: str, defines):
    return defines["constants"].get(token) or RTMA.constants.get(token) or token


def expand_expression(expression: str, defines):
    if not any((c in ("*+-/") for c in expression)):
        return str(expand(expression, defines))

    # Get any names in the expression
    tokens = [
        node.id
        for node in ast.walk(ast.parse(expression))
        if isinstance(node, ast.Name)
    ]

    if len(tokens) == 0:
        return expression

    for token in tokens:
        expression = re.sub(token, str(expand(token, defines)), expression)

    return expression


def parse_defines(text: str):
    defines = {}
    defines["MT"] = {}
    defines["MID"] = {}
    defines["constants"] = {}
    defines["expressions"] = {}

    # Get Defines (Only simple one line constants here)
    c_defines = re.findall(r"#define\s*(\w+)\s+([\(\)\[\]\w \*/\+-]+)\n", text)

    for name, expression in c_defines:
        name = name.strip()
        expression = expression.strip()

        while True:
            expanded_expression = expand_expression(expression, defines)
            if expression == expanded_expression:
                break
            expression = expanded_expression

        if re.search(r"[a-zA-Z]", expanded_expression):
            value = expanded_expression
        else:
            value = eval(expanded_expression)

        if name.startswith("MT_"):
            defines["MT"][camelcase(name.replace("MT_", ""))] = value
        elif name.startswith("MID_"):
            defines["MID"][name.replace("MID_", "")] = value
        else:
            defines["constants"][name] = value

        defines["expressions"][name] = expanded_expression

    return defines


def parse_typedefs(text: str):
    # Get simple typedefs
    typedefs = {}
    c_typedefs = re.findall(r"\s*typedef\s*((?:\w+\s+)+)(\w+)\s*;", text)
    for typ, alias in c_typedefs:
        if alias.startswith("MDF_"):
            # TODO:Non struct message defintion. Maybe drop support?
            pass
        else:
            typedefs[alias.strip()] = typ.strip()

    return typedefs


def parse_structs(text: str):
    structs = defaultdict(list)
    # Strip Newlines
    text = re.sub(r"\n", "", text)

    # Get Struct Definitions
    c_msg_defs = re.finditer(
        r"typedef\s*struct\s*\{(?P<def>[\s\w;\[\]]*)\}(?P<name>[\s\w]*);", text
    )

    for m in c_msg_defs:
        name = m.group("name").strip()
        struct_name = camelcase(name.replace("MDF_", ""))

        fields = m.group("def").split(sep=";")
        fields = [f.strip() for f in fields if f.strip() != ""]

        for field in fields:
            field_type, field_name = field.rsplit(sep=" ", maxsplit=1)
            fmatch = re.match(r"(?P<name>\w*)(\[(?P<length>.*)\])?", field_name)

            if fmatch is None:
                raise RuntimeError("Error parsing field definition.")

            # Field name
            fname = fmatch.group("name").strip()
            ftype = field_type.strip()
            flen = fmatch.group("length") or None

            if flen:
                try:
                    flen = int(flen)
                except ValueError:
                    pass

            structs[struct_name].append((fname, ftype, flen))

    return structs


def get_type(type_spec, typedefs, msg_defs):
    t = type_map.get(type_spec)
    if t:
        return t

    t = msg_defs.get(camelcase(type_spec))
    if t:
        return t

    t = RTMA.msg_defs.get(camelcase(type_spec))
    if t:
        return t

    # try a typedef alias
    s = typedefs.get(type_spec)

    if s:
        t = type_map.get(s)
        if t:
            return t

        t = msg_defs.get(camelcase(s))
        if t:
            return t

        t = RTMA.msg_defs.get(camelcase(type_spec))
        if t:
            return t

    print(f"Unable to map type {type_spec}.")
    raise KeyError(f"Unable to map type {type_spec}.")


def create_ctypes(defines, typedefs, structs):
    msg_defs = {}

    for msg_name, fields in structs.items():
        ctypes_fields = []
        for fname, ftype, flen in fields:
            # Parse array lengths if required
            if isinstance(flen, str):
                expression = flen.strip()

                while True:
                    expanded_expression = expand_expression(expression, defines)
                    if expression == expanded_expression:
                        break
                    expression = expanded_expression

                # Should only have a numeric value here
                if re.search(r"[a-zA-Z]", expanded_expression):
                    raise RuntimeError(
                        "Array length expression was not fully expanded."
                    )
                else:
                    flen = eval(expanded_expression)

            if flen:
                ctypes_fields.append(
                    (fname, get_type(ftype, typedefs, msg_defs) * flen)
                )
            else:
                ctypes_fields.append((fname, get_type(ftype, typedefs, msg_defs)))

            msg_defs[msg_name] = type(
                msg_name, (ctypes.Structure,), {"_fields_": ctypes_fields}
            )

    return msg_defs


def parse_file(filename):
    """Parse a C header file for message definitions.
    Notes:
        * Does not follow other #includes
        * Parsing order: #defines, typedefs, typedef struct
    """

    with open(filename, "r") as f:
        text = f.read()

    # Strip Inline Comments
    text = re.sub(r"//.*\n", "\n", text)

    # Strip Block Comments
    text = re.sub(r"/\*.*\*/", "\n", text)

    # Strip Tabs
    text = re.sub(r"\t+", " ", text)

    defines = parse_defines(text)
    typedefs = parse_typedefs(text)
    structs = parse_structs(text)
    msg_defs = create_ctypes(defines, typedefs, structs)

    # Only update the module after we are done parsing
    RTMA.MT.update(defines["MT"])
    RTMA.MID.update(defines["MID"])
    RTMA.constants.update(defines["constants"])
    RTMA.typedefs.update(typedefs)
    RTMA.structs.update(structs)
    RTMA.msg_defs.update(msg_defs)

    for msg_name, msg_def in msg_defs.items():
        setattr(msg_def, "__repr__", __msg_data_print__)

    return (defines, typedefs, structs, msg_defs)


def parse_files(include_files: List):
    for f in include_files:
        parse_file(f)
