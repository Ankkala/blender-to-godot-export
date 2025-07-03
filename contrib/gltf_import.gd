@tool
extends EditorScenePostImport

const PROP_PREFIX = "prop_"
const PROP_DIR = "res://models/gltf/"

var missing_props = {}

func _post_import(scene: Node):
	missing_props.clear()
	replace_prop_placeholders(scene)
	setup_animations(scene)
	if missing_props.size() > 0:
		push_error("Failed to load " + str(missing_props.size()) + " unique prop(s). Check previous errors for details.")
	return scene

func replace_prop_placeholders(node: Node):
	for child in node.get_children():
		if child is Node3D:
			var prop_name = get_prop_name(child.name)
			if prop_name:
				var prop_path = PROP_DIR + prop_name + ".gltf"
				print("Attempting to load: " + prop_path)
				if ResourceLoader.exists(prop_path):
					var prop_scene = load(prop_path)
					var prop_instance = prop_scene.instantiate()
					
					var original_name = child.name
					var original_transform = child.transform
					node.remove_child(child)
					child.queue_free()
					
					prop_instance.name = original_name
					prop_instance.transform = original_transform
					node.add_child(prop_instance)
					prop_instance.owner = node
				else:
					if not missing_props.has(prop_path):
						missing_props[prop_path] = true
						push_error("Could not find prop: " + prop_path)
		
		replace_prop_placeholders(child)

# Optional: For our use case, we want to set animations to autoplay on loop for static geometry
func setup_animations(node: Node):
	for child in node.get_children():
		if child is AnimationPlayer:
			var animations = child.get_animation_list()
			if animations.size() == 1:
				var anim_name = animations[0]
				child.autoplay = anim_name
				
				var animation = child.get_animation(anim_name)
				animation.loop_mode = Animation.LOOP_LINEAR
		setup_animations(child)

func get_prop_name(node_name: String) -> String:
	if not node_name.begins_with(PROP_PREFIX):
		return ""
		
	# Remove the "prop_" prefix
	var after_prefix = node_name.substr(PROP_PREFIX.length())
	
	# Find the position of the next underscore
	var next_underscore = after_prefix.find("_")
	if next_underscore == -1:
		return ""
		
	# Get the number part
	var number_part = after_prefix.substr(0, next_underscore)
	if not number_part.is_valid_int():
		return ""
		
	# Everything after the number and its underscore is the prop name
	return after_prefix.substr(next_underscore + 1)
