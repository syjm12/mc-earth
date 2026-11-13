"""Regression checks for the offline-built mod jar.

Why this exists
---------------
`tools/build_offline.py` compiles the mod against *compile-time-only* stubs for
`net.minecraft.*` (the real classes are shipped with the game, not in a jar we
can put on javac's classpath). A stub that gets the **kind** of a class wrong
(declaring an interface as a `class`, or the other way round) still compiles
perfectly -- javac just emits `invokevirtual` where the real JVM expects
`invokeinterface` -- and only explodes at runtime:

    java.lang.IncompatibleClassChangeError:
        Found class net.minecraft.network.chat.MutableComponent,
        but interface was expected
        at com.wanderingearth.block.ModBlock.appendHoverText(ModBlock.java:48)

That was the v1.0.0 bug. This script catches that whole family of mistakes
before the game runs, by comparing our compiled bytecode against the real
obfuscated 1.21.1 classes (translated with Mojang's official mappings).

Checks
------
  1. invoke kind      -- invokevirtual/invokespecial vs invokeinterface must
                         agree with the real class kind   (IncompatibleClassChangeError)
  2. member linkage   -- every method/field reference must exist on the real
                         class or one of its supertypes      (NoSuchMethodError /
                                                              NoSuchFieldError)
  3. override shape   -- a method of ours whose name exists in the real super
                         chain must have a matching descriptor, else the game
                         never calls it (silent dead code, no exception)
  4. stub leak        -- the jar must contain no net/minecraft or com/mojang
                         classes (the stubs must not ship)

Usage
-----
    python tools/verify_jar.py --jar prebuilt/wandering_earth-1.0.0.jar \
        --mappings  /path/to/client.txt \
        --vanilla   /path/to/1.21.1/client.jar \
        --cp-dir    /path/to/neoforge-jars

`client.txt` is Mojang's official 1.21.1 client mapping:
  https://piston-data.mojang.com/v1/objects/2244b6f072256667bcd9a73df124d6c58de77992/client.txt
`client.jar` is https://piston-data.mojang.com/v1/objects/30c73b1c5da787909b2f73340419fdf13b9def88/client.jar
`--cp-dir` is any directory containing neoforge-*-universal.jar plus the Fancy
Mod Loader jars (loader, bus, coremods, ...) from the same NeoForge version.

Exit code 0 means all four checks passed.
"""
import argparse
import io
import os
import re
import struct
import sys
import zipfile

ACC_INTERFACE, ACC_ENUM = 0x0200, 0x4000

CLASS_RE = re.compile(r"^(\S+) -> (\S+):$")
MEM_RE = re.compile(r"^\s+(?:-?\d+:-?\d+:)?(\S+) ([^(\s]+)\(([^)]*)\) -> (\S+)$")
FLD_RE = re.compile(r"^\s+(\S+) ([^(\s]+) -> (\S+)$")

PRIMS = {"void": "V", "boolean": "Z", "byte": "B", "char": "C", "short": "S",
         "int": "I", "long": "J", "float": "F", "double": "D"}


