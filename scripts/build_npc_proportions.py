"""Refine the original portrait NPC, retaining face, cloth details and limb pivots."""
import bpy, bmesh
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'public/assets/npc-cloth.glb'))
root=bpy.data.objects.get('NPC')
assert root is not None
# Undo the exaggerated extra torso expansion, preserving all jacket seams together.
for o in root.children:
 if o.type=='MESH':o.scale.x*=.80;o.scale.y*=.80
 if 'Arm' in o.name:
  o.location.x*=.815
  o.scale.x*=.88;o.scale.y*=.9
# Reduce the pear-shaped abdomen while keeping a broad chest and shoulders.
# Deform the jacket and its zipper/pockets together in character coordinates.
bpy.context.view_layer.update()
for o in root.children:
 if o.type != 'MESH': continue
 matrix=o.matrix_world.copy();inverse=matrix.inverted()
 for v in o.data.vertices:
  co=matrix@v.co
  t=max(0,min(1,(co.z-.97)/.39));t=t*t*(3-2*t)
  co.x*=.84+.16*t;co.y*=.85+.15*t
  v.co=inverse@co
 bpy.context.view_layer.objects.active=o
 if o.data.has_custom_normals:
  bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free();o.data.update()
# A natural overall height increase keeps the face unsquashed and feet grounded.
root.scale*=1.06
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/npc-proportions.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/npc-proportions.blend'))
print('NPC_PROPORTIONS_COMPLETE',flush=True)
