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
import net.minecraft.world.level.block.EntityBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.BooleanProperty;
import net.minecraft.world.level.block.state.properties.DirectionProperty;
import net.minecraft.world.phys.BlockHitResult;
import java.util.List;

/**
 * A rotatable, fuel-burning engine block.
 *
 * <p>Behaviours, all of them real state changes rather than chat messages:
 * <ul>
 *   <li><b>Rotates.</b> Placed blocks face the player; sneak-right-clicking with
 *       an empty hand turns the engine 90 degrees around the Y axis.</li>
 *   <li><b>Loads lighter stones.</b> Right-clicking while holding a lighter
 *       stone loads it; dropped lighter stones within three blocks are absorbed
 *       automatically by {@link ModEngineBlockEntity#serverTick}.</li>
 *   <li><b>Fires on redstone.</b> A loaded engine only ignites while it receives
 *       a neighbour signal (or a signal pushed by a {@link ControlPanelBlock}),
 *       and goes out the moment the signal drops.</li>
 *   <li><b>Spouts a beam.</b> While {@link #LIT} the client emits a plasma beam
 *       of {@code END_ROD} / {@code ELECTRIC_SPARK} particles out of the facing
 *       side, up to 12 blocks or until it hits something solid.</li>
 * </ul>
 *
 * <p>Signatures follow the official 1.21.1 Mojang mappings
 * ({@code useItemOn} returns {@link ItemInteractionResult},
 * {@code useWithoutItem} returns {@link InteractionResult}).
 */
public class EngineBlock extends Block implements EntityBlock {

    /** Horizontal facing, so a placed engine points somewhere sensible. */
    public static final DirectionProperty FACING = BlockStateProperties.HORIZONTAL_FACING;
    /** True while the engine is actually firing; driven by redstone, not by loading. */
    public static final BooleanProperty LIT = BlockStateProperties.LIT;

    /** How far the plasma beam reaches before it is cut short by a solid block. */
    public static final int BEAM_LENGTH = 12;

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
    // Redstone
    // ------------------------------------------------------------------

    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock, BlockPos neighborPos,
                                boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        if (level.isClientSide()) {
            return;
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (!(be instanceof ModEngineBlockEntity engine)) {
            return;
        }
        // A neighbour signal turns the engine on; a control panel can also push
        // one in, which is why the block entity remembers it separately.
        boolean powered = level.hasNeighborSignal(pos) || engine.hasRemotePower();
        boolean wantLit = powered && engine.getFuel() > 0;
        if (state.getValue(LIT) != wantLit) {
            level.setBlockAndUpdate(pos, state.setValue(LIT, wantLit));
        }
    }

    // ------------------------------------------------------------------
    // Interaction
    // ------------------------------------------------------------------

    /** Load a lighter stone into the engine. Lighting happens on redstone. */
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
        level.playSound((Player) null, pos, SoundEvents.FIRECHARGE_USE, SoundSource.BLOCKS, 1.0f, 1.0f);
        player.displayClientMessage(
                Component.translatable("message." + WanderingEarth.MOD_ID + ".engine_loaded",
                        engine.getFuel(), ModEngineBlockEntity.MAX_FUEL).withStyle(ChatFormatting.GOLD), true);
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
    // Beam particles (client side, called by the level each tick)
    // ------------------------------------------------------------------

    @Override
    public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource random) {
        if (!state.getValue(LIT)) {
            return;
        }
        Direction facing = state.getValue(FACING);
        double ox = pos.getX() + 0.5 + facing.getStepX() * 0.62;
        double oy = pos.getY() + 0.45;
        double oz = pos.getZ() + 0.5 + facing.getStepZ() * 0.62;

        // Mouth glow: a tight cluster right at the nozzle.
        for (int i = 0; i < 2; i++) {
            level.addParticle(ParticleTypes.SMALL_FLAME,
                    ox + (random.nextDouble() - 0.5) * 0.16,
                    oy + (random.nextDouble() - 0.5) * 0.16,
                    oz + (random.nextDouble() - 0.5) * 0.16,
                    facing.getStepX() * 0.02, 0.02, facing.getStepZ() * 0.02);
        }

        // The beam itself: march along the facing axis until something solid.
        int reach = BEAM_LENGTH;
        for (int step = 1; step <= BEAM_LENGTH; step++) {
            BlockPos probe = pos.relative(facing, step);
            if (!level.getBlockState(probe).isAir()) {
                reach = step - 1;
                break;
            }
        }
        if (reach <= 0) {
            return;
        }
        for (int step = 1; step <= reach; step++) {
            double along = step + 0.5;
            // Wobble grows with distance so the column reads as a beam, not a ruler.
            double wobble = 0.02 + (double) step / reach * 0.06;
            double x = pos.getX() + 0.5 + facing.getStepX() * along + (random.nextDouble() - 0.5) * wobble;
            double y = pos.getY() + 0.45 + (random.nextDouble() - 0.5) * wobble;
            double z = pos.getZ() + 0.5 + facing.getStepZ() * along + (random.nextDouble() - 0.5) * wobble;
            level.addParticle(ParticleTypes.END_ROD, x, y, z, 0.0, 0.0, 0.0);
            if (random.nextInt(3) == 0) {
                level.addParticle(ParticleTypes.ELECTRIC_SPARK, x, y, z, 0.0, 0.0, 0.0);
            }
        }
        if (random.nextInt(8) == 0) {
            level.playLocalSound(ox, oy, oz, SoundEvents.BLAZE_SHOOT, SoundSource.BLOCKS, 0.22f, 0.7f, false);
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