# ---------------------------------------------------------------- mappings
class Mappings:
    """Official Mojang ProGuard-style mapping file.

    Format::

        net.minecraft.world.level.block.Block -> dfy:
            net.minecraft.world.level.block.Block$Properties <init> -> <init>
            12:34:void method(java.lang.String) -> a
            net.minecraft.core.Registry field -> b

    Note the descriptors in that file are written with *dots*
    (``Ljava.lang.String;``) while real bytecode uses slashes -- that mismatch
    produced 50 false "NoSuchMethodError"s before it was fixed, so it is handled
    in `type_desc`.
    """

    def __init__(self, path):
        self.obf_to_deobf = {}
        self.deobf_to_obf = {}
        self.member_map = {}   # obf owner -> {obf member name: [(deobf name, desc)]}
        self.field_map = {}    # obf owner -> {obf field name: [(deobf name, desc)]}
        cur = None
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                if line.lstrip().startswith("#"):   # e.g. # {"fileName":"Block.java"}
                    continue
                if not line.startswith((" ", "\t")):
                    m = CLASS_RE.match(line)
                    if m:
                        deobf, obf = m.group(1), m.group(2)
                        self.obf_to_deobf[obf] = deobf
                        self.deobf_to_obf[deobf] = obf
                        cur = obf
                        self.member_map.setdefault(obf, {})
                        self.field_map.setdefault(obf, {})
                    else:
                        cur = None
                    continue
                if cur is None:
                    continue
                m = MEM_RE.match(line)
                if m:
                    ret, name, params, obf_name = m.groups()
                    pts = [t for t in params.split(",") if t]
                    desc = "(" + "".join(type_desc(t) for t in pts) + ")" + type_desc(ret)
                    # obfuscated names collide across overloads -> keep every entry
                    self.member_map[cur].setdefault(obf_name, []).append((name, desc))
                    continue
                m = FLD_RE.match(line)
                if m:
                    ftype, name, obf_name = m.groups()
                    self.field_map[cur].setdefault(obf_name, []).append(
                        (name, type_desc(ftype)))


def type_desc(token):
    """`int` -> `I`; `java.lang.String` -> `Ljava/lang/String;`."""
    if not token:
        return ""
    if token in PRIMS:
        return PRIMS[token]
    if token.endswith("[]"):
        return "[" + type_desc(token[:-2])
    return "L" + token.replace(".", "/") + ";"


# ---------------------------------------------------------------- class file
class ClassFile:
    def __init__(self, data):
        b = io.BytesIO(data)
        if b.read(4) != b"\xca\xfe\xba\xbe":
            raise ValueError("not a class file")
        b.read(4)
        n = struct.unpack(">H", b.read(2))[0]
        cp = [None] * n
        i = 1
        while i < n:
            tag = b.read(1)[0]
            if tag == 1:
                ln = struct.unpack(">H", b.read(2))[0]
                cp[i] = ("utf8", b.read(ln).decode("utf-8", "replace"))
            elif tag == 7:
                cp[i] = ("class", struct.unpack(">H", b.read(2))[0])
            elif tag in (8, 16, 19, 20):
                b.read(2)
                cp[i] = ("x", None)
            elif tag == 15:
                b.read(3)
                cp[i] = ("mh", None)
            elif tag in (9, 10, 11):
                cp[i] = (tag, (struct.unpack(">H", b.read(2))[0],
                               struct.unpack(">H", b.read(2))[0]))
            elif tag == 12:
                cp[i] = ("nat", (struct.unpack(">H", b.read(2))[0],
                                 struct.unpack(">H", b.read(2))[0]))
            elif tag in (3, 4, 17, 18):
                b.read(4)
                cp[i] = ("num", None)
            elif tag in (5, 6):          # 8-byte constants take two slots
                b.read(8)
                cp[i] = ("num", None)
                i += 1
            else:
                raise ValueError("constant pool tag %d" % tag)
            i += 1
        self.cp = cp
        self.access = struct.unpack(">H", b.read(2))[0]
        self.this_i = struct.unpack(">H", b.read(2))[0]
        self.super_i = struct.unpack(">H", b.read(2))[0]
        ni = struct.unpack(">H", b.read(2))[0]
        self.ifaces = [struct.unpack(">H", b.read(2))[0] for _ in range(ni)]
        self.b = b
        self.fields = []
        self.methods = []
        self._read_members()

    def u(self):
        return struct.unpack(">H", self.b.read(2))[0]

    def name(self, idx):
        if not idx:
            return None
        e = self.cp[idx]
        if not e:
            return None
        if e[0] == "utf8":
            return e[1]
        if e[0] == "class":
            return self.cp[e[1]][1]
        return None

    def skip_attrs(self):
        for _ in range(self.u()):
            self.b.read(2)
            self.b.read(struct.unpack(">I", self.b.read(4))[0])

    def _read_members(self):
        for _ in range(self.u()):
            self.b.read(2)
            self.fields.append((self.name(self.u()), self.name(self.u())))
            self.skip_attrs()
        for _ in range(self.u()):
            acc = struct.unpack(">H", self.b.read(2))[0]
            mname, mdesc = self.name(self.u()), self.name(self.u())
            code = None
            for _ in range(self.u()):
                aname = self.name(self.u())
                alen = struct.unpack(">I", self.b.read(4))[0]
                blob = self.b.read(alen)
                if aname == "Code":
                    clen = struct.unpack(">I", blob[4:8])[0]
                    code = blob[8:8 + clen]
            self.methods.append((mname, mdesc, code, acc))

    def kind(self):
        if self.access & ACC_INTERFACE:
            return "interface"
        if self.access & ACC_ENUM:
            return "enum"
        return "class"


