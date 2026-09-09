"""Original Blender character derivatives with tailored cloth and weighted joints.

Technique references: Blender Armature Modifier manual (vertex group binding),
Sculpt Brush Assets manual (directional compression rather than isotropic blobs).
No simulation, subdivision or corrective modifier remains in exported glTF.
Run: Blender -b -t 3 --python scripts/build_characters_refined.py
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Matrix, Vector
ROOT = Path(__file__).resolve().parents[1]

def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)

def components(mesh):
 links=[set() for _ in mesh.vertices]
 for e in mesh.edges:
  a,b=e.vertices;links[a].add(b);links[b].add(a)
 remaining=set(range(len(links)));groups=[]
 while remaining:
  seed=remaining.pop();group=[seed];queue=[seed]
  while queue:
   for v in links[queue.pop()]:
    if v in remaining:remaining.remove(v);group.append(v);queue.append(v)
  groups.append(group)
 return sorted(groups,key=len,reverse=True)

def reflow_sleeve(mesh, side, wide, female):
 # Continuous conical tailoring replaces the old alternating inflated rings.
 group=components(mesh)[0]
 # The former sleeve is the largest connected surface; preserve hands/cuff/seam.
 points=[mesh.vertices[i].co for i in group]
 if max(p.z for p in points)-min(p.z for p in points)<.3:return 0
 rows=[(-.49,.059,.058),(-.42,.063,.064),(-.31,.074,.075),
       (-.24,.083,.085),(-.15,.089,.091),(-.065,.099,.098),(.0,.096,.094),(.06,.035,.04)]
 factor=1.26 if wide else (.79 if female else 1.0)
 changed=0
 for i in group:
  p=mesh.vertices[i].co;z=p.z
  if z<-.47 or z>.035:continue
  t=max(0,min(1,-z/.26));cx=side*.078*(1-(1-t)**2);cy=-.05*smooth(-.06,.48,-z)
  if female:cx*=.87;cy*=1.2
  rx=ry=0
  for a,b in zip(rows,rows[1:]):
   if a[0]<=z<=b[0]:
    q=(z-a[0])/(b[0]-a[0]);rx=(a[1]*(1-q)+b[1]*q)*factor;ry=(a[2]*(1-q)+b[2]*q)*factor;break
  if not rx:continue
  angle=math.atan2((p.y-cy)/ry,(p.x-cx)/rx)
  # Two oblique asymmetric elbow rolls, terminating before sleeve seams/cuffs.
  mask=smooth(-.46,-.40,z)*(1-smooth(.015,.060,z))
  phase=.45 if side<0 else 1.05
  d=z+.251-.036*math.cos(angle+phase)
  ridge=math.exp(-(d/.028)**2)-.48*math.exp(-((d+.032)/.024)**2)
  d2=z+.336+.027*math.cos(angle-.8)
  fold=(.009*ridge+.004*(math.exp(-(d2/.024)**2)-.45*math.exp(-((d2+.025)/.02)**2))*(.30+.70*max(0,-math.sin(angle+.5))))
  target=Vector((cx+(rx+fold)*math.cos(angle),cy+(ry+fold)*math.sin(angle),z))
  p.x=p.x*(1-mask*.78)+target.x*mask*.78;p.y=p.y*(1-mask*.78)+target.y*mask*.78;changed+=1
 return changed

def normalize_mesh(o, parent):
 bpy.context.view_layer.update();matrix=parent.matrix_world.inverted()@o.matrix_world
 o.data.transform(matrix);o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4)
 # glTF duplicates vertices along UV islands; weld positions while keeping loop UVs
 # before component selection, so a sleeve is one continuous sculpted surface.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free()
 if o.data.has_custom_normals:
  bpy.context.view_layer.objects.active=o;bpy.ops.mesh.customdata_custom_splitnormals_clear()

def finish_surface(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free();o.data.update()
 # Minute tonal wear, not geometric noise; retain source zipper color attributes.
 colors=o.data.color_attributes.active_color
 if not colors:
  colors=o.data.color_attributes.new(name='TailoredWear',type='FLOAT_COLOR',domain='CORNER')
  for c in colors.data:c.color=(1,1,1,1)
 o.data.color_attributes.active_color=colors
 for polygon in o.data.polygons:
  material=o.data.materials[polygon.material_index]
  fabric=any(w in material.name.lower() for w in ['canvas','jacket','cloth','wool','denim','twill','scarf'])
  if not fabric:continue
  for li in polygon.loop_indices:
   p=o.data.vertices[o.data.loops[li].vertex_index].co
   shade=.958+.026*math.sin(p.z*8.5+p.x*4)+.016*math.sin(p.x*37+p.y*12+p.z*20)
   c=colors.data[li].color
   if c[3]==0:c=(1,1,1,1)
   colors.data[li].color=(c[0]*shade,c[1]*shade,c[2]*shade,1)

def rig_limb(limb, asset):
 side=-1 if limb.name.startswith('Left') else 1
 isleg='Leg' in limb.name;prefix='Left' if side<0 else 'Right'
 meshes=[o for o in limb.children_recursive if o.type=='MESH']
 for o in meshes:normalize_mesh(o,limb)
 for o in list(limb.children):
  if o.type=='EMPTY' and not o.children:bpy.data.objects.remove(o,do_unlink=True)
 # Keep source material grouping and draw count: one modifier per original mesh.
 changed=0
 if not isleg:
  for o in meshes:changed+=reflow_sleeve(o.data,side,asset=='npc',asset=='pedestrian-a')
 h=limb.location.z
 joint=.405 if isleg else .255
 ankle=h-.13
 upper=prefix+('ThighDeform' if isleg else 'UpperArmDeform')
 lower=prefix+('Knee' if isleg else 'Elbow')
 foot=prefix+'Foot'
 arm=bpy.data.armatures.new(prefix+('LegRig' if isleg else 'ArmRig'))
 rig=bpy.data.objects.new(arm.name,arm);bpy.context.collection.objects.link(rig);rig.parent=limb
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 # Vertical bones deliberately share orientation: local +X equals character +X.
 a=arm.edit_bones.new(upper);a.head=(0,0,0);a.tail=(0,0,-joint);a.roll=0
 b=arm.edit_bones.new(lower);b.head=a.tail;b.tail=(0,0,-ankle if isleg else -.49);b.parent=a;b.use_connect=True;b.roll=0
 if isleg:
  c=arm.edit_bones.new(foot);c.head=b.tail;c.tail=(0,0,-h-.03);c.parent=b;c.use_connect=True;c.roll=0
 bpy.ops.object.mode_set(mode='OBJECT')
 weighted=0
 for o in meshes:
  o.parent=rig
  groups={n:o.vertex_groups.new(name=n) for n in [upper,lower]+([foot] if isleg else [])}
  for v in o.data.vertices:
   z=-v.co.z
   blend=smooth(joint-.07,joint+.075,z)
   shoe=smooth(ankle-.025,ankle+.045,z) if isleg else 0
   if isleg and z>=h-.10:shoe=1
   weights={upper:1-blend,lower:blend*(1-shoe)}
   if isleg:weights[foot]=blend*shoe
   for name,w in weights.items():
    if w>1e-5:groups[name].add([v.index],w,'REPLACE')
   if 1e-5<blend<.99999:weighted+=1
  mod=o.modifiers.new('Weighted natural joint deformation','ARMATURE');mod.object=rig;mod.use_vertex_groups=True;mod.use_bone_envelopes=False;mod.use_deform_preserve_volume=False
  finish_surface(o)
 return {'pivot':limb.name,'joint':lower,'jointDepth':joint,'ankleDepth':ankle if isleg else None,'blendedVertices':weighted,'tailoredSleeveVertices':changed}

def materials():
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  p=m.node_tree.nodes.get('Principled BSDF')
  if not p:continue
  name=m.name.lower()
  if 'skin' in name or 'lips' in name:
   p.inputs['Roughness'].default_value=.66 if 'dark warm' in name else .71
   p.inputs['Specular IOR Level'].default_value=.28
  if 'eye white' in name:
   p.inputs['Base Color'].default_value=(.23,.21,.17,1);p.inputs['Roughness'].default_value=.4
  if any(w in name for w in ['canvas','jacket','wool','denim','twill','scarf']):
   p.inputs['Roughness'].default_value=.88 if 'jacket' in name else .94
   p.inputs['Specular IOR Level'].default_value=.21
   for n in m.node_tree.nodes:
    if n.type=='NORMAL_MAP':n.inputs['Strength'].default_value=.15

def refine_player_head(head):
 """Anatomical face planes and a softly irregular, fitted hood opening."""
 def bump(x,z,cx,cz,wx,wz):return math.exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
 for o in head.children:
  if o.type!='MESH':continue
  normalize_mesh(o,head)
  me=o.data;groups=components(me)
  skin_index=next(i for i,m in enumerate(me.materials) if m.name=='Warm shaded skin')
  colors=me.color_attributes.active_color or me.color_attributes.new(name='FacePlaneTint',type='FLOAT_COLOR',domain='CORNER')
  me.color_attributes.active_color=colors
  for c in colors.data:c.color=(1,1,1,1)
  for group in groups:
   vs=set(group);polys=[p for p in me.polygons if p.vertices[0] in vs]
   material=me.materials[polys[0].material_index].name
   pts=[me.vertices[i].co for i in group]
   zmin=min(p.z for p in pts);zmax=max(p.z for p in pts)
   if material=='Warm shaded skin' and len(group)>200:
    for p in pts:
     x,z=p.x,p.z
     # Narrow adult jaw/chin, stronger cheekbones and a flatter temple.
     jaw=.75+.25*smooth(-.132,-.029,z)
     temple=1-.07*smooth(.026,.096,z)
     p.x*=jaw*temple
     front=1-smooth(-.150,-.096,p.y)
     plane=.006*bump(x,z,0,.075,.085,.035)
     for side in [-1,1]:
      plane+=.009*bump(x,z,side*.043,.045,.027,.015)
      plane-=.009*bump(x,z,side*.042,.019,.025,.019)
      plane+=.007*bump(x,z,side*.058,-.024,.026,.027)
     plane+=.010*bump(x,z,0,-.022,.018,.060)
     plane+=.005*bump(x,z,0,-.108,.032,.022)
     p.y-=plane*front
   elif material=='Warm shaded skin' and 60<len(group)<120:
    # Taper the nose bridge and widen its lower plane without a separate ball tip.
    for p in pts:
     p.x*=.69+.53*(1-smooth(-.046,-.002,p.z))
     p.y-=.005*math.exp(-((p.z+.040)/.021)**2)
   elif material=='Rubber and black leather' and 30<len(group)<80:
    # Eyes sit inside sockets with narrower lids, instead of round protruding beads.
    for p in pts:p.z=.022+(p.z-.022)*.58;p.y+=.0035
   elif material=='Rubber and black leather' and zmax<-.05 and len(group)<30:
    for p in pts:p.z=-.072+(p.z+.069)*.33;p.y+=.002
    for poly in polys:
     poly.material_index=skin_index
     for li in poly.loop_indices:colors.data[li].color=(.43,.40,.37,1)
   if material in ['Weathered charcoal canvas','Worn stitched charcoal edges']:
    for p in pts:
     front=1-smooth(-.10,.10,p.y)
     lower=1-smooth(-.035,.115,p.z)
     # The opening gathers at the jaw and hangs unevenly into the collar.
     p.x*=1-.085*lower*front
     p.x+=.0045*math.sin(p.z*13+.4)*front
     p.y+=.0065*math.sin(p.x*17+.65)*lower*front
     p.z+=.004*math.sin(p.x*12+.5)*lower*front
  # Darker piping reads as sewn fabric rather than a bright, perfectly oval border.
  for i,m in enumerate(me.materials):
   if m.name=='Worn stitched charcoal edges':
    m=m.copy();m.name='Soft charcoal hood seam';me.materials[i]=m
    p=m.node_tree.nodes.get('Principled BSDF');c=p.inputs['Base Color'].default_value
    p.inputs['Base Color'].default_value=(c[0]*.67,c[1]*.67,c[2]*.67,1)
   if m.name=='Warm shaded skin':
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.235,.163,.124,1)
  finish_surface(o)

reports={}
for asset,source,rootname in [('player','player-cloth','Player'),('npc','npc-proportions','NPC'),('pedestrian-a','pedestrian-a','PedestrianA'),('pedestrian-b','pedestrian-b','PedestrianB')]:
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for m in list(bpy.data.materials):bpy.data.materials.remove(m)
 bpy.ops.import_scene.gltf(filepath=str(ROOT/f'public/assets/{source}.glb'))
 root=bpy.data.objects.get(rootname);assert root
 limbs=[bpy.data.objects[n] for n in ['LeftLeg','RightLeg','LeftArm','RightArm']]
 joints=[rig_limb(l,asset) for l in limbs]
 if asset=='player':refine_player_head(bpy.data.objects['Head'])
 for o in root.children:
  if o.type=='MESH':finish_surface(o)
 materials();bpy.context.view_layer.update()
 bpy.ops.object.select_all(action='SELECT')
 dest=ROOT/f'public/assets/{asset}-refined.glb'
 bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_skins=True,export_all_vertex_colors=False)
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/f'.dream-loop/{asset}-refined.blend'))
 for o in root.children_recursive:
  if o.type=='MESH':o.data.calc_loop_triangles()
 reports[asset]={'file':dest.name,'joints':joints,'triangles':sum(len(o.data.loop_triangles) for o in root.children_recursive if o.type=='MESH'),'materialSlots':sum(len(o.data.materials) for o in root.children_recursive if o.type=='MESH')}
 print('REFINED',asset,json.dumps(reports[asset]),flush=True)
(ROOT/'.dream-loop/characters-refined-report.json').write_text(json.dumps(reports,indent=2))
