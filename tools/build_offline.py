# -*- coding: utf-8 -*-
"""Offline javac build for The Wandering Earth mod.

On networks where maven.neoforged.net is unreachable, ModDevGradle cannot run
(NeoForm Runtime is only published there). This script compiles the *exact same*
src/main/java sources offline:

  real NeoForge / FML .class jars  (from bmclapi mirror, in lab/cp)
  + compile-time-only net.minecraft.* / com.mojang.* signature stubs (below)
  -> real compiled .class files -> a clean, installable mod jar.

The stubs are NEVER shipped in the jar. At runtime Minecraft + NeoForge supply
the real classes. Stubs only exist so javac can resolve method signatures;
signatures were verified against Mojang's official 1.21.1 mappings.

Usage:  python tools/build_offline.py
"""
import os
import sys
import shutil
import subprocess

ROOT = r"D:\money\wandering-earth"
LAB = r"D:\money\_we_probe\lab"
CP = os.path.join(LAB, "cp")
# Optional extra compile-only jars (Create's bundled Ponder, for compat/).
EXTRA_CP = os.path.join(LAB, "cp_extra")
STUB = os.path.join(LAB, "stub")
OUT = os.path.join(LAB, "classes")
BUILD = os.path.join(ROOT, "build", "libs")
JDK = r"D:\Program Files\Java\jdk-21"
JAVAC = os.path.join(JDK, "bin", "javac")
JAR = os.path.join(JDK, "bin", "jar")

MOD_ID = "wandering_earth"
VERSION = "1.4.0"

