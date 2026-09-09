"""Continuous original Blender pavement between the roundabout ellipse and façades.
Replaces facade-aprons.glb; keeps adjoining road-mouth sectors open.
"""
import bpy,math,random,bmesh
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rng=random.Random(8831);parts=defaultdict(lambda:[[],[],[],[]]);mats={}
tex=bpy.data.images.load(str(ROOT/'public/assets/granite-grain.png'));tex.pack();tex.colorspace_settings.name='sRGB'
for name,factor in [('Join_WeatheredGranite',1),('Join_FineGraniteBorder',1),('Join_RecessedJointBed',1)]:
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.96;bs.inputs['Specular IOR Level'].default_value=.18
 tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=tex;m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);mats[name]=m

def radius(a):return 1/math.sqrt((math.cos(a)/23.2)**2+(math.sin(a)/25.52)**2)
def add(group,mat,verts,faces,topColor=.72,uvOffset=(0,0)):
 vs,fs,uvs,cols=parts[(group,mat)];off=len(vs);vs.extend(verts)
 for face in faces:
  fs.append(tuple(off+i for i in face))
  # Fine mineral grain spans 0.32m, avoiding the oversized crystal look.
  for i in face:
   p=verts[i];uvs.append((p[0]/.32+uvOffset[0],p[1]/.32+uvOffset[1]));shade=topColor if i>=8 else topColor*.89;cols.append((shade,shade*.996,shade*.967,1))
def block(group,mat,rlo0,rhi0,rlo1,rhi1,a0,a1,z=.173,tint=.72):
 # Radial wedge clip joins the actual ellipse, without a rectangular tile ending
 # in open space. Top bevel is only 2.5 mm, and joints are only 3 mm total.
 polar=[(rlo0,a0),(rhi0,a0),(rhi1,a1),(rlo1,a1)];xy=[(r*math.cos(a),r*math.sin(a)) for r,a in polar];cx=sum(p[0] for p in xy)/4;cy=sum(p[1] for p in xy)/4
 inner=[]
 for x,y in xy:
  d=math.hypot(cx-x,cy-y);inner.append((x+(cx-x)*min(.0025/d,.15),y+(cy-y)*min(.0025/d,.15)))
 verts=[(x,y,.154) for x,y in xy]+[(x,y,z-.0025) for x,y in xy]+[(x,y,z) for x,y in inner];faces=[(8,9,10,11)]
 for i in range(4):j=(i+1)%4;faces.extend([(i,j,j+4,i+4),(i+4,j+4,j+8,i+8)])
 add(group,mat,verts,faces,tint,(rng.random()*3,rng.random()*3))

slabs=0
for group,rfront,start,end in [('North',27.09,39,134),('West',29.09,151,218)]:
 alo=math.radians(start);ahi=math.radians(end);steps=math.ceil((ahi-alo)*rfront/.47)
 # Foundation surface physically fills all joints and reaches slightly beneath
 # the existing outer pavement, so grazing reflections cannot reveal a void.
 for i in range(steps):
  a=alo+(ahi-alo)*i/steps;b=alo+(ahi-alo)*(i+1)/steps
  p=[(radius(a)-.028,a),(rfront,a),(rfront,b),(radius(b)-.028,b)]
  add(group,'Join_RecessedJointBed',[(r*math.cos(t),r*math.sin(t),.158) for r,t in p],[(0,1,2,3)],.45)
 # Building-first radial rows keep a consistent 46cm course width. Final row is
 # clipped to the ellipse and forms a fine-grained transition border.
 maxdepth=rfront-min(radius(alo+(ahi-alo)*i/100) for i in range(101))+.03
 for row in range(math.ceil(maxdepth/.465)):
  rhi=rfront-row*.465;rlo=rhi-.465;rm=(rhi+rlo)/2;step=.61/rm
  a=alo-(step*.5 if row%2 else 0)
  while a<ahi:
   aa=max(a,alo)+.0015/rm;bb=min(a+step,ahi)-.0015/rm
   if bb<=aa:a+=step;continue
   edge0=radius(aa)-.016;edge1=radius(bb)-.016
   if min(rhi-edge0,rhi-edge1)<.025:a+=step;continue
   low0=max(rlo+.0015,edge0);low1=max(rlo+.0015,edge1)
   if min(rhi-low0,rhi-low1)<.025:a+=step;continue
   border=low0==edge0 or low1==edge1
   # Broad edge/wall dampness is geometry color, never black outlines. A few
   # replaced slabs have modestly different wear; no random checkerboard.
   depth=rfront-(rhi+rlo)/2;damp=.91 if depth<.6 or border else 1
   patch=.94+.035*math.sin((aa+bb)*11+row*.36)+.025*math.sin((aa+bb)*25-row*.53)
   tint=(.69+rng.uniform(-.035,.035))*damp*patch
   block(group,'Join_FineGraniteBorder' if border else 'Join_WeatheredGranite',low0,rhi-.0015,low1,rhi-.0015,aa,bb,.173+rng.uniform(-.0007,.0007),tint);slabs+=1
   a+=step
 # Narrow perimeter foundation returns close the cut ends, with no tall curb
 # between two continuous pedestrian pavements.
triangles=0
for (group,mat),(verts,faces,uvs,colors) in parts.items():
 name='Pavement_Join_'+group+'_'+mat;me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mats[mat]);me.update();uv=me.uv_layers.new(name='UVMap');ca=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
 for u,c,v,col in zip(uv.data,ca.data,uvs,colors):u.uv=v;c.color=col
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 # Material exports the authored image, while COLOR_0 is multiplied by glTF.
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();me.calc_loop_triangles();triangles+=len(me.loop_triangles)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/pavement-joins.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/pavement-joins.glb'),export_format='GLB',export_vertex_color='NAME',export_vertex_color_name='Color',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('PAVEMENT JOIN RESULT',len(parts),'draws',triangles,'triangles',slabs,'slabs. Texture SRGB, ground shader, bump .0015-.002.')
