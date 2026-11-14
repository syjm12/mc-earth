# The Wandering Earth 1.3.0 — release notes

**Theme: the film research pass.** 1.3.0 does not add "more blocks for the
sake of blocks" — it adds the set pieces the films actually put on screen, and
it fixes every line of lore text that the films do not support.

---

## 1. Fact checking, with sources

Every lore claim in the mod was re-checked against the Chinese and English
Wikipedia articles for *The Wandering Earth* (2019) and *The Wandering Earth 2
(2023), fetched on 2026-11-14. The full transcript-style summary lives in
[`docs/FILM_LORE.md`](FILM_LORE.md): verified facts, the full timeline, the
numbers, the characters, the 550 lineage, a table of "how the mod handles the
uncertain items", and a list of what stays deliberately vague.

### Claims that were removed

| Old claim | Why it went |
|---|---|
| "The engines are 11 000 m tall" | The 11 000 m figure is from the **novella**. Neither film nor the encyclopaedic entries give a height. |
| "The undercity holds 3.5 billion people" | The films never give a number. They say **half of humanity** went underground, mostly chosen by **lottery**. |
| "The digital life plan was Israeli" / "Israel's singularities" | No such thing in the films. `singularity_data_core` survives only as a 550-line cabinet name. |
| "Several hundred iterations" | The films say **over 900 generations**. |
| "周罗" | A typo for **周喆直**. The mod now uses 周喆直 everywhere. |
| "UEW" | The correct abbreviation is **UEG** (United Earth Government, the UN reorganised). |

### Facts that were added

* 10 000 planetary engines and 2 000 turning engines.
* The lunar crisis of 2058: **3 371 nuclear bombs**, **300 astronauts over
  fifty** volunteering, the decryption still needing **714 hours**, the moon
  falling in **224 hours**, and the **three global root servers** (Beijing,
  Tokyo, Dulles) that had to be back online within half an hour.
* **30 000 digits** of password typed out by Tu Yaya.
* The day becoming **60 hours** long in 2053.
* **550A**: over 900 generations, 2 minutes of life, 70 years after the upload
  to 550W. **550C**: only three machines in the world, one destroyed by a Z9
  solar storm. **550W** renamed **MOSS** in 2058.
* The **Fire Seed plan** was authorised by **MOSS on its own** — it was never a
  UEG plan. In the sequel it is the origin of both crises.
* **Lighter Core** is the English name of 火石.
* Liu Peiqiang won the underground lottery; Han Duoduo did not, and had 84.3
  days left.
* Sulawesi No.3, Singapore No.1 and Jakarta No.4 were the three engines that
  tried to ignite Jupiter — the plasma still fell 5 000 km short.
* MOSS concluded the plan had failed **0.42 seconds** after Emergency Plan
  No.3 started.

All of these are now in the block and item tooltips, in both languages.

---

## 2. New content — 17 blocks

| Block | Category | What it is |
|---|---|---|
| `lunar_satellite_engine` | engines | One of the three engines on the moon. All three overloaded 1.7 s after Tu Hengyu uploaded his daughter's consciousness, and exploded. |
| `sulawesi_turning_engine` | engines | The engine that was reprogrammed to ignite Jupiter — and still fell short. |
| `moon_engine_platform` | engines | The construction platform for the lunar engines. |
| `moon_nuke_array` | military | The phased array of 3 371 bombs on the moon. |
| `root_server_beijing` | quantum | Where Ma Zhao and Tu Hengyu drowned when seawater flooded the hall. |
| `root_server_tokyo` | quantum | The second of the three root servers. |
| `root_server_dulles` | quantum | The third, in Virginia. |
| `delhi_digital_life_institute` | quantum | The ruins of the institute where the Digital Life plan began. |
| `digital_life_lab_ruin` | quantum | The laboratory where Tu Hengyu worked. |
| `ark_plan_terminal` | props | The American Ark plan terminal, never revived after 2044. |
| `moon_by_moon_terminal` | props | The Russian Moon-by-Moon terminal. |
| `fire_seed_plan_core` | props | The core of the plan MOSS launched on its own. |
| `emergency_plan_board` | props | The board marked "Emergency Plan No.3". |
| `navigator_iss_module` | elevator | A module of the Navigator ISS. |
| `navigator_iss_control` | elevator | Where Liu Peiqiang burned MOSS's core node with Makarov's vodka. |
| `jining_police_station` | props | Where Liu Qi was held after stealing a hauler. |
| `moon_return_capsule` | vehicles | The capsule Russia's first moon landing left behind. |

## 3. New content — 8 items

`hanzi_hao_vehicle_card` (韩子昂的车卡), `digital_life_plan_permit`,
`moon_nuke_placement_map`, `root_server_access_key`,
`emergency_plan_manual`, `li_yiyi_toolbox`, `fire_seed_civilization_record`,
`tu_yaya_memory_chip`.

## 4. Two more real engines

`lunar_satellite_engine` and `sulawesi_turning_engine` are not decoration.
They have the same `facing`/`lit` blockstates, the same `BlockEntity` with
NBT fuel state, the same redstone requirement and the same plasma beam as
every other engine — so a base of lunar engines behaves exactly like a base of
ground engines. Twelve engine blocks are now fully mechanical.

---

## Correctness work

```
python tools/build_offline.py
  classpath jars: 10 | stub files: 73 | real sources: 11
  javac OK | jar OK: build/libs/wandering_earth-1.3.0.jar | size: 582100 bytes

python tools/verify_jar.py --jar build/libs/wandering_earth-1.3.0.jar ...
  invoke sites: 371 | member refs: 428 | fields: 57 | overrides: 19
  phantom types: 0 | PROBLEMS: 0 | All checks passed.

python tools/verify_resources.py --jar build/libs/wandering_earth-1.3.0.jar ...
  resources checked: 412 | PROBLEMS: none | total problems: 0
```

Jar contents: 900 entries, 11 classes, 0 stub leakage, 156 block textures,
48 item textures, 164 recipes, 109 loot tables, 311 `zh_cn` keys and 311
`en_us` keys with identical key sets.

The new textures are produced by `tools/gen_v13_content.py`, a fresh
self-contained generator (the original all-in-one generator was lost in the
2026-11-14 filesystem incident and was never committed). It draws every new
texture with Pillow — no film assets, no copyrighted material.

## Building

```
gradlew build                                  # online, standard MDG build
python tools/build_offline.py                  # offline, no maven.neoforged.net
python tools/gen_v13_content.py                # regenerate the 1.3.0 textures
```

## License

MIT. Fan-made, non-commercial tribute. No film audio, stills or original art
is included.
