package com.wanderingearth;

import com.wanderingearth.registry.ModBlockEntities;
import com.wanderingearth.registry.ModBlocks;
import com.wanderingearth.registry.ModCreativeTabs;
import com.wanderingearth.registry.ModItems;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModList;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.event.lifecycle.FMLClientSetupEvent;

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
        ModBlockEntities.BLOCK_ENTITIES.register(modEventBus);
        ModItems.ITEMS.register(modEventBus);
        ModCreativeTabs.TABS.register(modEventBus);

        modEventBus.addListener(this::clientSetup);
    }

    /**
     * Create's Ponder ("hold W to think") is optional integration. Referencing any
     * net.createmod.* class while Create is absent throws NoClassDefFoundError, so the
     * real work sits in a separate class loaded by name only when Create is present.
     */
    private void clientSetup(FMLClientSetupEvent event) {
        if (!ModList.get().isLoaded("create")) {
            return;
        }
        try {
            Class.forName("com.wanderingearth.compat.WanderingEarthPonder")
                    .getMethod("register")
                    .invoke(null);
        } catch (ClassNotFoundException ignored) {
            // Ponder support not bundled - fine, the mod works without it.
        } catch (ReflectiveOperationException ignored) {
            // Never let optional integration break the client.
        }
    }

    public static ResourceLocation rl(String path) {
        return ResourceLocation.fromNamespaceAndPath(MOD_ID, path);
    }
}
