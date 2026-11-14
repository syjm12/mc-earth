package com.wanderingearth.registry;

import com.wanderingearth.WanderingEarth;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(WanderingEarth.MOD_ID);
    public static final Map<String, List<ItemLike>> BY_CATEGORY = new LinkedHashMap<>();
    /** 火石 / Lighter Stone: the fuel item the planetary engines inhale. */
    public static DeferredItem<Item> LIGHTER_STONE;

    static {
        // One BlockItem per block, so every block is obtainable.
        for (DeferredBlock<Block> b : ModBlocks.ALL) {
            String name = b.getId().getPath();
            java.util.function.Supplier<Block> bs = b::get;
            DeferredItem<net.minecraft.world.item.BlockItem> bi =
                    ITEMS.registerSimpleBlockItem(name, bs, new Item.Properties());
            add(ModBlocks.CATEGORY_OF.get(name), bi);
        }
        addPure("fusion_fuel_rod", "engines", new Item.Properties());
        addPure("heavy_nuclei_dust", "engines", new Item.Properties().stacksTo(64));
        addPure("heavy_element_sample", "engines", new Item.Properties().stacksTo(64));
        addPure("plasma_cell", "engines", new Item.Properties());
        addPure("sturdy_alloy_ingot", "engines", new Item.Properties().stacksTo(64));
        addPure("imperishable_alloy_ingot", "engines", new Item.Properties().stacksTo(64));
        addPure("mechanical_frame", "engines", new Item.Properties().stacksTo(64));
        addPure("planetary_engine_blueprint", "engines", new Item.Properties());
        addPure("earthworm_jerky", "undercity", new Item.Properties());
        addPure("undercity_access_card", "undercity", new Item.Properties());
        addPure("lottery_ticket", "undercity", new Item.Properties());
        addPure("han_duoduo_bag", "undercity", new Item.Properties());
        addPure("elevator_ticket", "elevator", new Item.Properties());
        addPure("cabin_safety_belt", "elevator", new Item.Properties());
        addPure("super_cable", "elevator", new Item.Properties());
        addPure("seed_sample", "elevator", new Item.Properties());
        addPure("driver_license", "vehicles", new Item.Properties());
        addPure("surface_helmet", "vehicles", new Item.Properties());
        addPure("cold_resistant_suit", "vehicles", new Item.Properties());
        addPure("lunar_eva_suit", "vehicles", new Item.Properties());
        addPure("exoskeleton_servo", "vehicles", new Item.Properties());
        addPure("benben_name_tag", "vehicles", new Item.Properties());
        addPure("service_rifle", "military", new Item.Properties());
        addPure("nuclear_launch_code", "military", new Item.Properties());
        addPure("cn171_11_badge", "military", new Item.Properties());
        addPure("lunar_rock_sample", "cosmos", new Item.Properties().stacksTo(64));
        addPure("jupiter_gas_sample", "cosmos", new Item.Properties());
        addPure("ice_core_sample", "cosmos", new Item.Properties().stacksTo(64));
        addPure("jupiter_ignition_plan", "cosmos", new Item.Properties());
        LIGHTER_STONE = addPure("lighter_stone", "props", new Item.Properties());
        addPure("vodka_bottle", "props", new Item.Properties());
        addPure("mountain_moving_blueprint", "props", new Item.Properties());
        addPure("digital_life_card", "quantum", new Item.Properties());
        addPure("precision_circuit", "quantum", new Item.Properties());
        addPure("data_card_blank", "quantum", new Item.Properties());
        addPure("moss_voice_chip", "quantum", new Item.Properties());
        addPure("moss_red_dot_module", "quantum", new Item.Properties());
        addPure("ma_zhao_id_card", "quantum", new Item.Properties());
        addPure("tu_hengyu_glasses", "quantum", new Item.Properties());
        // ---- v1.3.0: film-accurate additions (see docs/FILM_LORE.md) ---
        addPure("hanzi_hao_vehicle_card", "vehicles", new Item.Properties());
        addPure("digital_life_plan_permit", "quantum", new Item.Properties());
        addPure("moon_nuke_placement_map", "military", new Item.Properties());
        addPure("root_server_access_key", "quantum", new Item.Properties());
        addPure("emergency_plan_manual", "props", new Item.Properties());
        addPure("li_yiyi_toolbox", "vehicles", new Item.Properties());
        addPure("fire_seed_civilization_record", "props", new Item.Properties());
        addPure("tu_yaya_memory_chip", "quantum", new Item.Properties());
    }

    private static void add(String cat, ItemLike il) {
        BY_CATEGORY.computeIfAbsent(cat, k -> new ArrayList<>()).add(il);
    }

    private static DeferredItem<Item> addPure(String name, String cat, Item.Properties p) {
        DeferredItem<Item> it = ITEMS.registerSimpleItem(name, p);
        add(cat, it);
        return it;
    }

    private ModItems() {}
}
