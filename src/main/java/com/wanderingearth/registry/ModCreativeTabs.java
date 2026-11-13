package com.wanderingearth.registry;

import com.wanderingearth.WanderingEarth;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ItemLike;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.List;

public final class ModCreativeTabs {
    public static final DeferredRegister<CreativeModeTab> TABS =
            DeferredRegister.create(Registries.CREATIVE_MODE_TAB, WanderingEarth.MOD_ID);

    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> ENGINES =
            tab("engines");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> UNDERCITY =
            tab("undercity");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> ELEVATOR =
            tab("elevator");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> VEHICLES =
            tab("vehicles");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> MILITARY =
            tab("military");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> COSMOS =
            tab("cosmos");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> PROPS =
            tab("props");
    public static final DeferredHolder<CreativeModeTab, CreativeModeTab> QUANTUM =
            tab("quantum");

    private static DeferredHolder<CreativeModeTab, CreativeModeTab> tab(String cat) {
        return TABS.register(cat, () -> CreativeModeTab.builder(CreativeModeTab.Row.TOP, 0)
                .title(Component.translatable("itemGroup." + WanderingEarth.MOD_ID + "." + cat))
                .icon(icon(cat))
                .displayItems((params, output) -> {
                    List<ItemLike> list = ModItems.BY_CATEGORY.get(cat);
                    if (list != null) for (ItemLike il : list) output.accept(il);
                })
                .build());
    }

    private static java.util.function.Supplier<ItemStack> icon(String cat) {
        return () -> {
            List<ItemLike> list = ModItems.BY_CATEGORY.get(cat);
            ItemLike il = (list == null || list.isEmpty()) ? ModBlocks.ALL.get(0) : list.get(0);
            return new ItemStack(il);
        };
    }

    private ModCreativeTabs() {}
}
