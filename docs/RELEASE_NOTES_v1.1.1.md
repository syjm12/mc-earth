# The Wandering Earth v1.1.1

**Crash fix.** v1.1.0 could not load at all — it failed during block registration
and left the game in a half-registered state underneath every other mod. This
release fixes all three causes and adds the check that would have caught them.

Mod jar: `wandering_earth-1.1.1.jar`
SHA-256: `a441de963b0a0c4b47a4023281ca6f59dd56668fb08037658bb482a1609b3be2`

## What went wrong in 1.1.0

The crash report showed a Veil `NullPointerException` in `RenderTarget.blitToScreen`,
which is a red herring: Veil crashed *because* the mod list was already broken.
The real failures are in `latest.log`, all while NeoForge was dispatching
`RegisterEvent` for `wandering_earth`:

```
NoClassDefFoundError: net/minecraft/world/level/block/state/BlockStateProperties
    at com.wanderingearth.block.EngineBlock.<clinit>(EngineBlock.java:56)

NullPointerException: Trying to access unbound value:
    ResourceKey[minecraft:block / wandering_earth:planetary_engine_core]
    at DeferredHolder.value(DeferredHolder.java:103)
    at DeferredRegister$Items.lambda$registerSimpleBlockItem$1(...)

ArrayStoreException: arraycopy: element type mismatch: can not cast one of the
    elements of java.lang.Object[] to the type of the destination array,
    net.minecraft.world.level.block.Block
    at com.wanderingearth.registry.ModBlockEntities.engineBlocks(...)
```

### 1. Wrong package for `BlockStateProperties`

The real class is `net.minecraft.world.level.block.state.**properties**.BlockStateProperties`
(`client.txt:110000`: `net.minecraft.world.level.block.state.properties.BlockStateProperties -> dts:`).
`EngineBlock` and `WanderingEarthPonder` imported it from `...block.state`, which
does not exist. It compiled because the offline build has a hand-written stub,
and the stub had the same wrong path — a stub and its caller agreeing on a
package that Minecraft never had.

This is the failure that took the whole mod down: `EngineBlock.<clinit>` throws,
so every engine block fails to register, so `ModItems` cannot resolve the
`BlockItem` suppliers it built from those blocks (error 2), and so on.

### 2. `ModItems` could not build block items

A downstream symptom of 1, not a separate defect: `ModItems`'s static block
iterates `ModBlocks.ALL` and calls `registerSimpleBlockItem(name, b::get, ...)`.
Because the engine blocks never registered a value in error 1, dereferencing them
here threw "Trying to access unbound value".

The code is unchanged, because the ordering it relies on is correct: NeoForge
dispatches `BLOCK` before `ITEM`, so a healthy block register is always complete
before item suppliers run. The recorded timestamps back this up — block
registration at 46.913, block-entity types at 47.029. Fixing error 1 fixes this.

### 3. `toArray(new Block[0])` on a list of `DeferredBlock`

```java
ModBlocks.ENGINE_BLOCKS.toArray(new Block[0])   // ArrayStoreException
```

`ENGINE_BLOCKS` is a `List<DeferredBlock<Block>>`. `ArrayList.toArray(T[])` only
checks the *runtime* element type when copying, and `DeferredBlock` is not a
`Block`, so it throws. It never showed up in testing because the array is built
inside a supplier that only runs during `BLOCK_ENTITY_TYPE` registration — which
error 1 prevented from ever being reached.

Now it maps to the resolved blocks first:

```java
return ModBlocks.ENGINE_BLOCKS.stream().map(block -> (Block) block.get()).toArray(Block[]::new);
```

This is safe at that point: the log timestamps show block registration dispatching
at 46.913 and block-entity-type at 47.029, so the blocks are already bound.

## Hardening: the verifier now catches this class of bug

Every offline build is checked by `tools/verify_jar.py`. It missed the phantom
package because it only validated the owner of each method/field reference, and
skipped anything it could not resolve ("our own class or a JDK type").

It now has two phantom-type checks:

* `UNKNOWN_TYPE` at an invoke site — an owner under `net.minecraft.` that is not
  in the mapping table.
* `UNKNOWN_TYPE` anywhere in the constant pool — covers descriptors, field
  types, catch types and signatures, which have no invoke site but still fail
  the class load.

Run against the shipped 1.1.0 jar it now reports exactly the bug:

```
PROBLEMS: 3
  !! [UNKNOWN_TYPE] com/wanderingearth/block/EngineBlock.<clinit>+0
       net.minecraft.world.level.block.state.BlockStateProperties
  !! [UNKNOWN_TYPE] com/wanderingearth/block/EngineBlock.<clinit>+6
       net.minecraft.world.level.block.state.BlockStateProperties
  !! [UNKNOWN_TYPE] com/wanderingearth/compat/WanderingEarthPonder.engineScene+146
       net.minecraft.world.level.block.state.BlockStateProperties
```

And on 1.1.1:

```
invoke sites: 280 | member refs: 323 | fields: 43 | overrides: 10 | phantom types: 0
PROBLEMS: 0
```

The offline stub set was corrected to match (`state/properties/BlockStateProperties.java`),
with a comment recording the real obfuscated name so the path cannot drift back.

## Everything from 1.1.0 is still here

The engine behaviour itself was never broken — it just never got to run:

* Ten engine blocks with `FACING` + `LIT` blockstate, `BlockEntity` holding
  `Fuel`/`BurnTimer` in NBT, burning one lighter stone per 40 ticks.
* Sneak-right-click turns the nozzle a quarter turn, with a message naming the
  new facing.
* `animateTick` emits `FLAME` and `LARGE_SMOKE` along the facing direction, with
  an occasional `FIRE_AMBIENT` hiss.
* Right-click loads a lighter stone; engines also inhale any `lighter_stone`
  item entity within 3 blocks once a second.
* Create Ponder scenes for the engine, the lighter socket and MOSS (hold W),
  backed by real structure files in `assets/wandering_earth/ponder/`.
* 32×32 layered textures, including four distinct faces per engine block.

## Content

89 blocks, 39 items, 253 language keys (en_us + zh_cn), 130 block textures,
40 item textures, 89 loot tables, 138 recipes, 5 advancements.
Jar: 755 entries, 9 classes, no compile-time stubs shipped.

## Building

Both paths are reproducible from the repository:

```
./gradlew build                      # standard ModDevGradle build
python tools/build_offline.py        # offline build against real NeoForge jars
```

Then verify before shipping:

```
python tools/verify_jar.py --jar build/libs/wandering_earth-1.1.1.jar \
    --mappings client.txt --vanilla client.jar --cp-dir <neoforge jars>
python tools/verify_resources.py --jar build/libs/wandering_earth-1.1.1.jar \
    --vanilla client.jar
```
