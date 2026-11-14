package com.wanderingearth.block;

import com.wanderingearth.registry.ModBlockEntities;
import com.wanderingearth.registry.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import java.util.List;

/**
 * Persistent state for the planetary engine family.
 *
 * <p>Holds the lighter stone fuel load, the burn timer and the auto-load
 * cooldown, and absorbs dropped {@code lighter_stone} items that land within
 * three blocks of the engine (that is the "automatically loaded with a lighter
 * stone" behaviour). Everything is stored in NBT, so the load survives a
 * world reload.
 *
 * <p>All values written here match the official 1.21.1 signatures
 * ({@code saveAdditional}/{@code loadAdditional} take a
 * {@link HolderLookup.Provider}).
 */
public class ModEngineBlockEntity extends BlockEntity {

    /** Upper bound of lighter stones one engine block can hold. */
    public static final int MAX_FUEL = 64;
    /** Ticks one lighter stone burns for. */
    public static final int BURN_TICKS = 40;
    /** Ticks between two automatic pick-up attempts. */
    public static final int AUTO_LOAD_INTERVAL = 20;

    private int fuel;
    private int burnTimer;
    private int autoLoadTimer;

    public ModEngineBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.ENGINE.get(), pos, state);
    }

    /** Server side only: driven by {@link EngineBlock#getTicker}. */
    public static void serverTick(Level level, BlockPos pos, BlockState state, ModEngineBlockEntity engine) {
        if (level.isClientSide()) {
            return;
        }

        if (engine.autoLoadTimer > 0) {
            engine.autoLoadTimer--;
        } else {
            engine.autoLoadTimer = AUTO_LOAD_INTERVAL;
            engine.tryAbsorbLighter(level, pos);
        }

        if (!state.getValue(EngineBlock.LIT)) {
            return;
        }
        if (engine.fuel <= 0) {
            level.setBlockAndUpdate(pos, state.setValue(EngineBlock.LIT, false));
            return;
        }
        engine.burnTimer++;
        if (engine.burnTimer >= BURN_TICKS) {
            engine.burnTimer = 0;
            engine.fuel--;
            engine.setChanged();
        }
    }

    private void tryAbsorbLighter(Level level, BlockPos pos) {
        if (fuel >= MAX_FUEL) {
            return;
        }
        List<Entity> found = level.getEntities((Entity) null, new AABB(pos).inflate(3.0),
                e -> e instanceof ItemEntity);
        if (found == null) {
            return;
        }
        for (Entity entity : found) {
            ItemEntity drop = (ItemEntity) entity;
            ItemStack stack = drop.getItem();
            if (stack == null || stack.isEmpty()) {
                continue;
            }
            if (!stack.is(ModItems.LIGHTER_STONE.get())) {
                continue;
            }
            int moved = Math.min(stack.getCount(), MAX_FUEL - fuel);
            if (moved <= 0) {
                return;
            }
            fuel += moved;
            stack.shrink(moved);
            if (stack.isEmpty()) {
                drop.discard();
            }
            setChanged();
            return;
        }
    }

    /** Manual insert from a right click. Returns true when fuel was accepted. */
    public boolean insertFuel(int amount) {
        if (fuel >= MAX_FUEL) {
            return false;
        }
        fuel = Math.min(MAX_FUEL, fuel + amount);
        setChanged();
        return true;
    }

    public int getFuel() {
        return fuel;
    }

    public boolean isBurning() {
        return fuel > 0;
    }

    @Override
    public void saveAdditional(CompoundTag tag, HolderLookup.Provider provider) {
        super.saveAdditional(tag, provider);
        tag.putInt("Fuel", fuel);
        tag.putInt("BurnTimer", burnTimer);
    }

    @Override
    public void loadAdditional(CompoundTag tag, HolderLookup.Provider provider) {
        super.loadAdditional(tag, provider);
        fuel = tag.getInt("Fuel");
        burnTimer = tag.getInt("BurnTimer");
    }
}
