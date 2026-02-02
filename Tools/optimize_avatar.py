import bpy
import os
import sys

# --- LOGIC CONFIGURATION ---
# If an object name contains these words, do NOT decimate it.
# (Protects fingers, faces, and glitch-prone areas)
PRESERVE_KEYWORDS = ["head", "face", "hand", "finger", "viseme", "outline"]

# If an object name contains these words, CRUSH IT.
# (Things nobody looks at closely: soles of feet, belts, internal geo)
AGGRESSIVE_KEYWORDS = ["shoe", "boot", "belt", "strap", "inner", "prop", "accessory"]

# Decimation Ratios (1.0 = Keep Original, 0.1 = Reduce to 10%)
RATIO_STANDARD = 0.5  # 50% reduction for general body
RATIO_AGGRESSIVE = 0.2  # 80% reduction for props/shoes


def optimize_for_quest() -> None:
    # --- ARGUMENT PARSING ---
    try:
        args_start = sys.argv.index("--") + 1
        input_path = sys.argv[args_start]
    except (ValueError, IndexError):
        print("[ERROR] No input file passed.")
        return

    # --- SETUP ---
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print(f"[PROCESSING] {input_path}")
    bpy.ops.import_scene.fbx(filepath=input_path, use_manual_orientation=False)

    # --- INTELLIGENT OPTIMIZATION LOOP ---
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue

        obj_name = obj.name.lower()

        # LOGIC 1: VISEME SAFE-GUARD
        # If the mesh has Shape Keys (used for VRChat lip sync), do NOT touch it.
        # Decimating meshes with shape keys usually breaks the animation.
        if obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) > 0:
            print(f"  [SKIP] '{obj.name}' has Shape Keys (Face/Visemes detected).")
            continue

        # LOGIC 2: KEYWORD FILTERING
        # Check if the object is in our 'Do Not Touch' list
        if any(word in obj_name for word in PRESERVE_KEYWORDS):
            print(f"  [PROTECT] '{obj.name}' matches preservation list.")
            continue

        # Determine Ratio based on aggressive keywords
        target_ratio = RATIO_STANDARD
        if any(word in obj_name for word in AGGRESSIVE_KEYWORDS):
            print(f"  [AGGRESSIVE] '{obj.name}' identified as high-compression target.")
            target_ratio = RATIO_AGGRESSIVE
        else:
            print(f"  [STANDARD] Decimating '{obj.name}'...")

        # LOGIC 3: APPLY MODIFIER WITH SEAM PROTECTION
        try:
            bpy.context.view_layer.objects.active = obj

            # Add Decimate Modifier
            mod = obj.modifiers.new(name="SmartDecimate", type="DECIMATE")
            mod.ratio = target_ratio
            mod.use_collapse_triangulate = True

            # LOGIC 4: UV & BOUNDARY PROTECTION
            # Prevents texture warping at UV seams
            mod.use_symmetry = False
            mod.delimit = {"UV", "MATERIAL"}

            # Apply
            bpy.ops.object.modifier_apply(modifier="SmartDecimate")

        except Exception as exc:
            print(f"  [ERROR] Could not optimize {obj.name}: {exc}")

    # --- EXPORT ---
    dir_name = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(dir_name, f"{base_name}_QUEST_SMART.fbx")

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        add_leaf_bones=False,
        bake_anim=False,
    )
    print(f"[COMPLETE] Saved to {output_path}")


if __name__ == "__main__":
    optimize_for_quest()
