import re
from typing import List, Dict
from ._core import ctypes_map


def camelcase(name):
    name = re.sub(r"_", " ", name)
    pieces = [s.title() for s in name.split(sep=" ")]
    return "".join(pieces)


def preprocess(text: str) -> str:
    # Strip Inline Comments
    text = re.sub(r"//(.*)\n", r"\n", text)

    # Strip Block Comments
    text = re.sub(r"/\*(.*)\*/", r"\n", text, flags=re.DOTALL)

    # Strip Tabs
    text = re.sub(r"\t+", " ", text)

    return text


def parse_defines(text: str) -> Dict:
    defines = {}
    defines["MT"] = {}
    defines["MID"] = {}
    defines["constants"] = {}

    # Get Defines (Only simple one line constants here)
    macros = re.findall(
        r"#define\s*(?P<name>\w+)\s+(?P<expression>[\(\)\[\]\w \*/\+-]+)\n", text
    )

    for name, exp in macros:
        name = name.strip()
        exp = exp.strip()

        # Store a mapping for each define type
        if name.startswith("MT_"):
            defines["MT"][name] = exp
        elif name.startswith("MID_"):
            defines["MID"][name] = exp
        else:
            defines["constants"][name] = exp

    return defines


def parse_typedefs(text: str) -> Dict:
    # Get simple typedefs
    typedefs = {}
    c_typedefs = re.findall(r"\s*typedef\s*((?:\w+\s+)+)(\w+)\s*;", text)

    for typ, alias in c_typedefs:
        if alias.startswith("MDF_"):
            # TODO:Non struct message defintion. Maybe drop support?
            pass
        else:
            # Must typedef a native type
            ctype = ctypes_map[typ.strip()]

            # Create another alias for the native type
            typedefs[alias.strip()] = ctype

    return typedefs


def parse_structs(msg_types, text: str) -> Dict:
    structs = {}

    # Strip Newlines
    text = re.sub(r"\n", "", text)

    # Get Struct Definitions
    c_msg_defs = re.finditer(
        r"typedef\s*struct\s*\{(?P<def>[\s\w;\[\]]*)\}(?P<name>[\s\w]*);", text
    )

    for m in c_msg_defs:
        name = m.group("name").strip()
        # struct_name = camelcase(name.replace("MDF_", ""))

        fields = m.group("def").split(sep=";")
        fields = [f.strip() for f in fields if f.strip() != ""]

        c_fields = []
        for field in fields:
            field_type, field_name = field.rsplit(sep=" ", maxsplit=1)
            fmatch = re.match(r"(?P<name>\w*)(\[(?P<length>.*)\])?", field_name)

            if fmatch is None:
                raise RuntimeError("Error parsing field definition.")

            # Field name
            fname = fmatch.group("name").strip()
            ftype = field_type.strip()

            t = ctypes_map.get(ftype)
            if t:
                ftype = f"{t.__module__}.{t.__name__}"

            flen = fmatch.group("length") or None
            c_fields.append((fname, ftype, flen))

        structs[name] = c_fields

    # Add a placeholder for signal definitions
    for msg_type in msg_types.keys():
        if msg_type.startswith("MT_"):
            structs.setdefault("MDF_" + msg_type[3:], None)

    return structs


def generate_constant(name, value):
    return f"{name} = {value}"


def generate_struct(name: str, fields):
    assert not name.startswith("MDF_")

    f = []
    fnum = len(fields)
    for i, (fname, ftyp, flen) in enumerate(fields, start=1):
        nl = ",\n" if i < fnum else ""
        f.append(f"        (\"{fname}\", {ftyp}{' * ' + flen if flen else ''}){nl}")

    fstr = "".join(f)

    template = f"""
class {name}(ctypes.Structure):
    _pack_ = True
    _fields_ = [
{fstr}
    ]

"""
    return template


def generate_msg_def(name: str, fields):
    assert name.startswith("MDF_")

    basename = name[4:]
    f = []
    fnum = len(fields)
    for i, (fname, ftyp, flen) in enumerate(fields, start=1):
        nl = ",\n" if i < fnum else ""
        f.append(f"        (\"{fname}\", {ftyp}{' * ' + flen if flen else ''}){nl}")

    fstr = "".join(f)

    msg_id = "MT_" + basename
    template = f"""
class {name}(MessageData):
    _pack_ = True
    _fields_ = [
{fstr}
    ]
    type_id = {msg_id}
    type_name = \"{basename}\"


user_msg_defs[{msg_id}] = {name}

"""
    return template


def generate_sig_def(name: str):
    assert name.startswith("MDF_")
    basename = name[4:]
    msg_id = "MT_" + basename
    template = f"""
# Signal Definition
class {name}(MessageData):
    _pack_ = True
    _fields_ = []
    type_id = {msg_id}
    type_name = \"{basename}\"


user_msg_defs[{msg_id}] = {name}

"""
    return template


def parse_file(filename, seq: int = 1):
    """Parse a C header file for message definitions.
    Notes:
        * Does not follow other #includes
        * Parsing order: #defines, typedefs, typedef struct
    """

    with open(filename, "r") as f:
        text = f.read()

    text = preprocess(text)
    defines = parse_defines(text)
    typedefs = parse_typedefs(text)
    structs = parse_structs(defines["MT"], text)

    if seq == 1:
        print("import ctypes")
        print("from pylsb import *")
        print()

    print(f"# User Constants: {filename}")
    for name, value in defines["constants"].items():
        print(generate_constant(name, value))

    print()
    print(f"# User Message IDs: {filename}")
    for name, value in defines["MT"].items():
        print(generate_constant(name, value))

    print()
    print(f"# User Module IDs: {filename}")
    for name, value in defines["MID"].items():
        print(generate_constant(name, value))

    print()
    print(f"# User Type Definitions: {filename}")
    for name, value in typedefs.items():
        print(generate_constant(name, value))

    ctypes_map.update(typedefs)

    print()
    print(f"# User Message Definitions: {filename}", end="\n\n")

    for name, fields in structs.items():
        if name.startswith("MDF_"):
            if fields is not None:
                print(generate_msg_def(name, fields), end="")
            else:
                print(generate_sig_def(name), end="")
        else:
            print(generate_struct(name, fields), end="")


def compile(include_files: List):
    for n, f in enumerate(include_files, start=1):
        parse_file(f, seq=n)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="LabSwitchBoard Message Definition Compiler."
    )

    parser.add_argument(
        "-i, -I", nargs="*", dest="include_files", help="Files to parse",
    )
    args = parser.parse_args()
    compile(args.include_files)
