# The Wandering Earth v1.2.0

**Engines that need a grid, a control panel that drives one, and the movie map.**

Mod jar: `wandering_earth-1.2.0.jar` (519 465 bytes)

## What's new

### 1. Redstone drives the beam

In 1.1.x a lighter stone made an engine ignite on its own. That was wrong both
physically and dramatically — an engine that lights itself never needs a plan.
Now loading is only half the job:

* `EngineBlock.neighborChanged` evaluates
  `powered = level.hasNeighborSignal(pos) || engine.hasRemotePower()` and
  `wantLit = powered && engine.getFuel() > 0`, so an engine with fuel but no
  signal sits cold.
* `ModEngineBlockEntity.serverTick` applies the same rule every tick and
  returns early when `!wantLit`, so **fuel is only consumed while actually
  firing**.
* Clicking in a lighter no longer sets `lit=true`; it stores the stone and tells
  you the engine still needs a signal.

### 2. The beam itself

`EngineBlock.animateTick` walks along `facing` up to `BEAM_LENGTH = 12` blocks,
stopping at the first non-air block, then paints `ParticleTypes.END_ROD` for
every step of that reach with a wobble that grows with distance
(`0.02 + step / reach * 0.06`). Every third step adds `ELECTRIC_SPARK`, the
muzzle emits two `SMALL_FLAME`, and one in eight ticks plays `BLAZE_SHOOT`.

This is a client-side effect, so it costs nothing on the server and follows the
nozzle when you rotate the engine.

### 3. Engine Control Panel

New block `engine_control_panel` (engines tab), a real machine with its own
block entity:

| Property | Value |
|---|---|
| Scan radii | 8 / 16 / 32 blocks (default 16) |
| Max linked engines | 256 |
| Re-push interval | 20 ticks, or immediately when the panel's own signal changes |
| Cycle radius | sneak + right-click |

* `ModControlPanelBlockEntity.rescan` walks the cube around the panel, skips
  unloaded chunks via `level.isLoaded`, keeps only `EngineBlock`s, and stores
  each as a packed `BlockPos.asLong`.
* `pushPower` decodes every packed position and calls
  `engine.setRemotePower(powered)`, which is exactly the flag the engine's
  `wantLit` test reads.
* NBT: `Radius` (int), `Linked` (long[]), `PushedPower` (boolean) — the panel
  keeps its selection across reloads.
* Right-click reports radius / engine count / on-off; the blockstate has
  `facing` + `powered`, with a separate `_front_on` texture and a green LED when
  powered.

So one lever in front of a panel can ignite an entire engine farm.

### 4. Longer burn per lighter stone

`ModEngineBlockEntity.BURN_TICKS` went from `40` to **`400`** — one lighter
stone now burns for 20 seconds instead of 2. With 64 stones in the slot an
engine runs for over 21 minutes on a full load.

## The movie map

`map/流浪地球-电影还原/` is a complete Minecraft 1.21.1 world save (level.dat +
one region file, 588 KB) written entirely by `tools/mapgen/`, which contains a
dependency-free NBT reader/writer (`nbt.py`) and a 1.21.1 Anvil writer
(`anvil.py`).

| Landmark | Details |
|---|---|
| Planetary engine | (96, ·, 96), 200 blocks tall; stepped plinth, tapered casing, cooling rings, `heavy_fusion_reactor` core, plasma nozzle, `engine_light_pillar` and an `end_rod` beam column to build limit, four ignition stations, control deck with three panels |
| Undercity | y ≈ -51 under the engine: habitat hall, three floors of capsules, hibernation pods, eco-cycle units, ration dispensers, lottery terminal, Beijing-3 sign, artificial sun lamps, UEG flag and emblem, southern blast-door corridor |
| 550W room | MOSS mainframe, cameras, red dot, iteration console, digital-life terminal, human-in-the-loop port, Tu Yaya's data core, quantum racks |
| Space elevator | (152, ·, 96): base legs, rail, cable climbing 230 blocks, cabin, counterweight, ark station, seed vault, Gagarin plaque, four turrets, eighteen wreckage pieces |
| Surface | ice road, UEG checkpoint, six-`heavy_hauler` convoy, CN171-11 trench, command bunker with Zhou's ignition button and the over-fifty roster, Jupiter observation post, magma fissure, two ruined engine silhouettes |

Verified by reading the generated region back: `DataVersion 3955`,
`Status minecraft:full`, 144 chunks, and spot checks along the engine axis
(`heavy_fusion_reactor` from y -16 to 177, `plasma_beam_emitter` at 180,
`end_rod` at 220 and 250), the elevator axis (`space_elevator_base`, `rail`,
`cabin`, `cable`, `counterweight`, `ark_station_block`) and every undercity
prop.

**Honest scope.** This is a thematic reconstruction at Minecraft scale, not a
survey-accurate replica. An 11 000-block engine would be 11 km tall; the one
here is 200. Set pieces, their order and their props follow the films;
distances do not. Where the films disagree with themselves or leave a detail
unstated, the mod follows `docs/LORE.md` and marks the guess.

## Correctness work

Nothing here skipped the verifier, and the verifier grew a hole closed:

```
invoke sites: 363 | member refs: 420 | fields: 57 | overrides: 19
phantom types: 0 | PROBLEMS: 0
resources checked: 347 | PROBLEMS: none
```

One compile error was found and fixed during the port: `ModControlPanelBlockEntity`
called `BlockPos.offset(int,int,int)`, which the offline stub did not declare.
It exists in vanilla (`BlockPos.offset -> e`), so the stub was extended — the
mod code was correct.

## Content

* 90 blocks (89 + `engine_control_panel`) and 39 items across eight categories
* 261 language keys, identical key sets in `en_us` and `zh_cn`
* 133 block textures, 40 item textures (all 32×32 except the 64×64 logo)
* 139 recipes, 92 loot tables, 5 advancements
* 3 Ponder scenes with real structure files
* jar: 766 entries, 11 mod classes, zero leaked stub classes

## Building

Normal ModDevGradle build, needs access to `maven.neoforged.net`:

```
gradlew build
```

Reproducible offline build against real NeoForge API jars plus verified stubs:

```
python tools/build_offline.py
```

Then verify before shipping — this is not optional, it catches exactly the two
crash classes this project has hit:

```
python tools/verify_jar.py --jar build/libs/wandering_earth-1.2.0.jar \
    --mappings <client.txt> --vanilla <client.jar> --cp-dir <jars>
python tools/verify_resources.py --jar build/libs/wandering_earth-1.2.0.jar \
    --vanilla <client.jar>
```

Regenerate the map with:

```
cd tools/mapgen
python build_map.py
```

SHA-256 of `wandering_earth-1.2.0.jar`:
`c58c06f468e669ffc24d4c9e588f5f23661a77c2d61e085c4407149b8f48a465`
