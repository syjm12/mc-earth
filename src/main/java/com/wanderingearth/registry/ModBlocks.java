package com.wanderingearth.registry;

import com.wanderingearth.WanderingEarth;
import com.wanderingearth.block.ModBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.neoforged.neoforge.registries.DeferredBlock;
import net.neoforged.neoforge.registries.DeferredRegister;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;

public final class ModBlocks {
    public static final DeferredRegister.Blocks BLOCKS = DeferredRegister.createBlocks(WanderingEarth.MOD_ID);
    public static final List<DeferredBlock<Block>> ALL = new ArrayList<>();
    public static final Map<String, String> CATEGORY_OF = new LinkedHashMap<>();

    public static final DeferredBlock<Block> PLANETARY_ENGINE_CASING = reg("planetary_engine_casing", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> PLANETARY_ENGINE_CORE = reg("planetary_engine_core", "engines", 15, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> PLANETARY_ENGINE_NOZZLE = reg("planetary_engine_nozzle", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> PLASMA_BEAM_EMITTER = reg("plasma_beam_emitter", "engines", 15, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ENGINE_LIGHT_PILLAR = reg("engine_light_pillar", "engines", 15, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> EQUATORIAL_TURNING_ENGINE = reg("equatorial_turning_engine", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> THRUST_ENGINE = reg("thrust_engine", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> HEAVY_FUSION_REACTOR = reg("heavy_fusion_reactor", "engines", 13, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> STONE_BURNER = reg("stone_burner", "engines", 9, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ENGINE_MOUNTAIN_BASE = reg("engine_mountain_base", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ENGINE_UNDERCITY = reg("engine_undercity", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> LIGHTER_SOCKET = reg("lighter_socket", "engines", 7, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> IGNITION_CORE = reg("ignition_core", "engines", 11, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ENGINE_STATUS_MONITOR = reg("engine_status_monitor", "engines", 0, "engine", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ENGINE_NUMBER_PLATE = reg("engine_number_plate", "engines", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UNDERCITY_ENTRANCE = reg("undercity_entrance", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UNDERCITY_BLAST_DOOR = reg("undercity_blast_door", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UNDERCITY_HABITAT = reg("undercity_habitat", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> CAPSULE_APARTMENT = reg("capsule_apartment", "undercity", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> HIBERNATION_POD = reg("hibernation_pod", "undercity", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> ECO_CYCLE_UNIT = reg("eco_cycle_unit", "undercity", 7, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> LOTTERY_TERMINAL = reg("lottery_terminal", "undercity", 0, "lottery", 7.0f, 12.0f);
    public static final DeferredBlock<Block> RATION_DISPENSER = reg("ration_dispenser", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UNDERCITY_SCHOOL_DESK = reg("undercity_school_desk", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ARTIFICIAL_SUN_LAMP = reg("artificial_sun_lamp", "undercity", 15, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> UNDERCITY_VENT = reg("undercity_vent", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> DISTRICT_SIGN_BEIJING_3 = reg("district_sign_beijing_3", "undercity", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> SPACE_ELEVATOR_BASE = reg("space_elevator_base", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ELEVATOR_CABLE = reg("elevator_cable", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ELEVATOR_RAIL = reg("elevator_rail", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ELEVATOR_CABIN = reg("elevator_cabin", "elevator", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> CABIN_SEAT = reg("cabin_seat", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> COUNTERWEIGHT = reg("counterweight", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ARK_STATION_BLOCK = reg("ark_station_block", "elevator", 9, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> NAVIGATOR_STATION_BLOCK = reg("navigator_station_block", "elevator", 9, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> SEED_VAULT = reg("seed_vault", "elevator", 7, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> CIVILIZATION_ARCHIVE = reg("civilization_archive", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ELEVATOR_DEFENSE_TURRET = reg("elevator_defense_turret", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ELEVATOR_WRECKAGE = reg("elevator_wreckage", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> GAGARIN_ERA_PLAQUE = reg("gagarin_era_plaque", "elevator", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> HEAVY_HAULER = reg("heavy_hauler", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> HAULER_DRIVE_BALL = reg("hauler_drive_ball", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> CARGO_CONTAINER = reg("cargo_container", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> LIGHTER_TRANSPORT_RACK = reg("lighter_transport_rack", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> EXOSKELETON_FRAME = reg("exoskeleton_frame", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ROBOT_DOG_BENBEN = reg("robot_dog_benben", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UAV_DRONE = reg("uav_drone", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> TOWER_CRANE = reg("tower_crane", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> TUNNEL_BORING_MACHINE = reg("tunnel_boring_machine", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> LUNAR_ROVER = reg("lunar_rover", "vehicles", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UEG_SOLDIER_MARKER = reg("ueg_soldier_marker", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> CN171_11_PATCH = reg("cn171_11_patch", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> GATLING_UNIT = reg("gatling_unit", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> INTERCEPTOR_MISSILE = reg("interceptor_missile", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> LUNAR_NUKE = reg("lunar_nuke", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> PHASED_ARRAY_DETONATOR = reg("phased_array_detonator", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> MANUAL_DETONATOR = reg("manual_detonator", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> REBEL_INSIGNIA = reg("rebel_insignia", "military", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> HELIUM_FLASH_BEACON = reg("helium_flash_beacon", "military", 13, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> COUNTDOWN_DISPLAY = reg("countdown_display", "military", 0, "countdown", 7.0f, 12.0f);
    public static final DeferredBlock<Block> JUPITER_GREAT_RED_SPOT = reg("jupiter_great_red_spot", "cosmos", 9, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> JUPITER_GRAVITY_INDICATOR = reg("jupiter_gravity_indicator", "cosmos", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> LUNAR_SURFACE_REGOLITH = reg("lunar_surface_regolith", "cosmos", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> PROXIMA_CENTAURI_CHART = reg("proxima_centauri_chart", "cosmos", 11, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> FROZEN_GROUND = reg("frozen_ground", "cosmos", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> ICE_CRUST = reg("ice_crust", "cosmos", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> SNOW_DRIFT = reg("snow_drift", "cosmos", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> ATMOSPHERE_VENT = reg("atmosphere_vent", "cosmos", 0, "", 5.0f, 8.0f);
    public static final DeferredBlock<Block> MAGMA_FLOOD = reg("magma_flood", "cosmos", 15, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UEG_FLAG = reg("ueg_flag", "props", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> UEG_EMBLEM = reg("ueg_emblem", "props", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ASTRONAUT_BADGE = reg("astronaut_badge", "props", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ZHOU_IGNITION_BUTTON = reg("zhou_ignition_button", "props", 0, "ignition", 7.0f, 12.0f);
    public static final DeferredBlock<Block> OVER_FIFTY_ROSTER = reg("over_fifty_roster", "props", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> TRAFFIC_COMMITTEE_SPEAKER = reg("traffic_committee_speaker", "props", 0, "traffic", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ALERT_SIREN = reg("alert_siren", "props", 0, "alert", 7.0f, 12.0f);
    public static final DeferredBlock<Block> FIRE_SEED_PLAN_MARKER = reg("fire_seed_plan_marker", "props", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> QUANTUM_COMPUTER_550A = reg("quantum_computer_550a", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> QUANTUM_COMPUTER_550C = reg("quantum_computer_550c", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> QUANTUM_COMPUTER_550W = reg("quantum_computer_550w", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> MOSS_CAMERA = reg("moss_camera", "quantum", 0, "moss", 7.0f, 12.0f);
    public static final DeferredBlock<Block> MOSS_RED_DOT = reg("moss_red_dot", "quantum", 7, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> MOSS_MAINFRAME = reg("moss_mainframe", "quantum", 0, "moss", 7.0f, 12.0f);
    public static final DeferredBlock<Block> ITERATION_CONSOLE = reg("iteration_console", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> DIGITAL_LIFE_TERMINAL = reg("digital_life_terminal", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> TU_YAYA_DATA_CORE = reg("tu_yaya_data_core", "quantum", 9, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> HUMAN_IN_THE_LOOP_PORT = reg("human_in_the_loop_port", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> QUANTUM_SERVER_RACK = reg("quantum_server_rack", "quantum", 0, "", 7.0f, 12.0f);
    public static final DeferredBlock<Block> SINGULARITY_DATA_CORE = reg("singularity_data_core", "quantum", 0, "", 7.0f, 12.0f);

    private static DeferredBlock<Block> reg(String name, String cat, int light,
                                             String kind, float strength, float resistance) {
        BlockBehaviour.Properties base = BlockBehaviour.Properties.of()
                .sound(SoundType.METAL).strength(strength, resistance);
        final BlockBehaviour.Properties p = light > 0 ? base.lightLevel(s -> light) : base;
        final String n = name, k = kind;
        Supplier<Block> sup = () -> new ModBlock(p, n, k);
        DeferredBlock<Block> d = BLOCKS.<Block>register(name, sup);
        ALL.add(d);
        CATEGORY_OF.put(name, cat);
        return d;
    }

    private ModBlocks() {}
}