# ---------------------------------------------------------------- bytecode
CP2 = {0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xBB, 0xBD, 0xC0, 0xC1}
BR2 = set(range(0x99, 0xA9)) | {0xC6, 0xC7}
LOCAL = set(range(0x15, 0x1A)) | set(range(0x36, 0x3B)) | {0x10, 0x12, 0xA9, 0xBC}
WIDE2 = {0xB9, 0xBA, 0xC8, 0xC9}


def decode(bc):
    """Yield (offset, opcode, operand) with exact instruction widths.

    Exactness matters: one mis-sized instruction (invokedynamic is 5 bytes)
    desynchronises the stream and invents call sites that do not exist.
    """
    i, n = 0, len(bc)
    while i < n:
        op = bc[i]
        arg = None
        if op in (0xAA, 0xAB):                     # tableswitch / lookupswitch
            pad = (4 - ((i + 1) % 4)) % 4
            j = i + 1 + pad
            if op == 0xAA:
                low = struct.unpack(">i", bc[j + 4:j + 8])[0]
                high = struct.unpack(">i", bc[j + 8:j + 12])[0]
                i = j + 12 + (high - low + 1) * 4
            else:
                npairs = struct.unpack(">i", bc[j + 4:j + 8])[0]
                i = j + 8 + npairs * 8
            continue
        if op == 0xC4:                             # wide
            i += 6 if bc[i + 1] == 0x84 else 4
            continue
        if op in CP2:
            arg = (bc[i + 1] << 8) | bc[i + 2]
            w = 3
        elif op in WIDE2:
            arg = (bc[i + 1] << 8) | bc[i + 2]
            w = 5
        elif op == 0xC5:                           # multianewarray
            arg = (bc[i + 1] << 8) | bc[i + 2]
            w = 4
        elif op in BR2 or op == 0x11:              # branches / sipush
            arg = struct.unpack(">h", bc[i + 1:i + 3])[0]
            w = 3
        elif op == 0x84:                           # iinc
            arg = bc[i + 1]
            w = 3
        elif op in LOCAL:
            arg = bc[i + 1]
            w = 2
        else:
            w = 1
        yield i, op, arg
        i += w


INVOKE = {0xB6: "invokevirtual", 0xB7: "invokespecial",
          0xB8: "invokestatic", 0xB9: "invokeinterface"}
FIELD_OPS = {0xB2, 0xB3, 0xB4, 0xB5}


