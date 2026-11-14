package com.wanderingearth.client;

import com.wanderingearth.WanderingEarth;
import com.wanderingearth.registry.ModBlockEntities;

import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.client.event.EntityRenderersEvent;

/**
 * Client only hooks.
 *
 * <p>The engine beam is drawn by {@link EngineBeamRenderer}, which needs a block
 * entity renderer. It is registered here on the mod event bus: the
 * {@code EntityRenderersEvent.RegisterRenderers} event is a mod bus event, so it
 * must not be posted to the game bus.</p>
 *
 * <p>Note that this lives in its own class instead of inside
 * {@link WanderingEarth#clientSetup}: that setup hook returns early when Create
 * is not installed, and the beam renderer must be registered either way.</p>
 */
@EventBusSubscriber(modid = WanderingEarth.MOD_ID, value = Dist.CLIENT, bus = EventBusSubscriber.Bus.MOD)
public final class WanderingEarthClient {

    private WanderingEarthClient() {}

    @SubscribeEvent
    public static void registerRenderers(EntityRenderersEvent.RegisterRenderers event) {
        event.registerBlockEntityRenderer(ModBlockEntities.ENGINE.get(), context -> new EngineBeamRenderer());
    }
}