# ---------------------------------------------------------------------------
# compile-time-only stub sources
# ---------------------------------------------------------------------------
STUBS = {
    # ---- com.mojang.datafixers (referenced from real NeoForge .class signatures)
    "com/mojang/datafixers/util/Either.java": '''package com.mojang.datafixers.util;
public final class Either<L, R> {
    private Either() {}
    public static <L, R> Either<L, R> left(L value) { return new Either<>(); }
    public static <L, R> Either<L, R> right(R value) { return new Either<>(); }
    public L left() { return null; }
    public R right() { return null; }
    public java.util.Optional<L> leftOptional() { return java.util.Optional.empty(); }
    public java.util.Optional<R> rightOptional() { return java.util.Optional.empty(); }
    public Object map(java.util.function.Function<L, ?> l, java.util.function.Function<R, ?> r) { return null; }
}
''',
    "com/mojang/datafixers/types/Type.java": '''package com.mojang.datafixers.types;
public abstract class Type<A> {}
''',
    "com/mojang/serialization/DynamicOps.java": '''package com.mojang.serialization;
public interface DynamicOps<T> {}
''',
    # ---- net.minecraft core
    "net/minecraft/resources/ResourceLocation.java": '''package net.minecraft.resources;
public final class ResourceLocation {
    private final String namespace, path;
    private ResourceLocation(String n, String p) { namespace = n; path = p; }
    public static ResourceLocation fromNamespaceAndPath(String n, String p) { return new ResourceLocation(n, p); }
    public static ResourceLocation parse(String s) {
        int i = s.indexOf(':'); return new ResourceLocation(i < 0 ? "minecraft" : s.substring(0, i), i < 0 ? s : s.substring(i + 1));
    }
    public static ResourceLocation tryParse(String s) { return s == null ? null : parse(s); }
    public String getNamespace() { return namespace; }
    public String getPath() { return path; }
    public ResourceLocation withPath(String p) { return new ResourceLocation(namespace, p); }
    public ResourceLocation withPrefix(String p) { return new ResourceLocation(namespace, p + path); }
    public String toString() { return namespace + ":" + path; }
}
''',
    "net/minecraft/resources/ResourceKey.java": '''package net.minecraft.resources;
public final class ResourceKey<T> {
    private final ResourceLocation loc;
    private ResourceKey(ResourceLocation l) { loc = l; }
    public static <T> ResourceKey<T> create(ResourceKey<?> registry, ResourceLocation loc) { return new ResourceKey<>(loc); }
    public static <T> ResourceKey<T> create(ResourceLocation registry, ResourceLocation loc) { return new ResourceKey<>(loc); }
    public static <T> ResourceKey<T> createRegistryKey(ResourceLocation loc) { return new ResourceKey<>(loc); }
    public ResourceLocation location() { return loc; }
    public ResourceLocation registry() { return loc; }
    public ResourceKey<?> registryKey() { return this; }
}
''',
    "net/minecraft/core/Registry.java": '''package net.minecraft.core;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Stream;
public interface Registry<T> extends HolderGetter<T>, Iterable<T> {
    ResourceKey<? extends Registry<T>> key();
    Optional<Holder.Reference<T>> getHolder(ResourceKey<T> key);
    Optional<Holder.Reference<T>> getHolder(ResourceLocation loc);
    Set<ResourceKey<T>> keySet();
    Stream<Holder.Reference<T>> holders();
    int getId(T value);
    ResourceKey<T> getKey(T value);
    ResourceLocation getKeyLocation(T value);
    boolean containsKey(ResourceKey<T> key);
}
''',
    "net/minecraft/core/Holder.java": '''package net.minecraft.core;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.tags.TagKey;
import com.mojang.datafixers.util.Either;
import java.util.Optional;
import java.util.function.Predicate;
import java.util.stream.Stream;
public interface Holder<T> {
    T value();
    boolean isBound();
    boolean is(ResourceLocation loc);
    boolean is(ResourceKey<T> key);
    boolean is(Predicate<ResourceKey<T>> p);
    boolean is(TagKey<T> tag);
    boolean is(Holder<T> holder);
    Stream<TagKey<T>> tags();
    Either<ResourceKey<T>, T> unwrap();
    Optional<ResourceKey<T>> unwrapKey();
    Kind kind();
    boolean canSerializeIn(HolderOwner<T> owner);
    Holder<T> getDelegate();
    enum Kind { REFERENCE, DIRECT }
    interface Reference<T> extends Holder<T> {}
}
''',
    "net/minecraft/core/HolderOwner.java": '''package net.minecraft.core;
public interface HolderOwner<T> {}
''',
    "net/minecraft/core/HolderGetter.java": '''package net.minecraft.core;
import net.minecraft.resources.ResourceKey;
import java.util.Optional;
public interface HolderGetter<T> {
    Optional<Holder.Reference<T>> get(ResourceKey<T> key);
}
''',
    "net/minecraft/core/HolderLookup.java": '''package net.minecraft.core;
import net.minecraft.resources.ResourceKey;
import com.mojang.serialization.DynamicOps;
import java.util.Optional;
import java.util.stream.Stream;
// Real type is an INTERFACE (vanilla jo.class, access 0x0601) — must stay an
// interface or generated call sites become invokevirtual and die with ICCE.
public interface HolderLookup {
    public interface RegistryLookup<T> extends HolderGetter<T> {}
    public interface Provider extends net.minecraft.core.HolderGetter.Provider {
        Stream<ResourceKey<?>> listRegistries();
        <T> Optional<RegistryLookup<T>> lookup(ResourceKey<? extends Registry<T>> key);
        <T> RegistryLookup<T> lookupOrThrow(ResourceKey<? extends Registry<T>> key);
        <T> com.mojang.serialization.DynamicOps<T> createSerializationContext(DynamicOps<T> ops);
        static Provider create(Stream<Provider> p) { return null; }
    }
}
''',
    "net/minecraft/core/HolderGetter.java.provider": None,  # placeholder, see below
    "net/minecraft/core/component/DataComponentType.java": '''package net.minecraft.core.component;
// Real type is an INTERFACE (vanilla kp.class, access 0x0601).
public interface DataComponentType<T> {}
''',
    "net/minecraft/core/RegistryAccess.java": '''package net.minecraft.core;
public interface RegistryAccess extends HolderLookup.Provider {}
''',
    "net/minecraft/core/BlockPos.java": '''package net.minecraft.core;
public final class BlockPos {
    private final int x, y, z;
    public BlockPos(int x, int y, int z) { this.x = x; this.y = y; this.z = z; }
    public int getX() { return x; }
    public int getY() { return y; }
    public int getZ() { return z; }
    // Real 1.21.1: asLong()/asLong(int,int,int) pack into 38 bits, of(long) unpacks.
    public long asLong() { return asLong(x, y, z); }
    public static long asLong(int x, int y, int z) { return 0L; }
    public static BlockPos of(long packed) { return new BlockPos(0, 0, 0); }
    public static int getX(long packed) { return 0; }
    public static int getY(long packed) { return 0; }
    public static int getZ(long packed) { return 0; }
    public BlockPos above() { return new BlockPos(x, y + 1, z); }
    public BlockPos above(int n) { return new BlockPos(x, y + n, z); }
    public BlockPos below() { return new BlockPos(x, y - 1, z); }
    public BlockPos below(int n) { return new BlockPos(x, y - n, z); }
    public BlockPos relative(Direction d) { return this; }
    public BlockPos relative(Direction d, int n) { return this; }
    public BlockPos offset(int dx, int dy, int dz) { return new BlockPos(x + dx, y + dy, z + dz); }
    public BlockPos offset(int x, int y, int z, int n) { return new BlockPos(this.x + x * n, this.y + y * n, this.z + z * n); }
}
''',
    "net/minecraft/core/registries/BuiltInRegistries.java": '''package net.minecraft.core.registries;
import net.minecraft.core.Registry;
public final class BuiltInRegistries {
    public static final Registry<net.minecraft.world.level.block.Block> BLOCK = null;
    public static final Registry<net.minecraft.world.item.Item> ITEM = null;
    public static final Registry<net.minecraft.world.level.block.entity.BlockEntityType<?>> BLOCK_ENTITY_TYPE = null;
    public static final Registry<net.minecraft.world.item.CreativeModeTab> CREATIVE_MODE_TAB = null;
    public static final Registry<net.minecraft.sounds.SoundEvent> SOUND_EVENT = null;
}
''',
    "net/minecraft/core/registries/Registries.java": '''package net.minecraft.core.registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.core.Registry;
import net.minecraft.resources.ResourceLocation;
public final class Registries {
    private static <T> ResourceKey<Registry<T>> k(String s) { return ResourceKey.createRegistryKey(ResourceLocation.parse(s)); }
    public static final ResourceKey<Registry<net.minecraft.world.level.block.Block>> BLOCK = k("minecraft:block");
    public static final ResourceKey<Registry<net.minecraft.world.item.Item>> ITEM = k("minecraft:item");
    public static final ResourceKey<Registry<net.minecraft.world.level.block.entity.BlockEntityType<?>>> BLOCK_ENTITY_TYPE = k("minecraft:block_entity_type");
    public static final ResourceKey<Registry<net.minecraft.world.item.CreativeModeTab>> CREATIVE_MODE_TAB = k("minecraft:creative_mode_tab");
    public static final ResourceKey<Registry<net.minecraft.sounds.SoundEvent>> SOUND_EVENT = k("minecraft:sound_event");
    public static final ResourceKey<Registry<net.minecraft.core.component.DataComponentType<?>>> DATA_COMPONENT_TYPE = k("minecraft:data_component_type");
}
''',
    "net/minecraft/tags/TagKey.java": '''package net.minecraft.tags;
import net.minecraft.resources.ResourceKey;
public final class TagKey<T> {
    public ResourceKey<?> registry() { return null; }
}
''',
    "net/minecraft/ChatFormatting.java": '''package net.minecraft;
public enum ChatFormatting {
    BLACK, DARK_BLUE, DARK_GREEN, DARK_AQUA, DARK_RED, DARK_PURPLE, GOLD, GRAY,
    DARK_GRAY, BLUE, GREEN, AQUA, RED, LIGHT_PURPLE, YELLOW, WHITE, OBFUSCATED,
    BOLD, STRIKETHROUGH, UNDERLINE, ITALIC, RESET
}
''',
    "net/minecraft/network/chat/Component.java": '''package net.minecraft.network.chat;
public interface Component {
    static MutableComponent literal(String s) { return null; }
    static MutableComponent translatable(String s) { return null; }
    static MutableComponent translatable(String s, Object... args) { return null; }
    static MutableComponent empty() { return null; }
    String getString();
}
''',
    "net/minecraft/network/chat/MutableComponent.java": '''package net.minecraft.network.chat;
import net.minecraft.ChatFormatting;
import java.util.function.UnaryOperator;
// Real type is a CLASS (vanilla xn.class, access 0x0021, extends Object,
// implements Component). It MUST be a class: Component.translatable(...) returns
// MutableComponent, and a stub interface makes javac emit invokeinterface for
// withStyle(...) -> "IncompatibleClassChangeError: Found class ... but interface
// was expected" at runtime (this was the v1.0.0 crash).
public class MutableComponent implements Component {
    public MutableComponent append(String s) { return this; }
    public MutableComponent append(Component c) { return this; }
    public MutableComponent withStyle(ChatFormatting f) { return this; }
    public MutableComponent withStyle(ChatFormatting... f) { return this; }
    public MutableComponent withStyle(UnaryOperator<Style> op) { return this; }
    public MutableComponent withStyle(Style s) { return this; }
    public String getString() { return ""; }
}
''',
    "net/minecraft/network/chat/Style.java": '''package net.minecraft.network.chat;
public final class Style {
    public static final Style EMPTY = null;
}
''',
    "net/minecraft/sounds/SoundEvent.java": '''package net.minecraft.sounds;
import net.minecraft.resources.ResourceLocation;
import java.util.Optional;
public final class SoundEvent {
    public static SoundEvent createVariableRangeEvent(ResourceLocation loc) { return null; }
    public static SoundEvent create(ResourceLocation loc, Optional<Float> range) { return null; }
}
''',
    "net/minecraft/world/level/material/MapColor.java": '''package net.minecraft.world.level.material;
public final class MapColor {
    public static final MapColor STONE = null, METAL = null, WOOL = null;
}
''',
    "net/minecraft/world/DyeColor.java": '''package net.minecraft.world;
public enum DyeColor { WHITE, ORANGE, MAGENTA, LIGHT_BLUE, YELLOW, LIME, PINK, GRAY,
    LIGHT_GRAY, CYAN, PURPLE, BLUE, BROWN, GREEN, RED, BLACK }
''',
    "net/minecraft/world/level/block/SoundType.java": '''package net.minecraft.world.level.block;
public final class SoundType {
    public static final SoundType STONE = null, WOOD = null, GRAVEL = null, GRASS = null,
        METAL = null, GLASS = null, WOOL = null, SAND = null, SNOW = null, LADDER = null,
        ANVIL = null, SLIME_BLOCK = null, HONEY_BLOCK = null, RESONANT_AMETHYST = null,
        NETHERITE_BLOCK = null, NETHERRACK = null, NETHER_BRICKS = null, CANDLE = null;
}
''',
    "net/minecraft/world/item/Rarity.java": '''package net.minecraft.world.item;
public enum Rarity { COMMON, UNCOMMON, RARE, EPIC }
''',
    "net/minecraft/world/item/Item.java": '''package net.minecraft.world.item;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ItemLike;
import java.util.List;
public class Item implements ItemLike {
    public Item(Item.Properties p) {}
    public Item asItem() { return this; }
    public InteractionResult useOn(UseOnContext ctx) { return InteractionResult.PASS; }
    public InteractionResultHolder<ItemStack> use(Level l, Player p, InteractionHand h) { return null; }
    public String getDescriptionId() { return ""; }
    public String getDescriptionId(ItemStack s) { return ""; }
    public Component getName(ItemStack s) { return null; }
    public void appendHoverText(ItemStack s, TooltipContext c, List<Component> t, TooltipFlag f) {}
    public boolean isFoil(ItemStack s) { return false; }
    public interface TooltipContext {}
    public static final class Properties {
        public Properties() {}
        public Properties stacksTo(int n) { return this; }
        public Properties rarity(Rarity r) { return this; }
        public Properties fireResistant() { return this; }
        public Properties durability(int n) { return this; }
        public Properties food(Object f) { return this; }
    }
}
''',
    "net/minecraft/world/item/BlockItem.java": '''package net.minecraft.world.item;
import net.minecraft.world.level.block.Block;
public class BlockItem extends Item {
    public BlockItem(Block b, Item.Properties p) { super(p); }
    public Block getBlock() { return null; }
}
''',
    "net/minecraft/world/item/ItemStack.java": '''package net.minecraft.world.item;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.ItemLike;
import java.util.function.Predicate;
public final class ItemStack {
    public static final ItemStack EMPTY = null;
    public ItemStack(ItemLike i) {}
    public ItemStack(ItemLike i, int count) {}
    public ItemStack(Holder<Item> h, int count) {}
    public Item getItem() { return null; }
    public boolean isEmpty() { return true; }
    public int getCount() { return 0; }
    public void shrink(int n) {}
    public void grow(int n) {}
    public ItemStack copy() { return this; }
    public Component getHoverName() { return null; }
    public boolean is(Item i) { return false; }
    public boolean is(TagKey<Item> t) { return false; }
    public boolean is(Holder<Item> h) { return false; }
    public boolean is(Predicate<Item> p) { return false; }
}
''',
    "net/minecraft/world/item/TooltipFlag.java": '''package net.minecraft.world.item;
// Real type is an INTERFACE (vanilla cwm.class, access 0x0601); the concrete
// implementation is the record TooltipFlag.Default (cwm$a).
public interface TooltipFlag {
    boolean isAdvanced();
    boolean isCreative();
    class Default implements TooltipFlag {
        private final boolean advanced;
        private final boolean creative;
        public Default(boolean advanced, boolean creative) { this.advanced = advanced; this.creative = creative; }
        public boolean isAdvanced() { return advanced; }
        public boolean isCreative() { return creative; }
    }
}
''',
    "net/minecraft/world/level/ItemLike.java": '''package net.minecraft.world.level;
import net.minecraft.world.item.Item;
public interface ItemLike { Item asItem(); }
''',
    "net/minecraft/world/level/block/Block.java": '''package net.minecraft.world.level.block;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.util.RandomSource;
import java.util.List;
public class Block extends BlockBehaviour implements net.minecraft.world.level.ItemLike {
    public Block(BlockBehaviour.Properties p) { super(p); }
    public Item asItem() { return null; }
    public Block asBlock() { return this; }
    public BlockState defaultBlockState() { return null; }
    public void appendHoverText(ItemStack s, Item.TooltipContext c, List<Component> t, TooltipFlag f) {}
    public BlockState getStateForPlacement(BlockPlaceContext c) { return null; }
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> b) {}
    public void onRemove(BlockState s, Level l, BlockPos p, BlockState ns, boolean moving) {}
    public void neighborChanged(BlockState s, Level l, BlockPos p, Block b, BlockPos np, boolean moving) {}
    // Real: BlockBehaviour.onPlace -> b (client.txt 178), inherited by Block.
    public void onPlace(BlockState s, Level l, BlockPos p, BlockState oldState, boolean moving) {}
    public void animateTick(BlockState s, Level l, BlockPos p, RandomSource r) {}
    public void popResource(Level l, BlockPos p, ItemStack s) {}
    protected void registerDefaultState(BlockState s) {}
}
''',
    "net/minecraft/world/level/block/state/BlockBehaviour.java": '''package net.minecraft.world.level.block.state;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.properties.Property;
import net.minecraft.world.level.material.MapColor;
import net.minecraft.world.DyeColor;
import net.minecraft.world.phys.BlockHitResult;
import java.util.function.Function;
import java.util.function.ToIntFunction;
public abstract class BlockBehaviour {
    protected BlockBehaviour(Properties p) {}
    public Properties properties() { return null; }
    public InteractionResult useWithoutItem(BlockState s, Level l, BlockPos p, Player pl, BlockHitResult h) { return InteractionResult.PASS; }
    public ItemInteractionResult useItemOn(ItemStack st, BlockState s, Level l, BlockPos p, Player pl, InteractionHand hand, BlockHitResult h) { return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION; }
    public static final class Properties {
        private Properties() {}
        public static Properties of() { return new Properties(); }
        public static Properties ofFullCopy(BlockBehaviour b) { return of(); }
        public Properties mapColor(MapColor c) { return this; }
        public Properties mapColor(DyeColor c) { return this; }
        public Properties mapColor(Function<BlockState, MapColor> f) { return this; }
        public Properties noCollission() { return this; }
        public Properties noOcclusion() { return this; }
        public Properties sound(SoundType s) { return this; }
        public Properties lightLevel(ToIntFunction<BlockState> f) { return this; }
        public Properties strength(float s, float r) { return this; }
        public Properties strength(float s) { return this; }
        public Properties requiresCorrectToolForDrops() { return this; }
        public Properties destroyTime(float t) { return this; }
        public Properties explosionResistance(float r) { return this; }
    }
}
''',
    "net/minecraft/world/level/block/state/StateHolder.java": '''package net.minecraft.world.level.block.state;
import net.minecraft.world.level.block.state.properties.Property;
import java.util.Collection;
// Real: obf dte, abstract class, access 0x0421 (client.txt 1.21.1).
//
// IMPORTANT - this stub exists to reproduce the *erased* descriptors exactly.
// javap says:
//   public <T extends java.lang.Comparable<T>, V extends T> S a(duf<T>, V)
//     descriptor: (Lduf;Ljava/lang/Comparable;)Ljava/lang/Object;
// i.e. setValue erases to a method RETURNING java.lang.Object, because S is
// unbounded on StateHolder. Declaring setValue directly on BlockState with a
// BlockState return type makes javac emit a descriptor returning BlockState,
// which no real class has -> NoSuchMethodError at runtime (the verifier caught
// exactly this). Modelling the real generic hierarchy makes javac emit Object
// plus a checkcast, which is what vanilla bytecode does too.
public abstract class StateHolder<O, S> {
    protected StateHolder(O owner) {}
    @SuppressWarnings("unchecked")
    public <T extends Comparable<T>> T getValue(Property<T> p) { return null; }
    @SuppressWarnings("unchecked")
    public <T extends Comparable<T>, V extends T> S setValue(Property<T> p, V v) { return (S) this; }
    public <T extends Comparable<T>> boolean hasProperty(Property<T> p) { return false; }
    public Collection<Property<?>> getProperties() { return null; }
}
''',
    "net/minecraft/world/level/block/state/BlockState.java": '''package net.minecraft.world.level.block.state;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.properties.Property;
import java.util.Collection;
import java.util.Map;
// Real: obf dtc extends dtb$a (BlockStateBase) extends dte (StateHolder<Block, BlockState>).
public class BlockState extends StateHolder<Block, BlockState> {
    public BlockState(Block owner) { super(owner); }
    public Block getBlock() { return null; }
    public int getLightEmission() { return 0; }
    public BlockState asState() { return this; }
    public Map<Property<?>, Comparable<?>> getValues() { return null; }
    // Real: these live on BlockStateBase (obf dtb$a), inherited by BlockState.
    public boolean isAir() { return false; }
    public boolean isSolid() { return true; }
    public boolean canBeReplaced() { return false; }
}
''',
    "net/minecraft/world/level/block/state/StateDefinition.java": '''package net.minecraft.world.level.block.state;
import net.minecraft.world.level.block.state.properties.Property;
public final class StateDefinition<B, S> {
    public static final class Builder<B, S> {
        public Builder<B, S> add(Property<?>... p) { return this; }
    }
}
''',
    "net/minecraft/world/level/block/state/properties/Property.java": '''package net.minecraft.world.level.block.state.properties;
import java.util.Collection;
// Real obf duf: abstract class (access 0x0421), so a source call must not
// emit invokeinterface on it.
public abstract class Property<T extends Comparable<T>> {
    public String getName() { return ""; }
    public Collection<T> getPossibleValues() { return null; }
    public Class<T> getValueClass() { return null; }
    public java.util.Optional<T> getValue(String name) { return java.util.Optional.empty(); }
    public String getName(T value) { return ""; }
}
''',
    "net/minecraft/world/level/block/state/properties/BooleanProperty.java": '''package net.minecraft.world.level.block.state.properties;
import java.util.Collection;
// Real obf dtt: class (0x0021), superclass Property.
public class BooleanProperty extends Property<Boolean> {
    public BooleanProperty(String name) { super(); }
    public static BooleanProperty create(String name) { return null; }
}
''',
    "net/minecraft/world/level/block/state/properties/EnumProperty.java": '''package net.minecraft.world.level.block.state.properties;
import java.util.Collection;
import java.util.function.Predicate;
// Real obf dua: class (0x0021), superclass Property.
public class EnumProperty<T extends Enum<T> & net.minecraft.util.StringRepresentable> extends Property<T> {
    public EnumProperty(String name, Class<T> type, Collection<T> values) { super(); }
    public static <T extends Enum<T> & net.minecraft.util.StringRepresentable> EnumProperty<T> create(String name, Class<T> type) { return null; }
    public static <T extends Enum<T> & net.minecraft.util.StringRepresentable> EnumProperty<T> create(String name, Class<T> type, Predicate<T> filter) { return null; }
}
''',
    "net/minecraft/world/level/block/state/properties/DirectionProperty.java": '''package net.minecraft.world.level.block.state.properties;
import net.minecraft.core.Direction;
import java.util.Collection;
// Real obf dtw: class (0x0021), superclass EnumProperty.
public class DirectionProperty extends EnumProperty<Direction> {
    public DirectionProperty(String name, Collection<Direction> values) { super(null, null, null); }
    public static DirectionProperty create(String name) { return null; }
    public static DirectionProperty create(String name, net.minecraft.core.Direction... values) { return null; }
    public static DirectionProperty create(String name, Collection<Direction> values) { return null; }
    public static DirectionProperty create(String name, java.util.function.Predicate<Direction> filter) { return null; }
}
''',
    # Real FQN verified from client.txt:110000 --
    # "net.minecraft.world.level.block.state.properties.BlockStateProperties -> dts:"
    # The package is block.state.properties, NOT block.state. Getting this wrong
    # compiles fine and then dies at runtime with NoClassDefFoundError inside
    # EngineBlock.<clinit> (that is exactly what shipped in 1.1.0).
    "net/minecraft/world/level/block/state/properties/BlockStateProperties.java": '''package net.minecraft.world.level.block.state.properties;
public class BlockStateProperties {
    public static final BooleanProperty LIT = null;
    public static final BooleanProperty POWERED = null;
    public static final BooleanProperty WATERLOGGED = null;
    public static final DirectionProperty FACING = null;
    public static final DirectionProperty HORIZONTAL_FACING = null;
    public static final DirectionProperty VERTICAL_DIRECTION = null;
}
''',
    "net/minecraft/world/level/block/entity/BlockEntity.java": '''package net.minecraft.world.level.block.entity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
public abstract class BlockEntity {
    public BlockEntity(BlockEntityType<?> t, BlockPos p, BlockState s) {}
    public Level getLevel() { return null; }
    public void setChanged() {}
    public BlockPos getBlockPos() { return null; }
    public BlockState getBlockState() { return null; }
    public void saveAdditional(CompoundTag t, HolderLookup.Provider p) {}
    public void loadAdditional(CompoundTag t, HolderLookup.Provider p) {}
    public net.minecraft.network.protocol.Packet getUpdatePacket() { return null; }
    public CompoundTag getUpdateTag(HolderLookup.Provider p) { return null; }
}
''',
    "net/minecraft/world/level/block/entity/BlockEntityType.java": '''package net.minecraft.world.level.block.entity;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import com.mojang.datafixers.types.Type;
import java.util.Set;
public final class BlockEntityType<T extends BlockEntity> {
    public interface BlockEntitySupplier<T extends BlockEntity> { T create(BlockPos p, BlockState s); }
    public static final class Builder<T extends BlockEntity> {
        public Builder(BlockEntitySupplier<T> s, Set<Block> b) {}
        public static <T extends BlockEntity> Builder<T> of(BlockEntitySupplier<T> s, Block... b) { return null; }
        public BlockEntityType<T> build(Type<?> t) { return null; }
    }
}
''',
    "net/minecraft/world/level/block/EntityBlock.java": '''package net.minecraft.world.level.block;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
public interface EntityBlock {
    BlockEntity newBlockEntity(BlockPos p, BlockState s);
    <T extends BlockEntity> BlockEntityTicker<T> getTicker(Level l, BlockState s, net.minecraft.world.level.block.entity.BlockEntityType<T> t);
}
''',
    "net/minecraft/world/level/block/entity/BlockEntityTicker.java": '''package net.minecraft.world.level.block.entity;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
public interface BlockEntityTicker<T extends BlockEntity> {
    void tick(Level l, BlockPos p, BlockState s, T be);
}
''',
    "net/minecraft/nbt/CompoundTag.java": '''package net.minecraft.nbt;
public final class CompoundTag {
    public CompoundTag() {}
    public void putInt(String k, int v) {}
    public int getInt(String k) { return 0; }
    public void putFloat(String k, float v) {}
    public float getFloat(String k) { return 0; }
    public void putString(String k, String v) {}
    public String getString(String k) { return ""; }
    public void putBoolean(String k, boolean v) {}
    public boolean getBoolean(String k) { return false; }
    public boolean contains(String k) { return false; }
    public void putLong(String k, long v) {}
    public long getLong(String k) { return 0L; }
    public void putLongArray(String k, long[] v) {}
    public long[] getLongArray(String k) { return new long[0]; }
    public void putIntArray(String k, int[] v) {}
    public int[] getIntArray(String k) { return new int[0]; }
}
''',
    "net/minecraft/network/protocol/Packet.java": '''package net.minecraft.network.protocol;
public interface Packet<T> {}
''',
    "net/minecraft/world/level/Level.java": '''package net.minecraft.world.level;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.phys.AABB;
import java.util.List;
import java.util.function.Predicate;
public abstract class Level {
    public boolean isClientSide;
    public boolean isClientSide() { return isClientSide; }
    public boolean setBlockAndUpdate(BlockPos p, BlockState s) { return true; }
    public boolean setBlock(BlockPos p, BlockState s, int flags) { return true; }
    public void playSound(Player p, BlockPos pos, SoundEvent s, SoundSource src, float vol, float pitch) {}
    public void playSound(Player p, double x, double y, double z, SoundEvent s, SoundSource src, float vol, float pitch) {}
    public BlockEntity getBlockEntity(BlockPos p) { return null; }
    public void setBlockEntity(BlockEntity be) {}
    public void removeBlockEntity(BlockPos p) {}
    public BlockState getBlockState(BlockPos p) { return null; }
    public void updateNeighborsAt(BlockPos p, Block b) {}
    public void sendBlockUpdated(BlockPos p, BlockState o, BlockState n, int flags) {}
    public long getGameTime() { return 0L; }
    public ResourceKey<Level> dimension() { return null; }
    public void addParticle(ParticleOptions p, double x, double y, double z, double dx, double dy, double dz) {}
    public void addParticle(ParticleOptions p, boolean always, double x, double y, double z, double dx, double dy, double dz) {}
    public void addAlwaysVisibleParticle(ParticleOptions p, double x, double y, double z, double dx, double dy, double dz) {}
    public void playLocalSound(double x, double y, double z, SoundEvent s, SoundSource src, float vol, float pitch, boolean distanceDelay) {}
    public RandomSource getRandom() { return null; }
    // Real: SignalGetter.hasNeighborSignal -> C; Level's interface chain includes SignalGetter.
    public boolean hasNeighborSignal(BlockPos pos) { return false; }
    public int getBestNeighborSignal(BlockPos pos) { return 0; }
    public boolean hasSignal(BlockPos pos, net.minecraft.core.Direction side) { return false; }
    public int getSignal(BlockPos pos, net.minecraft.core.Direction side) { return 0; }
    public boolean isLoaded(BlockPos pos) { return true; }
    public List<Entity> getEntities(Entity except, AABB box, Predicate<? super Entity> filter) { return null; }
}
''',
    "net/minecraft/sounds/SoundSource.java": '''package net.minecraft.sounds;
public enum SoundSource { MASTER, MUSIC, RECORDS, WEATHER, BLOCKS, HOSTILE, NEUTRAL, PLAYERS, AMBIENT, VOICE }
''',
    "net/minecraft/world/entity/player/Player.java": '''package net.minecraft.world.entity.player;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
public abstract class Player {
    public void displayClientMessage(Component c, boolean actionBar) {}
    public boolean addItem(ItemStack s) { return true; }
    public Inventory getInventory() { return null; }
    // Real: Entity.isShiftKeyDown -> bW (client.txt 2461), inherited by Player.
    public boolean isShiftKeyDown() { return false; }
}
''',
    "net/minecraft/world/entity/player/Inventory.java": '''package net.minecraft.world.entity.player;
public final class Inventory {}
''',
    "net/minecraft/world/phys/BlockHitResult.java": '''package net.minecraft.world.phys;
import net.minecraft.core.BlockPos;
public final class BlockHitResult {
    public BlockPos getBlockPos() { return null; }
}
''',
    "net/minecraft/world/InteractionResult.java": '''package net.minecraft.world;
public enum InteractionResult {
    SUCCESS, SUCCESS_NO_ITEM_USED, CONSUME, CONSUME_PARTIAL, PASS, FAIL;
    public boolean consumesAction() { return this == SUCCESS || this == CONSUME; }
    public boolean shouldSwing() { return this == SUCCESS; }
    public boolean indicateItemUse() { return this == SUCCESS; }
    public static InteractionResult sidedSuccess(boolean client) { return client ? SUCCESS : SUCCESS; }
}
''',
    "net/minecraft/world/InteractionResultHolder.java": '''package net.minecraft.world;
public final class InteractionResultHolder<T> {
    public InteractionResultHolder(InteractionResult r, T o) {}
    public InteractionResult getResult() { return InteractionResult.PASS; }
    public T getObject() { return null; }
}
''',
    "net/minecraft/world/InteractionHand.java": '''package net.minecraft.world;
public enum InteractionHand { MAIN_HAND, OFF_HAND }
''',
    "net/minecraft/world/phys/Vec3.java": '''package net.minecraft.world.phys;
// Real: obf (Vec3) => class with public final double x/y/z.
public class Vec3 {
    public final double x, y, z;
    public Vec3(double x, double y, double z) { this.x = x; this.y = y; this.z = z; }
    public Vec3 add(double dx, double dy, double dz) { return this; }
    public Vec3 add(Vec3 o) { return this; }
    public Vec3 subtract(double dx, double dy, double dz) { return this; }
    public Vec3 subtract(Vec3 o) { return this; }
    public Vec3 scale(double s) { return this; }
    public double distanceTo(Vec3 o) { return 0; }
}
''',
    "net/minecraft/world/item/context/UseOnContext.java": '''package net.minecraft.world.item.context;
import net.minecraft.core.BlockPos;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
public class UseOnContext {
    public UseOnContext(Level l, Player p, InteractionHand h, ItemStack s, BlockHitResult r) {}
    public BlockPos getClickedPos() { return null; }
    public ItemStack getItemInHand() { return null; }
    public Player getPlayer() { return null; }
    public InteractionHand getHand() { return InteractionHand.MAIN_HAND; }
    public Level getLevel() { return null; }
    public BlockHitResult getHitResult() { return null; }
}
''',
    "net/minecraft/world/item/context/BlockPlaceContext.java": '''package net.minecraft.world.item.context;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.BlockHitResult;
public class BlockPlaceContext extends UseOnContext {
    public BlockPlaceContext(Level l, Player p, InteractionHand h, ItemStack s, BlockHitResult r) { super(l, p, h, s, r); }
    public BlockPlaceContext(UseOnContext c) { super(null, null, null, null, null); }
    public BlockPlaceContext(Player p, InteractionHand h, ItemStack s, BlockHitResult r) { super(null, null, null, null, null); }
    public BlockPos getClickedPos() { return null; }
    public boolean canPlace() { return true; }
    public boolean replacingClickedOnBlock() { return false; }
    public Direction getNearestLookingDirection() { return Direction.NORTH; }
    public Direction getNearestLookingVerticalDirection() { return Direction.UP; }
    public Direction[] getNearestLookingDirections() { return null; }
    // Real: UseOnContext.getHorizontalDirection -> g (client.txt 74).
    public Direction getHorizontalDirection() { return Direction.NORTH; }
    public Level getLevel() { return null; }
    public Player getPlayer() { return null; }
}
''',
    "net/minecraft/world/item/CreativeModeTab.java": '''package net.minecraft.world.item;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.item.CreativeModeTab;
import java.util.Collection;
import java.util.function.Supplier;
public final class CreativeModeTab {
    public enum Row { TOP, BOTTOM }
    public enum Type { CATEGORY, INVENTORY, HOTBAR, SEARCH }
    public enum TabVisibility { PARENT_AND_SEARCH_TABS, PARENT_TAB_ONLY, SEARCH_TAB_ONLY }
    public interface Output {
        void accept(ItemStack s, TabVisibility v);
        void accept(ItemStack s);
        void accept(ItemLike i, TabVisibility v);
        void accept(ItemLike i);
        void acceptAll(Collection<ItemStack> c, TabVisibility v);
        void acceptAll(Collection<ItemStack> c);
    }
    public interface DisplayItemsGenerator {
        void accept(ItemDisplayParameters p, Output o);
    }
    public static final class ItemDisplayParameters {}
    public static final class Builder {
        public Builder(Row r, int c) {}
        public Builder title(Component c) { return this; }
        public Builder icon(Supplier<ItemStack> s) { return this; }
        public Builder displayItems(DisplayItemsGenerator g) { return this; }
        public CreativeModeTab build() { return null; }
    }
    public static Builder builder(Row r, int c) { return new Builder(r, c); }
    public Component getDisplayName() { return null; }
}
''',
    "net/minecraft/world/item/CreativeModeTabs.java": '''package net.minecraft.world.item;
import net.minecraft.resources.ResourceKey;
public final class CreativeModeTabs {
    public static final ResourceKey<CreativeModeTab> BUILDING_BLOCKS = null;
    public static final ResourceKey<CreativeModeTab> COLORED_BLOCKS = null;
    public static final ResourceKey<CreativeModeTab> NATURAL_BLOCKS = null;
    public static final ResourceKey<CreativeModeTab> FUNCTIONAL_BLOCKS = null;
    public static final ResourceKey<CreativeModeTab> REDSTONE_BLOCKS = null;
    public static final ResourceKey<CreativeModeTab> OP_BLOCKS = null;
}
''',
    "net/minecraft/Util.java": '''package net.minecraft;
public final class Util {}
''',
    "net/minecraft/util/StringRepresentable.java": '''package net.minecraft.util;
public interface StringRepresentable {
    String getSerializedName();
}
''',
    "net/minecraft/core/Direction.java": '''package net.minecraft.core;
import net.minecraft.util.StringRepresentable;
import java.util.function.Predicate;
import java.util.stream.Stream;
// Real: obf ji, access 0x4031 => enum (extends java.lang.Enum). Method bodies
// here are inert; only the descriptor/kind matter for offline compilation.
public enum Direction implements StringRepresentable {
    DOWN, UP, NORTH, SOUTH, WEST, EAST;
    public static final Direction[] VALUES = values();
    public Direction getOpposite() { return this; }
    public Direction getClockWise() { return this; }
    public Direction getCounterClockWise() { return this; }
    public int getStepX() { return 0; }
    public int getStepY() { return 0; }
    public int getStepZ() { return 0; }
    public String getName() { return ""; }
    public String getSerializedName() { return ""; }
    public int get3DDataValue() { return 0; }
    public static Direction byName(String n) { return NORTH; }
    public static Direction from3DDataValue(int v) { return NORTH; }
    public static Direction fromYRot(double y) { return NORTH; }
    public float toYRot() { return 0f; }
    public static Stream<Direction> stream() { return Stream.empty(); }
}
''',
    "net/minecraft/util/RandomSource.java": '''package net.minecraft.util;
// Real: obf ayw, access 0x0601 => interface.
public interface RandomSource {
    static RandomSource create() { return null; }
    static RandomSource create(long seed) { return null; }
    int nextInt();
    int nextInt(int bound);
    default int nextIntBetweenInclusive(int a, int b) { return a; }
    float nextFloat();
    double nextDouble();
    boolean nextBoolean();
}
''',
    "net/minecraft/core/particles/ParticleOptions.java": '''package net.minecraft.core.particles;
// Real: obf lk, access 0x0601 => interface.
public interface ParticleOptions {
}
''',
    "net/minecraft/core/particles/ParticleType.java": '''package net.minecraft.core.particles;
public class ParticleType<T extends ParticleOptions> {
}
''',
    "net/minecraft/core/particles/SimpleParticleType.java": '''package net.minecraft.core.particles;
// Real: obf lq, access 0x0021 => class, superclass ParticleType.
public class SimpleParticleType extends ParticleType<SimpleParticleType> implements ParticleOptions {
}
''',
    "net/minecraft/core/particles/ParticleTypes.java": '''package net.minecraft.core.particles;
// Real: obf lm, access 0x0021 => class holding static particle singletons.
public class ParticleTypes {
    public static final SimpleParticleType FLAME = null;
    public static final SimpleParticleType SOUL_FIRE_FLAME = null;
    public static final SimpleParticleType LARGE_SMOKE = null;
    public static final SimpleParticleType LAVA = null;
    public static final SimpleParticleType SMOKE = null;
    public static final SimpleParticleType WHITE_SMOKE = null;
    public static final SimpleParticleType CAMPFIRE_COSY_SMOKE = null;
    // Beam particles added in 1.2.0 (real obf names verified in client.txt).
    public static final SimpleParticleType END_ROD = null;
    public static final SimpleParticleType ELECTRIC_SPARK = null;
    public static final SimpleParticleType SMALL_FLAME = null;
    public static final SimpleParticleType DUST = null;
}
''',
    "net/minecraft/world/phys/AABB.java": '''package net.minecraft.world.phys;
import net.minecraft.core.BlockPos;
// Real: obf ewx, access 0x0021 => class with public final double fields a..f.
public class AABB {
    public final double a, b, c, d, e, f;
    public AABB(double x1, double y1, double z1, double x2, double y2, double z2) {
        this.a = x1; this.b = y1; this.c = z1; this.d = x2; this.e = y2; this.f = z2;
    }
    public AABB(BlockPos p) { this(0, 0, 0, 1, 1, 1); }
    public AABB(Vec3 p1, Vec3 p2) { this(0, 0, 0, 1, 1, 1); }
    public AABB inflate(double v) { return this; }
    public AABB inflate(double x, double y, double z) { return this; }
    public AABB expandTowards(double x, double y, double z) { return this; }
    public AABB contract(double x, double y, double z) { return this; }
    public AABB move(double x, double y, double z) { return this; }
    public boolean contains(double x, double y, double z) { return false; }
    public Vec3 getCenter() { return null; }
}
''',
    "net/minecraft/world/entity/Entity.java": '''package net.minecraft.world.entity;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.AABB;
// Real: obf bsr, access 0x0421 => abstract class.
public abstract class Entity {
    public void discard() {}
    public boolean isShiftKeyDown() { return false; }
    public AABB getBoundingBox() { return null; }
    public double getX() { return 0; }
    public double getY() { return 0; }
    public double getEyeY() { return 0; }
    public double getZ() { return 0; }
    public Level level() { return null; }
}
''',
    "net/minecraft/world/entity/item/ItemEntity.java": '''package net.minecraft.world.entity.item;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
// Real: obf cjh, access 0x0021 => class, superclass Entity.
public class ItemEntity extends Entity {
    public ItemEntity(Level l, double x, double y, double z, ItemStack s) {}
    public ItemEntity(Level l, double x, double y, double z, ItemStack s, double dx, double dy, double dz) {}
    public ItemStack getItem() { return null; }
    public void setItem(ItemStack s) {}
}
''',
    "net/minecraft/sounds/SoundEvents.java": '''package net.minecraft.sounds;
// Real: obf avp, access 0x0021 => class of static SoundEvent constants.
public class SoundEvents {
    public static final SoundEvent FIRECHARGE_USE = null;
    public static final SoundEvent BLAZE_BURN = null;
    // Real: SoundEvents.LEVER_CLICK -> nU (client.txt), used by the control panel.
    public static final SoundEvent LEVER_CLICK = null;
    public static final SoundEvent BLAZE_SHOOT = null;
    public static final SoundEvent BLAZE_AMBIENT = null;
    public static final SoundEvent FIRE_AMBIENT = null;
    public static final SoundEvent FIRE_EXTINGUISH = null;
    // Real: SoundEvents.BEACON_ACTIVATE -> bK, BEACON_AMBIENT -> bL (client.txt).
    public static final SoundEvent BEACON_ACTIVATE = null;
    public static final SoundEvent BEACON_AMBIENT = null;
    public static final SoundEvent BEACON_DEACTIVATE = null;
    public static final SoundEvent BEACON_POWER_SELECT = null;
}
''',
    "net/minecraft/world/ItemInteractionResult.java": '''package net.minecraft.world;
// Real: obf bqt, access 0x4031 => enum.
public enum ItemInteractionResult {
    SUCCESS, CONSUME, CONSUME_PARTIAL, PASS_TO_DEFAULT_BLOCK_INTERACTION, SKIP_DEFAULT_BLOCK_INTERACTION, FAIL;
    public boolean consumesAction() { return this == SUCCESS || this == CONSUME; }
}
''',
    # --- Client side stubs, added in 1.4.0 for the beacon style engine beam. ---
    # Signatures are copied verbatim from the official Mojang mappings so that the
    # compiled descriptors match the real classes at runtime.
    "com/mojang/blaze3d/vertex/PoseStack.java": '''package com.mojang.blaze3d.vertex;
// Real: obf fbi, access 0x0021 => class.
public class PoseStack {
    public PoseStack() {}
    public void translate(double x, double y, double z) {}
    public void translate(float x, float y, float z) {}
    public void scale(float x, float y, float z) {}
    public void pushPose() {}
    public void popPose() {}
    public void setIdentity() {}
    public Pose last() { return new Pose(); }
    public static class Pose {
    }
}
''',
    "com/mojang/blaze3d/vertex/VertexConsumer.java": '''package com.mojang.blaze3d.vertex;
// Real: obf fbm, access 0x0201 => interface.
public interface VertexConsumer {
    VertexConsumer addVertex(float x, float y, float z);
    VertexConsumer addVertex(PoseStack.Pose pose, float x, float y, float z);
    VertexConsumer setColor(int red, int green, int blue, int alpha);
    VertexConsumer setColor(int argb);
    VertexConsumer setUv(float u, float v);
    VertexConsumer setLight(int light);
    VertexConsumer setOverlay(int overlay);
    VertexConsumer setNormal(float x, float y, float z);
    VertexConsumer setNormal(PoseStack.Pose pose, float x, float y, float z);
}
''',
    "net/minecraft/client/renderer/RenderType.java": '''package net.minecraft.client.renderer;
import net.minecraft.resources.ResourceLocation;
// Real: obf gfh, access 0x0421 => abstract class; beaconBeam -> e.
public abstract class RenderType {
    public static RenderType beaconBeam(ResourceLocation texture, boolean outline) { return null; }
}
''',
    "net/minecraft/client/renderer/MultiBufferSource.java": '''package net.minecraft.client.renderer;
import com.mojang.blaze3d.vertex.VertexConsumer;
// Real: obf gez, access 0x0201 => interface.
public interface MultiBufferSource {
    VertexConsumer getBuffer(RenderType type);
}
''',
    "net/minecraft/client/renderer/texture/OverlayTexture.java": '''package net.minecraft.client.renderer.texture;
// Real: obf gqc, access 0x0021 => class; NO_OVERLAY -> d.
// The value is boxed on purpose so that javac emits a getstatic instead of
// inlining a constant: the real overlay id is computed by the game.
public class OverlayTexture {
    public static final int SIZE = 16;
    public static final int NO_WHITE_U = 0;
    public static final int RED_OVERLAY_V = 3;
    public static final int WHITE_OVERLAY_V = 10;
    public static final int NO_OVERLAY = Integer.valueOf(0);
}
''',
    "net/minecraft/client/renderer/blockentity/BlockEntityRenderer.java": '''package net.minecraft.client.renderer.blockentity;
import com.mojang.blaze3d.vertex.PoseStack;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.phys.Vec3;
// Real: obf ggz, access 0x0201 => interface.
public interface BlockEntityRenderer<T extends BlockEntity> {
    void render(T blockEntity, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight, int packedOverlay);
    default boolean shouldRenderOffScreen(T blockEntity) { return false; }
    default int getViewDistance() { return 64; }
    default boolean shouldRender(T blockEntity, Vec3 camera) { return true; }
}
''',
    "net/minecraft/client/renderer/blockentity/BlockEntityRendererProvider.java": '''package net.minecraft.client.renderer.blockentity;
import net.minecraft.world.level.block.entity.BlockEntity;
// Real: obf gha, access 0x0201 => interface; create -> create.
public interface BlockEntityRendererProvider<T extends BlockEntity> {
    BlockEntityRenderer create(Context context);
    class Context {
    }
}
''',
}

