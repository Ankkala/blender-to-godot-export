# Ankkala Blender to Godot export plugin

Blender plugin to replace links to other .blend files with placeholder nodes. On Godot's side, we pair this with an import script that replaces the placeholder nodes with instances of the referenced props.

When making a game with Blender + Godot, we make both game props and levels in Blender. Each level is supposed to have instances of static props, which are in many cases meant to be shared across levels. On Blender's side we accomplish this by linkin the meshes from other .blend files. 

The Problem: With the default Blender -> Gltf -> Godot pipeline, the Gltf for each game level includes all used geometry, duplicating geometry data across game levels. This is due to a limitation of the Gltf format: Gltf files cannot contain references to other gltf files, and instead are self-contained.

The Solution: At export time, this Blender plugin replaces linked .blend meshes with empty placeholder nodes with just the transform and name of the prop. On Godot's side, an import script can then replace them with the instances of the proper props.

Usage: Install the plugin, then export to Gltf with File -> Export -> Godot Level (.gltf)

Install for development use:
```
cd ~/.config/blender/4.4/scripts/addons
ln -s /path/to/blender-to-godot-export/src blender-to-godot-export
```
