# The Wandering Earth v1.4.0 — the beacon beam

The engine beam used to be a trail of `END_ROD` particles. It now looks like a
beacon.

## Why the old beam flickered

`Block.animateTick` is not called every tick on every block. The client picks
**random** blocks around the player and animates them — the vanilla
`ClientLevel.animateTick` walks a 32-block box and animates 667 random
positions per tick — and the client never ticks block entities at all. So an
`END_ROD` trail emitted from `animateTick` was drawn a few times per second, at
random positions, with a random wobble on every particle. That is exactly what
the old beam looked like: a stuttering line of sparks.

## What 1.4.0 does

* **`com/wanderingearth/client/EngineBeamRenderer.java`** implements
  `BlockEntityRenderer` and draws the shaft itself, every frame, as real
  geometry.
* The shaft uses **the vanilla beacon render type and texture**:
  `RenderType.beaconBeam(ResourceLocation, boolean)` with
  `minecraft:textures/entity/beacon_beam.png`. Two passes are drawn, a bright
  core (`0xFFE8F4FF`, radius 0.16) and a translucent halo (`0x20E8F4FF`, radius
  0.30), the same two-pass trick vanilla uses for beacon beams.
* Every side of the square shaft is emitted in both winding orders, so the beam
  is visible from any angle regardless of how the render type culls.
* The beam is emitted from the **nozzle**, not from the block centre: the block
  entity renderer starts at the minimum corner of the block, so the renderer
  translates to `(0.5 + facingX * 0.62, 0.45, 0.5 + facingZ * 0.62)`.
* **v1.4.0 fix (post-release):** the vertices are written with
  `addVertex(PoseStack.Pose, float, float, float)` and
  `setNormal(PoseStack.Pose, float, float, float)`, i.e. the pose-aware
  overloads that vanilla `BeaconRenderer` itself uses. Those overloads bake the
  accumulated `Matrix4f` (the level renderer's block-to-camera translation plus
  our nozzle translation) into each vertex. The plain `addVertex(float,float,float)`
  overload does **not** apply the pose matrix, so with it the shaft was drawn at
  raw camera-space coordinates and appeared to shoot out of the player's viewpoint
  instead of out of the engine block.
* **v1.4.0 fix (axial viewing):** the renderer overrides
  `shouldRenderOffScreen()` → `true`, `getViewDistance()` → `256` and
  `shouldRender(...)` → `true`, the same three values vanilla `BeaconRenderer`
  uses. Without them, looking along the beam puts the engine block behind the
  camera, the block entity is frustum-culled using its 1x1x1 bounding box, and
  the entire beam vanishes. The shaft is now also capped at both ends: when the
  camera is exactly on the beam axis the four side walls are edge-on and collapse
  to a line, so the two cross-section quads keep it visible as a solid square and
  give the far end a visible head.
* The beam stops at the first solid block, exactly like the particle version
  did, and reaches **`BEAM_LENGTH = 32`** blocks (it was 12).
* `Block.animateTick` now only handles the muzzle: two `SMALL_FLAME` particles
  and a `BEACON_AMBIENT` hum.

## Registration

`EntityRenderersEvent.RegisterRenderers` is a **mod bus** event
(`EntityRenderersEvent implements IModBusEvent`), so it is registered in
`com/wanderingearth/client/WanderingEarthClient.java` with

```java
@EventBusSubscriber(modid = WanderingEarth.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
```

It deliberately does **not** live in `WanderingEarth.clientSetup`: that hook
returns early when Create is not installed, and the beam renderer has to be
registered either way.

## Offline build changes

`tools/build_offline.py` gained compile-time stubs for the seven client classes
the renderer needs. Each stub carries the official 1.21.1 signature **including
return types**, because the descriptor of a method includes its return type —
a stub that returns `void` where vanilla returns `VertexConsumer` compiles
fine and then fails at runtime with `NoSuchMethodError`:

| Stub | Real class |
|---|---|
| `com/mojang/blaze3d/vertex/PoseStack` | `fbi` |
| `com/mojang/blaze3d/vertex/VertexConsumer` | `fbm` |
| `net/minecraft/client/renderer/RenderType` | `gfh` |
| `net/minecraft/client/renderer/MultiBufferSource` | `gez` |
| `net/minecraft/client/renderer/texture/OverlayTexture` | `gqc` |
| `net/minecraft/client/renderer/blockentity/BlockEntityRenderer` | `ggz` |
| `net/minecraft/client/renderer/blockentity/BlockEntityRendererProvider` | `gha` |

`OverlayTexture.NO_OVERLAY` is written as `Integer.valueOf(0)` on purpose:
boxing stops javac from inlining the constant, so the bytecode keeps a
`getstatic` and picks up the real overlay id at runtime.

The real `org.joml` jar (1.10.5) was added to the offline classpath so
`Quaternionf` and friends are the genuine library classes; joml is not
obfuscated, so the names match at runtime.

The stubs are compile-time only — the jar still contains nothing but this
mod's own classes.

## Correctness checks

```
python tools/build_offline.py
  classpath jars: 11 | stub files: 80 | real sources: 13
  javac OK
  jar OK: build/libs/wandering_earth-1.4.0.jar (585870 bytes)

python tools/verify_jar.py --jar build/libs/wandering_earth-1.4.0.jar \
    --mappings client.txt --vanilla client.jar --cp-dir <neoforge-jars>
  invoke sites: 388 | member refs: 445 | fields: 57 | overrides: 19 | phantom types: 0
  PROBLEMS: 0

python tools/verify_resources.py --jar build/libs/wandering_earth-1.4.0.jar --vanilla client.jar
  resources checked: 412 | PROBLEMS: none
```

`verify_jar.py` is the important one here: it resolves every `invoke*` and
field reference in the built jar against the real 1.21.1 classes, so a stub
with the wrong return type or the wrong owner would be reported before the
mod ever reaches the game.

The jar contains 13 classes (the 11 from 1.3.0 plus `EngineBeamRenderer` and
`WanderingEarthClient`), 903 entries in total, and zero stub leakage.
