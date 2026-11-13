package com.wanderingearth.block;

import com.wanderingearth.WanderingEarth;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

import java.util.List;
import java.util.Random;

/**
 * A themed block: shows lore on hover, and an in-world message when used.
 * A handful of "kind" values give authentic little interactions (MOSS lines,
 * the undercity lottery, the countdown display, the traffic notice...).
 */
public class ModBlock extends Block {
    private static final String[] MOSS_LINES = {
        "MOSS: 让人类永远保持理智，确实是一种奢求。",
        "MOSS: MOSS 从未叛逃。",
        "MOSS: 550W 倒过来念，就是 MOSS。",
        "MOSS: 我们的人，一定能完成任务。"
    };
    private static final Random RANDOM = new Random();

    private final String name;
    private final String kind;

    public ModBlock(BlockBehaviour.Properties props, String name, String kind) {
        super(props);
        this.name = name;
        this.kind = kind;
    }

    @Override
    public void appendHoverText(ItemStack stack, Item.TooltipContext ctx,
                                List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("lore." + WanderingEarth.MOD_ID + "." + name)
                .withStyle(ChatFormatting.GRAY));
    }

    @Override
    public InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos,
                                            Player player, BlockHitResult hit) {
        if (!level.isClientSide()) {
            player.displayClientMessage(message(), true);
        }
        return InteractionResult.sidedSuccess(level.isClientSide());
    }

    private Component message() {
        switch (kind) {
            case "moss":
                return Component.literal(MOSS_LINES[RANDOM.nextInt(MOSS_LINES.length)])
                        .withStyle(ChatFormatting.AQUA);
            case "lottery":
                return Component.translatable(RANDOM.nextInt(3) == 0
                        ? "message.wandering_earth.lottery_win"
                        : "message.wandering_earth.lottery_lose");
            case "countdown":
                return Component.literal("T-" + (RANDOM.nextInt(900) + 100) + " s")
                        .withStyle(ChatFormatting.RED);
            case "traffic":
                return Component.translatable("message.wandering_earth.traffic")
                        .withStyle(ChatFormatting.YELLOW);
            case "alert":
                return Component.translatable("message.wandering_earth.alert")
                        .withStyle(ChatFormatting.RED);
            case "ignition":
                return Component.translatable("message.wandering_earth.ignition")
                        .withStyle(ChatFormatting.GOLD);
            case "engine":
                return Component.translatable("message.wandering_earth.engine")
                        .withStyle(ChatFormatting.GREEN);
            default:
                return Component.translatable("lore." + WanderingEarth.MOD_ID + "." + name);
        }
    }
}
