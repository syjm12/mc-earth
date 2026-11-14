"""Write minimal 1.21.1 StructureTemplate (.nbt) files for the Ponder scenes.

Ponder places the schematic at the scene origin and uses it as the subject of
the animations. Without a file, PonderSceneRegistry.loadSchematic() logs an
error and the scene renders on an empty base plate.

The files are plain gzipped NBT:
  { size:[I;..], palette:[{Name,Properties}], blocks:[{pos:[I;..],state:int}],
    entities:[], DataVersion:int }
"""
import gzip
import io
import os
import struct

TAG_END, TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG = 0, 1, 2, 3, 4
TAG_FLOAT, TAG_DOUBLE, TAG_BYTE_ARRAY, TAG_STRING = 5, 6, 7, 8
TAG_LIST, TAG_COMPOUND, TAG_INT_ARRAY, TAG_LONG_ARRAY = 9, 10, 11, 12

DATA_VERSION_1_21_1 = 3955


def _s(text):
    raw = text.encode("utf-8")
    return struct.pack(">H", len(raw)) + raw


def _tag(id_, name, payload):
    return bytes([id_]) + _s(name) + payload


def nbt_string(name, value):
    return _tag(TAG_STRING, name, _s(value))


def nbt_int(name, value):
    return _tag(TAG_INT, name, struct.pack(">i", value))


def nbt_int_array(name, values):
    return _tag(TAG_INT_ARRAY, name, struct.pack(">i", len(values)) + b"".join(struct.pack(">i", v) for v in values))


def nbt_compound(name, payload):
    return _tag(TAG_COMPOUND, name, payload + bytes([TAG_END]))


def nbt_list(name, elem_type, payloads):
    return _tag(TAG_LIST, name, struct.pack(">b", elem_type) + struct.pack(">i", len(payloads)) + b"".join(payloads))


def structure_nbt(size, palette, blocks, data_version=DATA_VERSION_1_21_1):
    """size = (x,y,z); palette = [(name, {prop: value} | None)]; blocks = [((x,y,z), index)]."""
    palette_payloads = []
    for name, props in palette:
        body = nbt_string("Name", name)
        if props:
            inner = b"".join(nbt_string(k, v) for k, v in sorted(props.items()))
            body += nbt_compound("Properties", inner)
        palette_payloads.append(body + bytes([TAG_END]))

    block_payloads = []
    for pos, state in blocks:
        body = nbt_int_array("pos", list(pos)) + nbt_int("state", state)
        block_payloads.append(body + bytes([TAG_END]))

    root = b""
    root += nbt_int("DataVersion", data_version)
    root += nbt_list("entities", TAG_COMPOUND, [])
    root += nbt_list("blocks", TAG_COMPOUND, block_payloads)
    root += nbt_list("palette", TAG_COMPOUND, palette_payloads)
    root += nbt_int_array("size", list(size))
    root += bytes([TAG_END])

    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(_tag(TAG_COMPOUND, "", root))
    return buf.getvalue()


FLOOR = "minecraft:stone_bricks"


def build(size_x, size_z, center_block, props):
    """A stone-brick platform with one machine block in the middle."""
    palette = [(FLOOR, None), (center_block, props or None)]
    blocks = []
    cx, cz = size_x // 2, size_z // 2
    for x in range(size_x):
        for z in range(size_z):
            blocks.append(((x, 0, z), 0))
    blocks.append(((cx, 1, cz), 1))
    return structure_nbt((size_x, 2, size_z), palette, blocks)


def write_all(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    scenes = {
        "planetary_engine": ("wandering_earth:planetary_engine_core",
                             {"facing": "south", "lit": "true"}),
        "lighter_socket": ("wandering_earth:lighter_socket",
                           {"facing": "south", "lit": "false"}),
        "moss_mainframe": ("wandering_earth:moss_mainframe", None),
    }
    written = []
    for name, (block, props) in scenes.items():
        data = build(5, 5, block, props)
        path = os.path.join(out_dir, name + ".nbt")
        with open(path, "wb") as fh:
            fh.write(data)
        written.append((path, len(data)))
    return written


if __name__ == "__main__":
    for path, size in write_all(r"D:\money\wandering-earth\src\main\resources\assets\wandering_earth\ponder"):
        print(path, size)
