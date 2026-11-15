package com.wanderingearth.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import com.wanderingearth.block.EngineBlock;

import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Draws the plasma beam of a planetary engine the way a vanilla beacon draws its
 * beam: one straight, steady shaft of light that is rendered by the block entity
 * renderer instead of being sprayed out as particles.
 *
 * <p>Before 1.4.0 the beam was a trail of {@code END_ROD} particles emitted from
 * {@code Block.animateTick}. The client calls that hook on random blocks only, so
 * the trail flickered instead of standing still. Rendering the shaft through the
 * block entity renderer makes it frame perfect, and lets the vanilla beacon beam
 * shader do the work.</p>
 */
public class EngineBeamRenderer implements BlockEntityRenderer {

    /** The vanilla beacon beam texture, reused so the beam blends into the world. */
    private static final ResourceLocation BEAM_TEXTURE =
            ResourceLocation.fromNamespaceAndPath("minecraft", "textures/entity/beacon_beam.png");

    /** Bright core of the shaft. */
    private static final int CORE_COLOR = 0xFFE8F4FF;

    /** Soft halo around the core, drawn with the translucent beacon beam pass. */
    private static final int GLOW_COLOR = 0x20E8F4FF;

    private static final float CORE_RADIUS = 0.16F;
    private static final float GLOW_RADIUS = 0.30F;

    /** Height of the nozzle inside the block. */
    private static final double NOZZLE_HEIGHT = 0.45D;

    /** How far the nozzle sticks out of the block face. */
    private static final double NOZZLE_OFFSET = 0.62D;

    @Override
    public void render(BlockEntity blockEntity, float partialTick, PoseStack poseStack,
                        MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        BlockState state = blockEntity.getBlockState();
        if (!state.getValue(EngineBlock.LIT)) {
            return;
        }
        Direction facing = state.getValue(EngineBlock.FACING);
        int length = beamLength(blockEntity, facing);
        if (length <= 0) {
            return;
        }

        poseStack.pushPose();
        // Block entity renderers start at the minimum corner of the block, so the
        // centre of the block sits at (0.5, 0.5, 0.5) and the nozzle is a little
        // further along the facing direction.
        poseStack.translate(0.5D + facing.getStepX() * NOZZLE_OFFSET,
                NOZZLE_HEIGHT,
                0.5D + facing.getStepZ() * NOZZLE_OFFSET);

        // The pose carries every translation applied so far: the level renderer's
        // block-to-camera offset plus our nozzle offset. addVertex(pose, ...) bakes
        // that matrix into each vertex; the plain addVertex(float,float,float)
        // overload does NOT and would leave the shaft stuck at the camera origin.
        PoseStack.Pose pose = poseStack.last();

        VertexConsumer core = bufferSource.getBuffer(RenderType.beaconBeam(BEAM_TEXTURE, false));
        drawShaft(core, pose, facing, length, CORE_RADIUS, CORE_COLOR);

        VertexConsumer glow = bufferSource.getBuffer(RenderType.beaconBeam(BEAM_TEXTURE, true));
        drawShaft(glow, pose, facing, length, GLOW_RADIUS, GLOW_COLOR);

        poseStack.popPose();
    }

    /**
     * Walks along the facing axis until something solid stops the beam, exactly
     * like the particle beam of 1.3.0 did.
     */
    private int beamLength(BlockEntity blockEntity, Direction facing) {
        Level level = blockEntity.getLevel();
        if (level == null) {
            return EngineBlock.BEAM_LENGTH;
        }
        BlockPos pos = blockEntity.getBlockPos();
        int length = EngineBlock.BEAM_LENGTH;
        for (int step = 1; step <= EngineBlock.BEAM_LENGTH; step++) {
            BlockPos probe = pos.relative(facing, step);
            if (!level.getBlockState(probe).isAir()) {
                length = step - 1;
                break;
            }
        }
        return length;
    }

    /**
     * Draws a square shaft of light along the facing axis. Every side is emitted
     * twice, once in each winding order, so the beam is visible from any angle no
     * matter how the beacon beam render type handles culling.
     */
    private void drawShaft(VertexConsumer consumer, PoseStack.Pose pose, Direction facing,
                           int length, float radius, int argb) {
        double dx = facing.getStepX();
        double dz = facing.getStepZ();

        // Right hand side of the beam when looking along the facing direction.
        double rx = dz;
        double rz = -dx;

        // The four corners of the cross section of the shaft.
        double[] cornerX = { rx * radius, -rx * radius, -rx * radius, rx * radius };
        double[] cornerY = { radius, radius, -radius, -radius };
        double[] cornerZ = { rz * radius, -rz * radius, -rz * radius, rz * radius };

        double endX = dx * length;
        double endZ = dz * length;

        for (int side = 0; side < 4; side++) {
            int next = (side + 1) % 4;

            // Outward normal of this side, taken from the diagonal of the face.
            float normalX = (float) ((cornerX[side] + cornerX[next]) / (2.0D * radius));
            float normalY = (float) ((cornerY[side] + cornerY[next]) / (2.0D * radius));
            float normalZ = (float) ((cornerZ[side] + cornerZ[next]) / (2.0D * radius));

            float u1 = 0.25F;
            float u2 = 0.75F;

            vertex(consumer, pose, cornerX[side], cornerY[side], cornerZ[side], u1, 0.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, cornerX[next], cornerY[next], cornerZ[next], u2, 0.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, endX + cornerX[next], cornerY[next], endZ + cornerZ[next], u2, 1.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, endX + cornerX[side], cornerY[side], endZ + cornerZ[side], u1, 1.0F, normalX, normalY, normalZ, argb);

            // Same quad with the opposite winding.
            vertex(consumer, pose, endX + cornerX[side], cornerY[side], endZ + cornerZ[side], u1, 1.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, endX + cornerX[next], cornerY[next], endZ + cornerZ[next], u2, 1.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, cornerX[next], cornerY[next], cornerZ[next], u2, 0.0F, normalX, normalY, normalZ, argb);
            vertex(consumer, pose, cornerX[side], cornerY[side], cornerZ[side], u1, 0.0F, normalX, normalY, normalZ, argb);
        }
    }

    private void vertex(VertexConsumer consumer, PoseStack.Pose pose, double x, double y, double z,
                        float u, float v, float normalX, float normalY, float normalZ, int argb) {
        consumer.addVertex(pose, (float) x, (float) y, (float) z)
                .setColor(argb)
                .setUv(u, v)
                .setOverlay(OverlayTexture.NO_OVERLAY)
                .setLight(15728880)
                .setNormal(pose, normalX, normalY, normalZ);
    }
}
