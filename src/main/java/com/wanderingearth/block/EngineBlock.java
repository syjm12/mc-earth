package com.wanderingearth.block;

import com.wanderingearth.WanderingEarth;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.phys.BlockHitResult;
import java.util.List;

/**
 * A rotatable, fuel-burning engine block.
 *
 * <p>Behaviours, all of them real state changes rather than chat messages:
 * <ul>
 *   <li><b>Rotates.</b> Placed blocks face the player; right-clicking with an
 *       empty hand turns the engine 90 degrees around the Y axis.</li>
 *   <li><b>Burns lighter stones.</b> Right-clicking while holding a lighter
 *       stone loads it; dropped lighter stones within three blocks are absorbed
 *       automatically by {@link ModEngineBlockEntity#serverTick}.</li>
 *   <li><b>Spouts flame.</b> While {@link #LIT} the client emits flame and
 *       smoke particles out of the facing side every tick in
 *       {@link #animateTick}.</li>
 * </ul>
 *
 * <p>Signatures follow the official 1.21.1 Mojang mappings
 * ({@code useItemOn} returns {@link ItemInteractionResult},
 * {@code useWithoutItem} returns {@link InteractionResult}).
 */
public class EngineBlock extends Block implements EntityBlock {

    /** Horizontal facing, so a placed engine points somewhere sensible. */
    public static final DirectionProperty FACING = BlockStateProperties.HORIZONTAL_FACING;
    /** True while fuel is being burned; drives the particles and the sound. */
    public static final net.minecraft.world.level.block.state.properties.BooleanProperty LIT = BlockStateProperties.LIT;

    private final String name;
    private final String kind;

    public EngineBlock(BlockBehaviour.Properties props, String name, String kind) {
        super(props);
        this.name = name;
        this.kind = kind;
        BlockState state = this.defaultBlockState();
        if (state.hasProperty(FACING)) {
            state = state.setValue(FACING, Direction.NORTH);
        }
        if (state.hasProperty(LIT)) {
            state = state.setValue(LIT, false);
        }
        registerDefaultState(state);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, LIT);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState()
                .setValue(FACING, ctx.getHorizontalDirection().getOpposite())
                .setValue(LIT, false);
    }

    // ------------------------------------------------------------------
    // Block entity wiring
    // ------------------------------------------------------------------

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ModEngineBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide()) {
            return null;
        }
        return (lvl, pos, st, be) -> {
            if (be instanceof ModEngineBlockEntity engine) {
                ModEngineBlockEntity.serverTick(lvl, pos, st, engine);
            }
        };
    }

    // ------------------------------------------------------------------
    // Interaction
    // ------------------------------------------------------------------

    /** Load a lighter stone into the engine and light it. */
    @Override
    public ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                           Player player, InteractionHand hand, BlockHitResult hit) {
        if (stack == null || stack.isEmpty()) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        Item lighter = com.wanderingearth.registry.ModItems.LIGHTER_STONE.get();
        if (stack.getItem() != lighter) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (level.isClientSide()) {
            return ItemInteractionResult.SUCCESS;
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (!(be instanceof ModEngineBlockEntity engine)) {
            return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
        }
        if (!engine.insertFuel(1)) {
            player.displayClientMessage(
                    Component.translatable("message." + WanderingEarth.MOD_ID + ".engine_full")
                            .withStyle(ChatFormatting.RED), true);
            return ItemInteractionResult.FAIL;
        }
        stack.shrink(1);
        level.setBlockAndUpdate(pos, state.setValue(LIT, true));
        level.playSound((Player) null, pos, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 1.0f, 1.0f);
        player.displayClientMessage(
                Component.translatable("message." + WanderingEarth.MOD_ID + ".engine_loaded")
                        .withStyle(ChatFormatting.GOLD), true);
        return ItemInteractionResult.SUCCESS;
    }

    /** Turn the engine a quarter turn, or report its fuel level. */
    @Override
    public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (player.isShiftKeyDown()) {
            Direction next = state.getValue(FACING).getClockWise();
            level.setBlockAndUpdate(pos, state.setValue(FACING, next));
            level.playSound((Player) null, pos, SoundEvents.BLAZE_AMBIENT, SoundSource.BLOCKS, 0.4f, 1.4f);
            player.displayClientMessage(
                    Component.translatable("message." + WanderingEarth.MOD_ID + ".engine_turned",
                            next.getName()).withStyle(ChatFormatting.YELLOW), true);
            return InteractionResult.CONSUME;
        }
        if (be instanceof ModEngineBlockEntity engine) {
            player.displayClientMessage(
                    Component.translatable("message." + WanderingEarth.MOD_ID + ".engine_status",
                            engine.getFuel(), ModEngineBlockEntity.MAX_FUEL).withStyle(ChatFormatting.AQUA), true);
        }
        return InteractionResult.CONSUME;
    }

    // ------------------------------------------------------------------
    // Flame particles (client side, called by the level each tick)
    // ------------------------------------------------------------------

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(LIT)) {
            return;
        }
        Direction facing = state.getValue(FACING);
        double x = pos.getX() + 0.5 + facing.getStepX() * 0.62;
        double y = pos.getY() + 0.45;
        double z = pos.getZ() + 0.5 + facing.getStepZ() * 0.62;
        // Two flame streaks plus smoke, jittered so the plume does not look stamped.
        for (int i = 0; i < 2; i++) {
            level.addParticle(ParticleTypes.FLAME,
                    x + (random.nextDouble() - 0.5) * 0.18,
                    y + (random.nextDouble() - 0.5) * 0.18,
                    z + (random.nextDouble() - 0.5) * 0.18,
                    facing.getStepX() * 0.09,
                    0.045 + random.nextDouble() * 0.03,
                    facing.getStepZ() * 0.09);
        }
        level.addParticle(ParticleTypes.LARGE_SMOKE,
                x, y + 0.35, z,
                facing.getStepX() * 0.03, 0.05, facing.getStepZ() * 0.03);
        if (random.nextInt(6) == 0) {
            level.playLocalSound(x, y, z, SoundEvents.FIRE_AMBIENT, SoundSource.BLOCKS, 0.18f, 1.0f, false);
        }
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("lore." + WanderingEarth.MOD_ID + "." + name)
                .withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("lore." + WanderingEarth.MOD_ID + ".engine_hint")
                .withStyle(ChatFormatting.DARK_AQUA));
    }
}
