# Create recipe examples

The datapack already ships six optional `create:crushing` / `create:pressing`
recipes under `data/wandering_earth/recipe/create_*.json`. They use Create 6.0's
item-stack result format (`{"id": ..., "count": ...}`) and only load when Create
is installed. Example:

```json
{
  "type": "create:crushing",
  "ingredients": [{"item": "minecraft:stone"}],
  "results": [{"id": "wandering_earth:heavy_nuclei_dust", "count": 2}],
  "processingTime": 150
}
```

Chain: stone -> heavy_nuclei_dust -> (Press) fusion_fuel_rod -> Heavy Fusion Reactor
-> Planetary Engine. If a future Create version changes the codec, drop or edit
these six files; the vanilla recipes are unaffected.
