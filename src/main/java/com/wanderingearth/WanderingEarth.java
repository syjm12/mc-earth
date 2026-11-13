package com.wanderingearth;

import com.wanderingearth.registry.ModBlocks;
import com.wanderingearth.registry.ModCreativeTabs;
import com.wanderingearth.registry.ModItems;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;

/**
 * The Wandering Earth - a Create / Create Aeronautics themed content mod.
 * Lore follows the films (2019 / 2023) and the original novella.
 */
@Mod(WanderingEarth.MOD_ID)
public class WanderingEarth {
    public static final String MOD_ID = "wandering_earth";
    public static final String MOD_NAME = "The Wandering Earth";

    public WanderingEarth(IEventBus modEventBus) {
        // Order matters: blocks first, then items (which need the block list),
        // then creative tabs (which need the item lists).
        ModBlocks.BLOCKS.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.TABS.register(modEventBus);
    }

    public static ResourceLocation rl(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
