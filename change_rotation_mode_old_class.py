import bpy

class convert():

	def get_or_create_fcurve(self, action, data_path, array_index=-1, group=None):
		for fc in action.fcurves:
			if fc.data_path == data_path and (array_index<0 or fc.array_index == array_index):
				return fc

		fc = action.fcurves.new(data_path, array_index)
		fc.group = group
		return fc

	def add_keyframe_quat(self, action, quat, frame, bone_prefix, group):
		for i in range(len(quat)):
			fc = self.get_or_create_fcurve(action, bone_prefix+"rotation_quaternion", i, group)
			pos = len(fc.keyframe_points)
			fc.keyframe_points.add(1)
			fc.keyframe_points[pos].co = [frame, quat[i]]
			fc.update()

	def add_keyframe_euler(self, action, euler, frame, bone_prefix, group):
		for i in range(len(euler)):
			fc = self.get_or_create_fcurve(action, bone_prefix+"rotation_euler", i, group)
			pos = len(fc.keyframe_points)
			fc.keyframe_points.add(1)
			fc.keyframe_points[pos].co = [frame, euler[i]]
			fc.update()


	def frames_matching(self, action, data_path):
		frames = set()
		for fc in action.fcurves:
			if fc.data_path == data_path:
				fri = [kp.co[0] for kp in fc.keyframe_points]
				frames.update(fri)
		return frames

	# Converts only one group/bone in one action - Quat to euler
	def group_qe(self, obj, action, bone, bone_prefix, order):
		
		pose_bone = bone
		data_path = bone_prefix + "rotation_quaternion"
		frames = self.frames_matching(action, data_path)
		group = action.groups[bone.name]
		
		for fr in frames:
			quat = bone.rotation_quaternion.copy()
			for fc in action.fcurves:
				if fc.data_path == data_path:
					quat[fc.array_index] = fc.evaluate(fr)
			euler = quat.to_euler(order)

			self.add_keyframe_euler(action, euler, fr, bone_prefix, group)
			bone.rotation_mode = order

	# Converts only one group/bone in one action - Euler to Quat
	def group_eq(self, obj, action, bone, bone_prefix, order):
		
		pose_bone = bone
		data_path = bone_prefix + "rotation_euler"
		frames = self.frames_matching(action, data_path)
		group = action.groups[bone.name]
		
		for fr in frames:
			euler = bone.rotation_euler.copy()
			for fc in action.fcurves:
				if fc.data_path == data_path:
					euler[fc.array_index] = fc.evaluate(fr)
			quat = euler.to_quaternion()

			self.add_keyframe_quat(action, quat, fr, bone_prefix, group)
			bone.rotation_mode = order

	# One Action - One Bone
	def one_act_one_bon(self, obj, action, bone, order):
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
			self.group_qe(obj, action, bone, bone_prefix, order)
			
			# Removes quaternion fcurves
			for key in action.fcurves:
				if key.data_path == 'pose.bones["' + bone.name + '"].rotation_quaternion':
					action.fcurves.remove(key)

		elif do and order_quat:
			# Converts the group/bone from Euler to Quat
			self.group_eq(obj, action, bone, bone_prefix, order)

			# Removes euler fcurves
			for key in action.fcurves:
				if key.data_path == 'pose.bones["' + bone.name + '"].rotation_euler':
					action.fcurves.remove(key)
		
		# Changes rotation mode to new one
		bone.rotation_mode = order

	
	# One Action, selected bones
	def one_act_sel_bon(self, obj, action, pose_bones, order):
		for bone in pose_bones:
			self.one_act_one_bon(obj, action, bone, order)

	# One action, all Bones (in Action)
	def one_act_every_bon(self, obj, action, order):
		
		# Collects pose_bones that are in the action
		pose_bones = set()
		# Checks all fcurves
		for fcurve in action.fcurves:
			# Look for the ones that has rotation_quaternion
			if order == 'QUATERNION':
				if fcurve.data_path.endswith('rotation_euler'):
					if obj.pose.bones[fcurve.group.name] not in pose_bones:
						pose_bones.add(obj.pose.bones[fcurve.group.name])
			else:
				if fcurve.data_path.endswith('rotation_quaternion'):
					if obj.pose.bones[fcurve.group.name] not in pose_bones:
						pose_bones.add(obj.pose.bones[fcurve.group.name])
				
		
		# Convert current action and pose_bones that are in each action
		print(pose_bones)
		for bone in pose_bones:
			self.one_act_one_bon(obj, action, bone, order)

	# All Actions, selected bones
	def all_act_sel_bon(self, obj, pose_bones, order):
		for action in bpy.data.actions:
			for bone in pose_bones:
				self.one_act_one_bon(obj, action, bone, order)

	# All actions, All Bones (in each Action)
	def all_act_every_bon(self, obj, order):
		for action in bpy.data.actions:
			self.one_act_every_bon(obj, action, order)


convert = convert()

obj = bpy.context.active_object
pose_bones = bpy.context.selected_pose_bones
action = obj.animation_data.action

#~ order='XYZ'
order='QUATERNION'


#~ convert.one_act_sel_bon(obj, action, pose_bones, order)
#~ convert.one_act_every_bon(obj, action, order)
#~ convert.all_act_sel_bon(obj, pose_bones, order)
convert.all_act_every_bon(obj, order)