# Fix the HolderGetter.Provider nested interface (declared in HolderLookup)
EXTRA = {
    "net/minecraft/core/HolderGetter.java": '''package net.minecraft.core;
import net.minecraft.resources.ResourceKey;
import java.util.Optional;
public interface HolderGetter<T> {
    Optional<Holder.Reference<T>> get(ResourceKey<T> key);
    interface Provider {
        <T> HolderGetter<T> asGetterLookup();
    }
}
''',
}
STUBS.update(EXTRA)
# remove the placeholder entry
STUBS.pop("net/minecraft/core/HolderGetter.java.provider", None)


def write_stubs():
    os.makedirs(STUB, exist_ok=True)
    for rel, src in STUBS.items():
        if src is None:
            continue
        p = os.path.join(STUB, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)


def src_files():
    out = []
    for base in (os.path.join(ROOT, "src", "main", "java"), STUB):
        for root, _, files in os.walk(base):
            for fn in files:
                if fn.endswith(".java"):
                    out.append(os.path.join(root, fn))
    return out


def extra_classpath():
    """Optional compile-only jars: Create's bundled Ponder (for the compat package).

    Kept in a side directory so a missing jar degrades to a clear skip message
    instead of a confusing 'cannot find symbol net.createmod...'.
    """
    out = []
    for d in (EXTRA_CP,):
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".jar"):
                out.append(os.path.join(d, fn))
    return out


