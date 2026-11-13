# The Wandering Earth v1.0.1

Fixes the crash that made v1.0.0 unusable.

## What was broken

v1.0.0 threw this the first time a tooltip rendered — i.e. as soon as you opened
a creative tab containing the mod's items and hovered one:

```
java.lang.IncompatibleClassChangeError: Found class
    net.minecraft.network.chat.MutableComponent, but interface was expected
    at com.wanderingearth.block.ModBlock.appendHoverText(ModBlock.java:48)
```

Cause: this project builds offline against compile-time-only `net.minecraft.*`
stubs (the real classes ship with the game). Four of those stubs declared the
wrong **kind** of type. That compiles perfectly cleanly — javac just emits
`invokeinterface` where the JVM expects `invokevirtual` — and then dies at
runtime the moment the code is reached.

## Fixed

Corrected stub kinds, each now carrying a comment with the real obfuscated class
and its access flags so it cannot silently regress:

| Type | Was | Now | Real class |
|---|---|---|---|
| `MutableComponent` | interface | **class** | `xn`, `0x0021` |
| `TooltipFlag` | enum | **interface** | `cwm`, `0x0601` |
| `HolderLookup` | class | **interface** | `jo`, `0x0601` |
| `DataComponentType` | class | **interface** | `kp`, `0x0601` |

## New: `tools/verify_jar.py`

A regression check that validates a built jar against the real 1.21.1 classes
before it ships:

- **invoke kinds** — catches `IncompatibleClassChangeError`
- **member linkage** — catches `NoSuchMethodError` / `NoSuchFieldError`
- **override descriptors** — catches overrides that silently never run
- **stub leakage** — the compile-time stubs must not end up inside the jar

Pointed at the old v1.0.0 jar it reproduces the crash: **7 ICCE reports**, one at
`ModBlock.appendHoverText+16`, the exact crashing offset. On this jar:
**0 problems** across 93 invoke sites, 103 member references and 2 overrides.

## Contents

Unchanged from v1.0.0 — 89 blocks, 39 items, 8 creative tabs, full
blockstates / models / loot tables / recipes / language files (en_us + zh_cn),
129 procedurally drawn original textures, 6 optional Create recipes,
4 advancements.

## Install

Minecraft **1.21.1** + **NeoForge 21.1.x**. Drop
`wandering_earth-1.0.1.jar` into `mods/`.

Create / Create Aeronautics are **optional** (recommended for theme and the
Create recipes).

Artifact: `wandering_earth-1.0.1.jar` — 285,049 bytes
SHA-256 `f14190443b098a1e946a6b2478e27415328fd3a07cbecb09f3f1f96800965aa5`