# ---------------------------------------------------------------- world view
class World:
    """The real Minecraft + NeoForge classes, addressed by deobfuscated names."""

    def __init__(self, mappings, vanilla_jar, cp_dir):
        self.map = mappings
        self.vanilla = {}
        with zipfile.ZipFile(vanilla_jar) as zf:
            for nm in zf.namelist():
                if nm.endswith(".class"):
                    self.vanilla[nm[:-6]] = zf.read(nm)
        self.lib = {}
        for fn in sorted(os.listdir(cp_dir)):
            if not fn.endswith(".jar"):
                continue
            try:
                with zipfile.ZipFile(os.path.join(cp_dir, fn)) as z:
                    for nm in z.namelist():
                        if nm.endswith(".class"):
                            self.lib.setdefault(nm[:-6], z.read(nm))
            except zipfile.BadZipFile:
                print("  (skipping non-zip %s)" % fn)
        self.cache = {}

    def locate(self, deobf_dotted):
        """deobf dotted name -> (kind, raw bytes) or (None, None)."""
        obf = self.map.deobf_to_obf.get(deobf_dotted)
        if obf is not None and obf in self.vanilla:
            return "vanilla", self.vanilla[obf], obf
        binname = deobf_dotted.replace(".", "/")
        if binname in self.vanilla:                 # non-obfuscated vanilla class
            return "vanilla", self.vanilla[binname], binname
        if binname in self.lib:
            return "lib", self.lib[binname], binname
        return None, None, None

    def entry(self, deobf_dotted):
        """{'kind', 'methods': set[(name, desc)], 'fields': set[...], 'supers': [...]}"""
        if deobf_dotted in self.cache:
            return self.cache[deobf_dotted]
        kind, raw, binname = self.locate(deobf_dotted)
        if kind is None:
            self.cache[deobf_dotted] = None
            return None
        cf = ClassFile(raw)
        entry = {"kind": cf.kind(), "methods": set(), "fields": set(), "supers": []}
        if kind == "vanilla":
            mm = self.map.member_map.get(binname, {})
            fm = self.map.field_map.get(binname, {})
            for mname, _md, _code, _acc in cf.methods:
                entry["methods"].update(mm.get(mname, ()))
            for fname, _fd in cf.fields:
                entry["fields"].update(fm.get(fname, ()))
            sup = cf.name(cf.super_i)
            if sup:
                entry["supers"].append(self.map.obf_to_deobf.get(sup, sup.replace("/", ".")))
            for i in cf.ifaces:
                nm = cf.name(i)
                if nm:
                    entry["supers"].append(self.map.obf_to_deobf.get(nm, nm.replace("/", ".")))
        else:
            entry["methods"] = {(m[0], m[1]) for m in cf.methods}
            entry["fields"] = {(f[0], f[1]) for f in cf.fields}
            sup = cf.name(cf.super_i)
            if sup:
                entry["supers"].append(sup.replace("/", "."))
            for i in cf.ifaces:
                nm = cf.name(i)
                if nm:
                    entry["supers"].append(nm.replace("/", "."))
        self.cache[deobf_dotted] = entry
        return entry

    def chain(self, deobf_dotted, limit=40):
        """The class plus all resolvable supertypes."""
        out, seen, stack = [], set(), [deobf_dotted]
        while stack and len(out) < limit:
            cur = stack.pop(0)
            if not cur or cur in seen:
                continue
            seen.add(cur)
            e = self.entry(cur)
            if e is None:
                continue
            out.append((cur, e))
            stack.extend(e["supers"])
        return out

    def member_owner(self, deobf_dotted, name, desc, what):
        """First type in the chain that really declares this member."""
        for cls, e in self.chain(deobf_dotted):
            if (name, desc) in e[what]:
                return cls
        return None


