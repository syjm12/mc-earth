package com.wanderingearth.compat;

import com.wanderingearth.WanderingEarth;
import net.createmod.ponder.api.registration.PonderPlugin;
import net.createmod.ponder.api.registration.PonderSceneRegistrationHelper;
import net.createmod.ponder.api.scene.PonderStoryBoard;
import net.createmod.ponder.api.scene.SceneBuilder;
import net.createmod.ponder.api.scene.SceneBuildingUtil;
import net.createmod.ponder.foundation.PonderIndex;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.phys.Vec3;

/**
 * Optional Create "Ponder" integration (hold W on an item to open the scene).
 *
 * <p>This class is only ever loaded reflectively from WanderingEarth#clientSetup,
 * and only when Create is installed. That keeps net.createmod.* off the classpath
 * of players who run this mod standalone.
 *
 * <p>Each scene is backed by a real structure file under
 * {@code assets/wandering_earth/ponder/<scene>.nbt}: a small stone platform with
 * the machine in the middle, so the animation has something to point at.
 */
public final class WanderingEarthPonder implements PonderPlugin {

    public static void register() {
        PonderIndex.addPlugin(new WanderingEarthPonder());
    }

    @Override
    public String getModId() {
        return WanderingEarth.MOD_ID;
    }

    @Override
    public void registerScenes(PonderSceneRegistrationHelper<ResourceLocation> helper) {
        helper.addStoryBoard(item("planetary_engine_core"), "planetary_engine",
                WanderingEarthPonder::engineScene);
        helper.addStoryBoard(item("lighter_socket"), "lighter_socket",
                WanderingEarthPonder::lighterScene);
        helper.addStoryBoard(item("moss_mainframe"), "moss_mainframe",
                WanderingEarthPonder::mossScene);
    }

    private static ResourceLocation item(String path) {
        return ResourceLocation.fromNamespaceAndPath(WanderingEarth.MOD_ID, path);
    }

    private static void engineScene(SceneBuilder scene, SceneBuildingUtil util) {
        scene.title("planetary_engine", "Planetary Engine");
        scene.configureBasePlate(0, 0, 5);
        scene.scaleSceneView(0.85f);
        scene.idle(10);

        // The schematic holds the engine at (2, 1, 2); show it rising out of the plate.
        BlockPos engine = util.grid().at(2, 1, 2);
        scene.world().showSection(util.select().position(2, 1, 2), Direction.DOWN);
        scene.idle(10);

        scene.overlay().showText(70)
                .text("重型聚变反应堆烧的是石头，吐出来的是等离子体。")
                .pointAt(util.vector().centerOf(2, 1, 2))
                .placeNearTarget();
        scene.idle(80);

        // Light it: flip lit=false -> lit=true and spit flame out of the nozzle.
        scene.world().cycleBlockProperty(engine, net.minecraft.world.level.block.state.properties.BlockStateProperties.LIT);
        Vec3 front = util.vector().topOf(2, 1, 2);
        scene.effects().emitParticles(front,
                scene.effects().simpleParticleEmitter(ParticleTypes.FLAME, front), 1.0f, 60);

        scene.overlay().showText(70)
                .text("往火石插口里放一块火石，发动机就点着了。")
                .pointAt(front)
                .placeNearTarget();
        scene.idle(80);
        scene.effects().indicateSuccess(engine);
        scene.idle(20);

        scene.overlay().showText(70)
                .text("空手潜行右键可以改变喷口朝向。")
                .independent();
        scene.idle(60);

        scene.world().hideSection(util.select().position(2, 1, 2), Direction.UP);
        scene.idle(20);
        scene.markAsFinished();
    }

    private static void lighterScene(SceneBuilder scene, SceneBuildingUtil util) {
        scene.title("lighter_socket", "Lighter Socket");
        scene.configureBasePlate(0, 0, 5);
        scene.idle(10);

        BlockPos socket = util.grid().at(2, 1, 2);
        scene.world().showSection(util.select().position(2, 1, 2), Direction.DOWN);
        scene.idle(10);

        scene.overlay().showText(70)
                .text("火石是发动机的燃料。掉在附近的火石会被自动吸入。")
                .pointAt(util.vector().centerOf(2, 1, 2))
                .placeNearTarget();
        scene.idle(80);
        scene.effects().indicateSuccess(socket);
        scene.idle(40);
        scene.markAsFinished();
    }

    private static void mossScene(SceneBuilder scene, SceneBuildingUtil util) {
        scene.title("moss_mainframe", "MOSS");
        scene.configureBasePlate(0, 0, 5);
        scene.idle(10);

        scene.world().showSection(util.select().position(2, 1, 2), Direction.DOWN);
        scene.idle(10);

        scene.overlay().showText(80)
                .text("MOSS 从不叛逃。")
                .pointAt(util.vector().centerOf(2, 1, 2))
                .placeNearTarget();
        scene.idle(90);
        scene.markAsFinished();
    }

    private WanderingEarthPonder() {
    }
}
