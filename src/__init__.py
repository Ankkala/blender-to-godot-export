bl_info = {
    "name": "Export Level as Godot-ready glTF",
    "blender": (4, 0, 0),
    "category": "Import-Export",
}

import bpy
from contextlib import ExitStack
import re
import os

PREFIX = "prop_"

def strip_blender_number_suffix(name):
    """Remove the .001, .002 etc suffixes that Blender adds to duplicates"""
    return re.sub(r'\.\d{3}$', '', name)

def is_linked_prop(obj):
    return (
        obj.library is not None or
        (obj.data and obj.data.library) or
        (obj.instance_type == 'COLLECTION' and
         obj.instance_collection and
         obj.instance_collection.library)
    )

def print_object_info(obj):
    """Debug helper to print detailed object information"""
    print(f"\nObject: {obj.name}")
    print(f"  Type: {obj.type}")
    print(f"  Library linked: {obj.library is not None}")
    if obj.data:
        print(f"  Data type: {obj.data.bl_rna.name}")
        print(f"  Data library linked: {obj.data.library is not None}")
    if obj.instance_type == 'COLLECTION':
        print(f"  Instance type: COLLECTION")
        if obj.instance_collection:
            print(f"  Collection: {obj.instance_collection.name}")
            print(f"  Collection library linked: {obj.instance_collection.library is not None}")

class EXPORT_OT_level_gltf(bpy.types.Operator):
    """Export the current scene so that every library-linked object
       is replaced by a placeholder Empty that keeps transform + name."""
    bl_idname  = "export_scene.level_gltf_godot"
    bl_label   = "Export Level (Godot glTF)"
    filename_ext = ".gltf"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    # ---------- UI ----------
    def invoke(self, ctx, event):
        # Get current .blend filename without extension
        blend_filepath = bpy.data.filepath
        if blend_filepath:
            # Use the .blend filename as default
            filename = os.path.splitext(os.path.basename(blend_filepath))[0]
            
            # Check for ../gltf directory
            blend_dir = os.path.dirname(blend_filepath)
            gltf_dir = os.path.normpath(os.path.join(blend_dir, "..", "gltf"))
            
            if os.path.isdir(gltf_dir):
                # ../gltf exists, use it
                export_dir = gltf_dir
            else:
                # Fallback to .blend directory
                export_dir = blend_dir
        else:
            # Fallback to scene name if file hasn't been saved
            filename = bpy.path.clean_name(ctx.scene.name)
            export_dir = "//"
            
        self.filepath = os.path.join(export_dir, f"{filename}.gltf")
            
        ctx.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # ---------- Main ----------
    def execute(self, ctx):
        scene    = ctx.scene
        empties  = []
        unlinked = []  # (object, [collections])
        prop_counter = 0  # Global counter for prop numbering

        print("\n=== Starting Level Export ===")
        print(f"Scene: {scene.name}")
        print(f"Output: {self.filepath}")
        
        # Make temporary modifications and make sure we undo them
        with ExitStack() as stack:
            try:
                for obj in scene.objects:
                    print_object_info(obj)
                    
                    if not is_linked_prop(obj):
                        print("  → Not a linked prop, keeping as is")
                        continue

                    print(f"  → Replacing with Empty placeholder")
                    
                    # Get base name without numerical suffix
                    base_name = strip_blender_number_suffix(obj.name)
                    
                    # 1. Create the placeholder Empty with numbered name
                    dummy_name = f"{PREFIX}{prop_counter:04d}_{base_name}"
                    dummy = bpy.data.objects.new(dummy_name, None)
                    dummy.empty_display_type = 'ARROWS'
                    dummy.matrix_world = obj.matrix_world.copy()
                    scene.collection.objects.link(dummy)
                    empties.append(dummy)
                    prop_counter += 1
                    
                    print(f"  → Created Empty: {dummy.name}")

                    # 2. Unlink the real object from all collections
                    collections = [c for c in bpy.data.collections if obj.name in c.objects]
                    for c in collections:
                        c.objects.unlink(obj)
                    if obj.name in scene.collection.objects:
                        scene.collection.objects.unlink(obj)
                    
                    # Store original collections for restoration
                    unlinked.append((obj, collections))
                    print(f"  → Unlinked from {len(collections) + 1} collections")

                print("\nStarting glTF export...")
                
                # 3. Call the built-in exporter with custom-props enabled
                bpy.ops.export_scene.gltf(
                    filepath=self.filepath,
                    export_format='GLTF_SEPARATE',  # separate .gltf + .bin files
                    export_extras=True,           # write our custom property
                    use_selection=False,          # export entire scene
                    export_apply=False,
                    export_yup=True,
                    export_keep_originals=True,   # don't copy textures, keep original files
                )

                print("glTF export completed")

            finally:
                # ------ ALWAYS restore scene state ------
                print("\nRestoring scene state...")
                
                # Remove temporary empties
                for dummy in empties:
                    bpy.data.objects.remove(dummy, do_unlink=True)
                
                # Restore original collection links
                for obj, collections in unlinked:
                    for c in collections:
                        c.objects.link(obj)
                    if not any(obj.name in c.objects for c in bpy.data.collections):
                        # If not in any collection, restore to scene collection
                        scene.collection.objects.link(obj)
                
                print("Scene state restored")

        self.report({'INFO'}, f"Exported level to {self.filepath}")
        return {'FINISHED'}

# --- Registration helpers ---
def menu_func_export(self, context):
    self.layout.operator(
        EXPORT_OT_level_gltf.bl_idname,
        text="Godot Level (.gltf)"
    )

classes = (EXPORT_OT_level_gltf,)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    # <-- append to File ▶ Export
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    register()
