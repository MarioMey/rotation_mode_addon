import bpy

obj = bpy.context.active_object
pose_bones = bpy.context.selected_pose_bones
action = obj.animation_data.action


def get_or_create_fcurve(action, data_path, array_index=-1, group=None):
	for fc in action.fcurves:
		if fc.data_path == data_path and (array_index<0 or fc.array_index == array_index):
			return fc

	fc = action.fcurves.new(data_path, array_index)
	fc.group = group
	return fc

def add_keyframe_quat(action, quat, frame, bone_prefix, group):
	for i in range(len(quat)):
		fc = get_or_create_fcurve(action, bone_prefix+"rotation_quaternion", i, group)
		pos = len(fc.keyframe_points)
		fc.keyframe_points.add(1)
		fc.keyframe_points[pos].co = [frame, quat[i]]
		fc.update()

def add_keyframe_euler(action, euler, frame, bone_prefix, group):
	for i in range(len(euler)):
		fc = get_or_create_fcurve(action, bone_prefix+"rotation_euler", i, group)
		pos = len(fc.keyframe_points)
		fc.keyframe_points.add(1)
		fc.keyframe_points[pos].co = [frame, euler[i]]
		fc.update()


def frames_matching(action, data_path):
	frames = set()
	for fc in action.fcurves:
		if fc.data_path == data_path:
			fri = [kp.co[0] for kp in fc.keyframe_points]
			frames.update(fri)
	return frames

# Converts only one group/bone in one action - Quat to euler
def convert_group_qe(obj, action, bone, bone_prefix, order):
	
	pose_bone = bone
	data_path = bone_prefix + "rotation_quaternion"
	frames = frames_matching(action, data_path)
	group = action.groups[bone.name]
	
	for fr in frames:
		quat = bone.rotation_quaternion.copy()
		for fc in action.fcurves:
			if fc.data_path == data_path:
				quat[fc.array_index] = fc.evaluate(fr)
		euler = quat.to_euler(order)

		add_keyframe_euler(action, euler, fr, bone_prefix, group)
		bone.rotation_mode = order

# Converts only one group/bone in one action - Euler to Quat
def convert_group_eq(obj, action, bone, bone_prefix, order):
	
	pose_bone = bone
	data_path = bone_prefix + "rotation_euler"
	frames = frames_matching(action, data_path)
	group = action.groups[bone.name]
	
	for fr in frames:
		euler = bone.rotation_euler.copy()
		for fc in action.fcurves:
			if fc.data_path == data_path:
				euler[fc.array_index] = fc.evaluate(fr)
		quat = euler.to_quaternion()

		add_keyframe_quat(action, quat, fr, bone_prefix, group)
		bone.rotation_mode = order

# One Action - One Bone
def convert_one_act_one_bon(obj, action, bone, order):
	do = False
	bone_prefix = ''
	
	# What kind of conversion
	cond1 = order == 'XYZ'
	cond2 = order == 'XZY'
	cond3 = order == 'YZX'
	cond4 = order == 'YXZ'
	cond5 = order == 'ZXY'
	cond6 = order == 'ZYX'
	
	order_euler = cond1 or cond2 or cond3 or cond4 or cond5 or cond6
	order_quat = order == 'QUATERNION'

	for fcurve in action.fcurves:
		if fcurve.group.name == bone.name:
			if order_euler:
				if fcurve.data_path.endswith('rotation_quaternion'):
					do = True
					bone_prefix = fcurve.data_path[:-len('rotation_quaternion')]
					break

			elif order_quat:
				if fcurve.data_path.endswith('rotation_euler'):
					do = True
					bone_prefix = fcurve.data_path[:-len('rotation_euler')]
					break
			else:
				print('Bad order')
				pass
	
	if do and order_euler:
		# Converts the group/bone from Quat to Euler
		convert_group_qe(obj, action, bone, bone_prefix, order)
		
		# Removes quaternion fcurves
		for key in action.fcurves:
			if key.data_path == 'pose.bones["' + bone.name + '"].rotation_quaternion':
				action.fcurves.remove(key)

	elif do and order_quat:
		# Converts the group/bone from Euler to Quat
		convert_group_eq(obj, action, bone, bone_prefix, order)

		# Removes euler fcurves
		for key in action.fcurves:
			if key.data_path == 'pose.bones["' + bone.name + '"].rotation_euler':
				action.fcurves.remove(key)
	
	# Changes rotation mode to new one
	bone.rotation_mode = order

# Borra todos los channels en Quaterniones
# Para usar en conjunto con el script de Blender Stack
def borra_quat_channels(test=True):
    for accion in bpy.data.actions:
        for key in accion.fcurves:
            if 'rotation_quaternion' in key.data_path:
                print('Action:', accion.name)
                print('Data_Path original:', key.data_path)
                if not test:
                    accion.fcurves.remove(key)



# One Actions, selected bones
def convert_one_act_sel_bon(obj, action, pose_bones, order):
	for bone in pose_bones:
		convert_one_act_one_bon(obj, action, bone, order)

# Current action, all Bones (in Action)
def convert_one_act_every_bon(obj, action, order):
	
	# Collects fcurve.groups with its names
	pose_bones_names = set()
	for fcurve in action.fcurves:
		if fcurve.data_path.endswith('rotation_quaternion'):
			if fcurve.group.name not in pose_bones_names:
				pose_bones_names.add(fcurve.group.name)
	
	# Use the names to select pose_bones
	pose_bones = set()
	for pose_bone_name in pose_bones_names:
		pose_bones.add(obj.pose.bones[pose_bone_name])
	
	# Convert current action and pose_bones that are in each action
	for bone in pose_bones:
		convert_one_act_one_bon(obj, action, bone, order)

# All Actions, selected bones
def convert_all_act_sel_bon(obj, pose_bones, order):
	for action in bpy.data.actions:
		for bone in pose_bones:
			convert_one_act_one_bon(obj, action, bone, order)

# All actions, All Bones (in each Action)
def convert_all_act_every_bon(obj, order):
	for action in bpy.data.actions:
		convert_one_act_every_bon(obj, action, order)

order='XYZ'
#~ order='QUATERNION'


#~ convert_one_act_sel_bon(obj, action, pose_bones, order)
convert_one_act_every_bon(obj, action, order)
#~ convert_all_act_sel_bon(obj, pose_bones, order)
#~ convert_all_act_every_bon(obj, order)

