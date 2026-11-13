# 流浪地球 · The Wandering Earth

A **Minecraft 1.21.1 / NeoForge** content mod themed around *The Wandering Earth*
(《流浪地球》, films 2019 & 2023 and the novella), designed as a
**Create / Create Aeronautics addon**.

> "道路千万条，安全第一条；行车不规范，亲人两泪流。"
> — 北京第三区交通委

## What's inside

89 blocks + 39 items across eight authentic categories:

| Category | 内容 | Examples |
|---|---|---|
| 行星发动机 | engines | Planetary Engine Core / Nozzle / Light Pillar, Heavy Fusion Reactor, Lighter Socket, Ignition Core |
| 地下城 | undercity | Blast Door, Capsule Apartment, Hibernation Pod, Lottery Terminal, Artificial Sun Lamp, Beijing-3 sign |
| 太空电梯 | elevator | Cable (carbon nanotube), Cabin, Counterweight, Ark / Navigator stations, Seed Vault, Wreckage |
| 载具装备 | vehicles | Heavy Hauler, Drive Ball, Exoskeleton, Robot Dog Benben, UAV, Tower Crane, Lunar Rover, EVA suit |
| 军事危机 | military | CN171-11 patch, Gatling, Lunar Nuke, Phased-array Detonator, Manual Detonator, Helium Flash Beacon |
| 天文环境 | cosmos | Jupiter Great Red Spot, Proxima Centauri Chart, Frozen Ground, Ice Crust, Magma Flood |
| 道具符号 | props | UEG Flag, Vodka Bottle, Lighter Stone, Zhou's Ignition Button, Over-Fifty Roster, MOSS quotes |
| 550 / MOSS | quantum | 550A / 550C / 550W, MOSS Camera / Red Dot / Mainframe, Digital Life Card, Tu Yaya Data Core |

Every block: blockstate, cube model, loot table, crafting recipe, `en_us` + `zh_cn`
name, lore tooltip (hover) and an in-world message on right-click. A few blocks
have authentic little interactions: the **undercity lottery**, the **countdown
display**, **MOSS** lines, the **traffic notice**, the **UEG alert** and Zhou's
**ignition button**. All blocks are grouped into 8 creative tabs.

Recipes use **vanilla ingredients only**, so the mod is fully playable
standalone. Optional `create:crushing` / `create:pressing` recipes are also
included and activate when Create is installed. In `neoforge.mods.toml`,
`create` and `aeronautics` are declared as *optional* dependencies so it loads
both with and without them (thematically it is a Create Aeronautics addon).

## Building

Standard ModDevGradle project (Java 21):

```
gradlew build
```

The produced jar is in `build/libs/`. This requires a machine that can reach
`maven.neoforged.net` (ModDevGradle's NeoForm runtime is only published there).
The Gradle wrapper here points at a Tencent mirror for the Gradle distribution.

### Offline build (no maven.neoforged.net)

On networks where `maven.neoforged.net` is unreachable, a full ModDevGradle build
cannot run (NeoForm Runtime `net.neoforged:neoform-runtime:2.0.31` is not
mirrored). This repository therefore also ships an **offline-compiled jar**:
`prebuilt/wandering_earth-1.0.1.jar`. It was produced by compiling the exact
same `src/main/java` sources against the real NeoForge 1.21.1 API jars plus
compile-time-only `net.minecraft.*` signature stubs (verified against Mojang's
official 1.21.1 mappings). The stubs are **not** shipped inside the jar — at
runtime the game supplies the real Minecraft + NeoForge classes. The jar
contains only this mod's classes and resources and installs like any other mod.

See `tools/build_offline.py` for the reproducible offline build.

> **Why the stubs get verified, not just compiled.** A stub that declares the
> wrong *kind* of type (an interface as a `class`, or vice versa) compiles
> perfectly — javac emits `invokevirtual` where the JVM expects
> `invokeinterface` — and then throws
> `IncompatibleClassChangeError` the first time the game touches it. That is
> exactly what broke v1.0.0 (`MutableComponent` was stubbed as an interface;
> it is a class). The same class of failure has a second form: a field stubbed
> as an instance field when the real one is `static` (or the reverse) makes
> `getstatic`/`getfield` disagree with the real `ACC_STATIC` flag, which throws
> `IncompatibleClassChangeError` too — again only at runtime. `tools/verify_jar.py`
> therefore checks the built jar against the real 1.21.1 classes before it is
> shipped: invoke kinds, field staticness, member linkage, override descriptors,
> and that no stub leaked into the jar. Run it with:
>
> ```
> python tools/verify_jar.py --jar prebuilt/wandering_earth-1.0.1.jar \
>     --mappings client.txt --vanilla client.jar --cp-dir <neoforge-jars>
> ```
>
> It reproduces the v1.0.0 crash on the old jar and reports 0 problems on this
> one.

## Install

Drop the jar into `mods/` of a Minecraft **1.21.1** + **NeoForge 21.1.x**
instance. Create / Create Aeronautics are optional (recommended, for theme and
the Create recipes).

## Lore notes

Content is based on the films and novella; a few ambiguous items (e.g. the
"singularity data core", "周罗", exact engine counts) are deliberately generic
rather than invented as fact. See `docs/LORE.md`. No copyrighted audio or
original film assets are included — all textures are programmatically generated.

## License

MIT. This is a fan-made, non-commercial tribute.
