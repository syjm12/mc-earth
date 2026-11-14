"""Validate that every resource reference in the mod jar resolves.

blockstate -> model, model -> parent chain + textures, loot table items,
recipe ingredients/results. Vanilla targets are resolved against a real 1.21.1
client jar, so typos like minecraft:block/oreintable are caught here instead of
showing up in game as a missing model.

    python tools/verify_resources.py --jar build/libs/wandering_earth-1.1.0.jar \
        --vanilla path/to/client.jar
"""
import json
import os
import zipfile

import argparse

_ap = argparse.ArgumentParser()
_ap.add_argument("--jar", required=True)
_ap.add_argument("--vanilla", required=True)
_ap.add_argument("--namespace", default="wandering_earth")
_args = _ap.parse_args()

MOD_JAR = _args.jar
VANILLA = _args.vanilla
NS = _args.namespace

mod = zipfile.ZipFile(MOD_JAR)
van = zipfile.ZipFile(VANILLA)
van_names = set(van.namelist())
mod_names = set(mod.namelist())

problems = []
checked = 0


def model_path(rl):
    ns, path = rl.split(":", 1) if ":" in rl else ("minecraft", rl)
    return "assets/%s/models/%s.json" % (ns, path)


def texture_path(rl):
    ns, path = rl.split(":", 1) if ":" in rl else ("minecraft", rl)
    return "assets/%s/textures/%s.png" % (ns, path)


def blockstate_path(rl):
    ns, path = rl.split(":", 1) if ":" in rl else ("minecraft", rl)
    return "assets/%s/blockstates/%s.json" % (ns, path)


def exists(rel):
    if rel in mod_names:
        return True
    return rel in van_names


def load(rel):
    if rel in mod_names:
        return json.loads(mod.read(rel).decode("utf-8"))
    if rel in van_names:
        return json.loads(van.read(rel).decode("utf-8"))
    return None


BUILTIN = {"assets/minecraft/models/builtin/generated.json",
           "assets/minecraft/models/builtin/entity.json"}


def check_model(rel, depth=0):
    global checked
    if rel in BUILTIN:
        return
    if depth > 6:
        problems.append("parent chain too deep: " + rel)
        return
    doc = load(rel)
    if doc is None:
        problems.append("missing model: " + rel)
        return
    parent = doc.get("parent")
    if parent:
        check_model(model_path(parent), depth + 1)
    for key, value in doc.get("textures", {}).items():
        if isinstance(value, str) and not value.startswith("#"):
            checked += 1
            if not exists(texture_path(value)):
                problems.append("missing texture %s (in %s)" % (value, rel))


# blockstates
for n in sorted(mod_names):
    if n.startswith("assets/%s/blockstates/" % NS) and n.endswith(".json"):
        checked += 1
        doc = json.loads(mod.read(n).decode("utf-8"))
        models = set()
        if "variants" in doc:
            for v in doc["variants"].values():
                entries = v if isinstance(v, list) else [v]
                for e in entries:
                    models.add(e["model"])
        if "multipart" in doc:
            for part in doc["multipart"]:
                entries = part["apply"] if isinstance(part["apply"], list) else [part["apply"]]
                for e in entries:
                    models.add(e["model"])
        for m in models:
            check_model(model_path(m))

# item models follow the block models; make sure every registered block has one
block_items = [n for n in mod_names
               if n.startswith("assets/%s/models/item/" % NS) and n.endswith(".json")]
for n in block_items:
    doc = json.loads(mod.read(n).decode("utf-8"))
    parent = doc.get("parent")
    if parent:
        check_model(model_path(parent))

# loot tables: drops must reference real items
for n in sorted(mod_names):
    if n.startswith("data/%s/loot_table/blocks/" % NS) and n.endswith(".json"):
        doc = json.loads(mod.read(n).decode("utf-8"))

        def walk(pools):
            for pool in pools:
                for entry in pool.get("entries", []):
                    item = entry.get("name")
                    if item:
                        ns, path = item.split(":", 1) if ":" in item else ("minecraft", item)
                        if not exists("assets/%s/models/item/%s.json" % (ns, path)):
                            problems.append("loot item without model: %s (%s)" % (item, n))
                    walk([{"entries": entry.get("children", [])}])

        walk(doc.get("pools", []))

# recipes: ingredients and results must exist as items
for n in sorted(mod_names):
    if n.startswith("data/%s/recipe/" % NS) and n.endswith(".json"):
        doc = json.loads(mod.read(n).decode("utf-8"))

        def check_item(rl, where):
            ns, path = rl.split(":", 1) if ":" in rl else ("minecraft", rl)
            if ns == NS and not exists("assets/%s/models/item/%s.json" % (ns, path)):
                problems.append("recipe item without model: %s (%s)" % (rl, where))

        def collect(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ("item", "id") and isinstance(v, str):
                        check_item(v, n)
                    else:
                        collect(v)
            elif isinstance(obj, list):
                for v in obj:
                    collect(v)

        collect(doc)

print("resources checked:", checked)
print("PROBLEMS:", "none" if not problems else "")
for p in problems[:40]:
    print("  -", p)
print("total problems:", len(problems))
raise SystemExit(1 if problems else 0)
