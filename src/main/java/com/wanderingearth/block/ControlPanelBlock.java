package com.wanderingearth.block;

import com.wanderingearth.WanderingEarth;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
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
 * The engine control panel: one block that drives a whole field of engines.
 *
 * <p>When placed (or when sneak-right-clicked) it scans a cube around itself and
 * registers every {@link EngineBlock} it finds, up to
 * {@link ModControlPanelBlockEntity#MAX_LINKED}. While the panel itself receives
 * a redstone signal it pushes that signal into every registered engine, so one
 * lever lights an entire bank. Sneak-right-click cycles the scan radius.
 */
public class ControlPanelBlock extends Block implements EntityBlock {

    public static final DirectionProperty FACING = BlockStateProperties.HORIZONTAL_FACING;
    public static final BooleanProperty POWERED = BlockStateProperties.POWERED;

    private final String name;

    public ControlPanelBlock(BlockBehaviour.Properties props, String name) {
        super(props);
        this.name = name;
        BlockState state = this.defaultBlockState();
        if (state.hasProperty(FACING)) {
            state = state.setValue(FACING, net.minecraft.core.Direction.NORTH);
        }
        if (state.hasProperty(POWERED)) {
            state = state.setValue(POWERED, false);
        }
        registerDefaultState(state);
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING, POWERED);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext ctx) {
        return defaultBlockState()
                .setValue(FACING, ctx.getHorizontalDirection().getOpposite())
                .setValue(POWERED, false);
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pos, BlockState state) {
        return new ModControlPanelBlockEntity(pos, state);
    }

    @Override
    public <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level level, BlockState state, BlockEntityType<T> type) {
        if (level.isClientSide()) {
            return null;
        }
        return (lvl, pos, st, be) -> {
            if (be instanceof ModControlPanelBlockEntity panel) {
                ModControlPanelBlockEntity.serverTick(lvl, pos, st, panel);
            }
        };
    }

    /** Build the engine list as soon as the panel is put down. */
    @Override
    public void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean movedByPiston) {
        super.onPlace(state, level, pos, oldState, movedByPiston);
        if (level.isClientSide()) {
            return;
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof ModControlPanelBlockEntity panel) {
            panel.rescan(level, pos);
        }
    }

    /** Mirror our own redstone state and forward it to every registered engine. */
    @Override
    public void neighborChanged(BlockState state, Level level, BlockPos pos, Block neighborBlock, BlockPos neighborPos,
                                boolean movedByPiston) {
        super.neighborChanged(state, level, pos, neighborBlock, neighborPos, movedByPiston);
        if (level.isClientSide()) {
            return;
        }
        boolean powered = level.hasNeighborSignal(pos);
        if (state.getValue(POWERED) != powered) {
            level.setBlockAndUpdate(pos, state.setValue(POWERED, powered));
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof ModControlPanelBlockEntity panel) {
            panel.pushPower(level, pos, powered);
        }
    }

    @Override
    public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        BlockEntity be = level.getBlockEntity(pos);
        if (!(be instanceof ModControlPanelBlockEntity panel)) {
            return InteractionResult.PASS;
        }
        if (player.isShiftKeyDown()) {
            int radius = panel.cycleRadius(level, pos);
            level.playSound((Player) null, pos, SoundEvents.LEVER_CLICK, SoundSource.BLOCKS, 0.7f, 1.2f);
            player.displayClientMessage(
                    Component.translatable("message." + WanderingEarth.MOD_ID + ".panel_rescanned",
                            radius, panel.getLinkedCount()).withStyle(ChatFormatting.YELLOW), true);
            return InteractionResult.CONSUME;
        }
        boolean powered = state.getValue(POWERED);
        player.displayClientMessage(
                Component.translatable("message." + WanderingEarth.MOD_ID + ".panel_status",
                        panel.getRadius(), panel.getLinkedCount(),
                        Component.translatable("message." + WanderingEarth.MOD_ID
                                + (powered ? ".panel_on" : ".panel_off")))
                        .withStyle(ChatFormatting.AQUA), true);
        return InteractionResult.CONSUME;
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext ctx, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("lore." + WanderingEarth.MOD_ID + "." + name)
                .withStyle(ChatFormatting.GRAY));
        tooltip.add(Component.translatable("lore." + WanderingEarth.MOD_ID + ".panel_hint")
                .withStyle(ChatFormatting.DARK_AQUA));
    }
}
