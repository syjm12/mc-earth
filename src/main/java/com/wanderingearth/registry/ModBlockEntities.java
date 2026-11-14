package com.wanderingearth.registry;

import com.wanderingearth.WanderingEarth;
import com.wanderingearth.block.ModEngineBlockEntity;
import net.minecraft.core.registries.Registries;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

/**
 * Block entity types.
 *
 * <p>{@code BlockEntityType.Builder.of(...).build(null)} is the 1.21.1 form:
 * the {@code DataFixer Type} argument is only needed for world upgrades, and
 * passing {@code null} is what vanilla and every modern mod does.
 */
public final class ModBlockEntities {

    public static final DeferredRegister<BlockEntityType<?>> BLOCK_ENTITIES =
            DeferredRegister.create(Registries.BLOCK_ENTITY_TYPE, WanderingEarth.MOD_ID);

    /** Backing type for every engine-family block. */
    public static final DeferredHolder<BlockEntityType<?>, BlockEntityType<ModEngineBlockEntity>> ENGINE =
            BLOCK_ENTITIES.register("engine",
                    () -> BlockEntityType.Builder.of(ModEngineBlockEntity::new, engineBlocks()).build(null));

    private static Block[] engineBlocks() {
        return ModBlocks.ENGINE_BLOCKS.toArray(new Block[0]);
    }

    private ModBlockEntities() {}
}