# ---------------------------------------------------------------- the checks
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jar", required=True, help="the mod jar to verify")
    ap.add_argument("--mappings", required=True, help="Mojang 1.21.1 client.txt")
    ap.add_argument("--vanilla", required=True, help="vanilla 1.21.1 client.jar")
    ap.add_argument("--cp-dir", required=True,
                    help="directory with neoforge-*-universal.jar + FML jars")
    ap.add_argument("--prefix", default="com/wanderingearth",
                    help="only classes under this package are checked")
    args = ap.parse_args(argv)

    mp = Mappings(args.mappings)
    print("mappings: %d classes" % len(mp.obf_to_deobf))
    world = World(mp, args.vanilla, args.cp_dir)
    print("vanilla classes: %d | library classes: %d" %
          (len(world.vanilla), len(world.lib)))

    own = {}
    with zipfile.ZipFile(args.jar) as zf:
        names = zf.namelist()
        leaks = [n for n in names
                 if n.endswith(".class") and n.startswith(("net/minecraft/", "com/mojang/"))]
        for nm in names:
            if nm.endswith(".class") and nm.startswith(args.prefix):
                own[nm[:-6]] = zf.read(nm)

    problems = []
    checked_invokes = checked_members = checked_overrides = 0

    print("\nchecking %d mod classes ..." % len(own))
    for rel, raw in sorted(own.items()):
        cf = ClassFile(raw)
        mine = {}

        # --- 1 & 2: invoke kind + member linkage
        for mname, mdesc, code, _acc in cf.methods:
            if not code:
                continue
            for off, op, arg in decode(code):
                if op not in INVOKE and op not in FIELD_OPS:
                    continue
                if arg is None or arg >= len(cf.cp):
                    continue
                e = cf.cp[arg]
                if not e or e[0] not in (9, 10, 11):
                    continue
                owner_bin = cf.name(e[1][0])
                if not owner_bin or owner_bin.startswith("["):
                    continue
                owner = owner_bin.replace("/", ".")
                nat = cf.cp[e[1][1]]
                ref_name = cf.name(nat[1][0])
                ref_desc = cf.name(nat[1][1])
                if world.locate(owner)[0] is None:
                    continue        # our own class or a JDK type
                entry = world.entry(owner)
                if entry is None:
                    continue
                where = "fields" if op in FIELD_OPS else "methods"
                checked_members += 1
                if op in INVOKE:
                    checked_invokes += 1
                    real_kind = entry["kind"]
                    if op == 0xB9 and real_kind != "interface":
                        problems.append(("ICCE", rel, mname, off,
                                         "invokeinterface on %s, real kind=%s"
                                         % (owner, real_kind)))
                    elif op in (0xB6, 0xB7) and real_kind == "interface":
                        problems.append(("ICCE", rel, mname, off,
                                         "%s on interface %s"
                                         % (INVOKE[op], owner)))
                if world.member_owner(owner, ref_name, ref_desc, where) is None:
                    problems.append(("NO_SUCH_" + where[:-1].upper(),
                                     rel, mname, off,
                                     "%s.%s%s" % (owner, ref_name, ref_desc)))

        # --- 3: overrides of real methods must match the real descriptor
        sup_bin = cf.name(cf.super_i)
        if sup_bin:
            sup = mp.obf_to_deobf.get(sup_bin, sup_bin.replace("/", "."))
            real_methods = {}
            for cls, e in world.chain(sup):
                for rn, rd in e["methods"]:
                    real_methods.setdefault(rn, set()).add(rd)
            for mname, mdesc, _code, _acc in cf.methods:
                if mname.startswith("<") or mname not in real_methods:
                    continue
                checked_overrides += 1
                if mdesc not in real_methods[mname]:
                    problems.append(("SILENT_OVERRIDE", rel, mname, -1,
                                     "descriptor %s never matches %s in %s; real: %s"
                                     % (mdesc, mname, sup, sorted(real_methods[mname]))))

    # --- 4: stub leak
    for nm in leaks:
        problems.append(("STUB_LEAK", nm, "-", -1,
                         "compile-time stub shipped inside the jar"))

    print("invoke sites: %d | member refs: %d | overrides: %d"
          % (checked_invokes, checked_members, checked_overrides))
    print("PROBLEMS: %d" % len(problems))
    for kind, rel, mname, off, detail in problems:
        loc = "%s.%s" % (rel, mname) + ("+%d" % off if off >= 0 else "")
        print("  !! [%s] %s\n       %s" % (kind, loc, detail))
    if not problems:
        print("\nAll checks passed.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
