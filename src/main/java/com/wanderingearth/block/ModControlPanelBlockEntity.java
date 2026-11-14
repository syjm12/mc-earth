package com.wanderingearth.block;

import com.wanderingearth.registry.ModBlockEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/**
 * The control panel's brain: a scan radius, the list of engines it found, and
 * the redstone state it last pushed into them.
 *
 * <p>Engine positions are stored as packed {@code long}s
 * ({@link BlockPos#asLong()}), which is what makes the "area selection" idea
 * cheap to persist: one long array covers up to {@link #MAX_LINKED} machines.
 */
public class ModControlPanelBlockEntity extends BlockEntity {

    /** Selectable scan radii, in blocks. Sneak-right-click cycles through them. */
    public static final int[] RADII = {8, 16, 32};
    /** Ticks between two automatic re-pushes of the current power state. */
    public static final int PUSH_INTERVAL = 20;
    /** Cap on how many engines one panel may drive. */
    public static final int MAX_LINKED = 256;

    private int radius = RADII[1];
    private int pushTimer;
    private long[] linked = new long[0];
    private boolean pushedPower;

    public ModControlPanelBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.PANEL.get(), pos, state);
    }

    public static void serverTick(Level level, BlockPos pos, BlockState state, ModControlPanelBlockEntity panel) {
        if (level.isClientSide()) {
            return;
        }
        panel.pushTimer--;
        if (panel.pushTimer > 0) {
            return;
        }
        panel.pushTimer = PUSH_INTERVAL;
        boolean powered = level.hasNeighborSignal(pos);
        if (powered != panel.pushedPower || panel.linked.length == 0) {
            panel.pushPower(level, pos, powered);
        }
    }

    /** Walk the cube around the panel and remember every engine in it. */
    public void rescan(Level level, BlockPos pos) {
        java.util.List<Long> found = new java.util.ArrayList<>();
        for (int dx = -radius; dx <= radius; dx++) {
            for (int dy = -radius; dy <= radius; dy++) {
                for (int dz = -radius; dz <= radius; dz++) {
                    BlockPos cursor = pos.offset(dx, dy, dz);
                    if (!level.isLoaded(cursor)) {
                        continue;
                    }
                    if (level.getBlockState(cursor).getBlock() instanceof EngineBlock) {
                        found.add(BlockPos.asLong(cursor.getX(), cursor.getY(), cursor.getZ()));
                        if (found.size() >= MAX_LINKED) {
                            break;
                        }
                    }
                }
            }
        }
        long[] next = new long[found.size()];
        for (int i = 0; i < next.length; i++) {
            next[i] = found.get(i);
        }
        linked = next;
        setChanged();
        pushPower(level, pos, level.hasNeighborSignal(pos));
    }

    /** Advance to the next radius and rescan. Returns the new radius. */
    public int cycleRadius(Level level, BlockPos pos) {
        int idx = 0;
        for (int i = 0; i < RADII.length; i++) {
            if (RADII[i] == radius) {
                idx = i;
                break;
            }
        }
        radius = RADII[(idx + 1) % RADII.length];
        rescan(level, pos);
        return radius;
    }

    /** Hand the current power state to every engine this panel registered. */
    public void pushPower(Level level, BlockPos pos, boolean powered) {
        pushedPower = powered;
        for (long packed : linked) {
            BlockPos target = BlockPos.of(packed);
            if (!level.isLoaded(target)) {
                continue;
            }
            if (level.getBlockEntity(target) instanceof ModEngineBlockEntity engine) {
                engine.setRemotePower(powered);
            }
        }
        setChanged();
    }

    public int getRadius() {
        return radius;
    }

    public int getLinkedCount() {
        return linked.length;
    }

    @Override
    public void saveAdditional(CompoundTag tag, HolderLookup.Provider provider) {
        super.saveAdditional(tag, provider);
        tag.putInt("Radius", radius);
        tag.putLongArray("Linked", linked);
        tag.putBoolean("PushedPower", pushedPower);
    }

    @Override
    public void loadAdditional(CompoundTag tag, HolderLookup.Provider provider) {
        super.loadAdditional(tag, provider);
        int r = tag.getInt("Radius");
        radius = r > 0 ? r : RADII[1];
        linked = tag.getLongArray("Linked");
        pushedPower = tag.getBoolean("PushedPower");
    }
}