def main():
    write_stubs()
    jars = [os.path.join(CP, j) for j in os.listdir(CP) if j.endswith(".jar")]
    jars += extra_classpath()
    cp = ";".join(jars)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT, exist_ok=True)

    files = src_files()
    real = [p for p in files if p.startswith(os.path.join(ROOT, "src"))]
    print("classpath jars:", len(jars))
    print("stub files:", len([p for p in files if p.startswith(STUB)]))
    print("real sources:", len(real))

    cmd = [JAVAC, "-J-Duser.language=en", "-J-Duser.country=US",
           "-J-Dfile.encoding=UTF-8",
           "-proc:none", "-encoding", "UTF-8", "--release", "21",
           "-Xmaxerrs", "200", "-cp", cp, "-d", OUT] + files
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        print("javac FAILED")
        return r.returncode
    print("javac OK")

    # Package: compiled mod classes + resources. Stubs are EXCLUDED.
    os.makedirs(BUILD, exist_ok=True)
    jar_path = os.path.join(BUILD, "%s-%s.jar" % (MOD_ID, VERSION))
    if os.path.exists(jar_path):
        os.remove(jar_path)
    # jar with -C OUT (all classes incl stubs) then delete stub packages via a
    # staging dir: copy only com/wanderingearth classes.
    stage = os.path.join(LAB, "stage")
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    shutil.copytree(os.path.join(OUT, "com", "wanderingearth"),
                    os.path.join(stage, "com", "wanderingearth"))
    shutil.copytree(os.path.join(ROOT, "src", "main", "resources"), stage, dirs_exist_ok=True)
    # manifest
    mf = os.path.join(LAB, "MANIFEST.MF")
    with open(mf, "w", encoding="utf-8", newline="\n") as f:
        f.write("Manifest-Version: 1.0\n"
                "Implementation-Title: TheWanderingEarth\n"
                "Implementation-Version: %s\n"
                "Built-On-Minecraft: 1.21.1\n"
                "Built-On-NeoForge: 21.1.209\n\n" % VERSION)
    r2 = subprocess.run([JAR, "cfm", jar_path, mf, "-C", stage, "."],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r2.returncode != 0:
        sys.stderr.write(r2.stderr)
        print("jar FAILED")
        return r2.returncode
    print("jar OK:", jar_path)
    print("size:", os.path.getsize(jar_path), "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
