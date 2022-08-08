import re
import ctypes
from typing import List, Dict, Tuple
from collections import defaultdict
from .internal_types import LSB, __msg_data_print__


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


def preprocess(text: str) -> Tuple[str, Dict]:
    # Strip Inline Comments
    text = re.sub(r"//.*\n", "\n", text)

    # Strip Block Comments
    text = re.sub(r"/\*.*\*/", "\n", text)

    # Strip Tabs
    text = re.sub(r"\t+", " ", text)

    # Find and replace all previously defined constants
    for constant, value in LSB.constants.items():
        text = re.sub(r"\b" + re.escape(constant) + r"\b", str(value), text)

    # Get Defines (Only simple one line constants here)
    macros = re.findall(r"#define\s*(\w+)\s+([\(\)\[\]\w \*/\+-]+)\n", text)

    # Expand all the macros
    for n, (macro, expression) in enumerate(macros):
        for m, (other_macro, other_expression) in enumerate(macros[n:]):
            macros[m + n] = (
                other_macro,
                re.sub(r"\b" + re.escape(macro) + r"\b", expression, other_expression),
            )

    defines = {}
    defines["MT"] = {}
    defines["MID"] = {}
    defines["constants"] = {}

    for n, (macro, expression) in enumerate(macros):
        # Evaluate the expression
        if re.search(r"[a-zA-Z]", expression):
            value = expression
        else:
            value = eval(expression)

        # Find and replace all defines in file with macro value
        count = -1

        def repl(match):
            nonlocal count
            count += 1
            # Skip first match
            if count == 0:
                return match.group(0)
            else:
                return str(value)

        text = re.sub(r"\b" + re.escape(macro) + r"\b", repl, text)

        # Store a mapping for each define type
        if macro.startswith("MT_"):
            defines["MT"][camelcase(macro.replace("MT_", ""))] = value
        elif macro.startswith("MID_"):
            defines["MID"][macro.replace("MID_", "")] = value
        else:
            defines["constants"][macro] = value

    return text, defines


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

            # Parse array lengths if required
            if flen:
                if isinstance(flen, str):
                    expression = flen.strip()
                    # Should only have a numeric value or expression here
                    if re.search(r"[a-zA-Z]", expression):
                        raise RuntimeError(
                            "Array length expression was not fully expanded."
                        )
                    else:
                        flen = eval(expression)

            structs[struct_name].append((fname, ftype, flen))

    return structs


def get_type(type_spec, typedefs, msg_defs):
    t = type_map.get(type_spec)
    if t:
        return t

    t = msg_defs.get(camelcase(type_spec))
    if t:
        return t

    t = LSB.msg_defs.get(camelcase(type_spec))
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

        t = LSB.msg_defs.get(camelcase(type_spec))
        if t:
            return t

    print(f"Unable to map type {type_spec}.")
    raise KeyError(f"Unable to map type {type_spec}.")


def create_ctypes(typedefs, structs):
    msg_defs = {}

    for msg_name, fields in structs.items():
        ctypes_fields = []
        for fname, ftype, flen in fields:
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

    text, defines = preprocess(text)
    typedefs = parse_typedefs(text)
    structs = parse_structs(text)
    msg_defs = create_ctypes(typedefs, structs)

    # Only update the module after we are done parsing
    LSB.MT.update(defines["MT"])
    LSB.MID.update(defines["MID"])
    LSB.constants.update(defines["constants"])
    LSB.typedefs.update(typedefs)
    LSB.structs.update(structs)
    LSB.msg_defs.update(msg_defs)

    for msg_name, msg_def in msg_defs.items():
        setattr(msg_def, "__repr__", __msg_data_print__)

    return (defines, typedefs, structs, msg_defs)


def parse_files(include_files: List):
    for f in include_files:
        parse_file(f)
