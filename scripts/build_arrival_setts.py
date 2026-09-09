"""Original individually cut granite setts for the arrival street.
Variable coursing, staggered joints, two repairs and a fitted manhole collar.
All geometry and texture sampling are authored locally; no downloaded assets.
"""
import bpy,math,random,bmesh,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rng=random.Random(73105)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
verts=[];faces=[];uvs=[];colors=[];stone_count=0
axis=(-.7933533403,-.608761429)
mat=bpy.data.materials.new('Arrival hand laid weathered granite');mat.use_nodes=True
p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.77
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'public/assets/granite-grain.png'));tex.image.pack()
mat.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
def point(t,l):return (axis[0]*t-axis[1]*l,axis[1]*t+axis[0]*l)
def stone(poly,t,l,repair=False):
 global stone_count
 stone_count+=1;cx=sum(x for x,y in poly)/len(poly);cy=sum(y for x,y in poly)/len(poly)
 # Distinct natural gray, pink and warm granite, blended into coherent repairs.
 warmth=rng.uniform(-.045,.045);tone=.76+rng.random()*.17
 tone*=.96+.055*math.sin(t*.48+l*.73)+.025*math.sin(l*1.9-t*.21)
 if repair:tone*=1.09;warmth-=.025
 color=(tone*(1+warmth),tone,tone*(1-warmth*.7),1)
 off=len(verts);n=len(poly);cu=rng.random();cv=rng.random();a=rng.random()*math.tau;c=math.cos(a);s=math.sin(a)
 top=.015+(.003*math.sin(t*.83+l*.7))+rng.uniform(-.0015,.0015)
 for level in range(2):
  for x,y in poly:
   if level:x=cx+(x-cx)*.965;y=cy+(y-cy)*.95
   wx,wz=point(x,y);h=top+rng.uniform(-.0015,.0015) if level else -.022
   verts.append((wx,-wz,h));du=x-cx;dv=y-cy
   uvs.append((cu+(du*c-dv*s)*1.35,cv+(du*s+dv*c)*1.35));colors.append(color)
 wx,wz=point(cx,cy);verts.append((wx,-wz,top+rng.uniform(-.0005,.0015)));uvs.append((cu,cv));colors.append(color)
 for i in range(n):
  j=(i+1)%n;faces.append((off+i,off+j,off+n+j,off+n+i));faces.append((off+n+i,off+n+j,off+2*n))
def rect(t,l,depth,width,repair=False):
 a=t-depth/2;b=t+depth/2;c=l-width/2;d=l+width/2;ch=rng.uniform(.006,.012)
 poly=[(a+ch,c),(b-ch,c),(b,c+ch),(b,d-ch),(b-ch,d),(a+ch,d),(a,d-ch),(a,c+ch)]
 stone([(x+rng.uniform(-.001,.001),y+rng.uniform(-.001,.001)) for x,y in poly],t,l,repair)
t=21.68;row=0
while t<41.92:
 depth=rng.uniform(.145,.181);center=t+depth/2
 l=-3.88
 while l<3.88:
  width=min(rng.uniform(.205,.322),3.88-l)
  if width<.065:break
  mid=l+width/2
  wave=.016*math.sin(mid*.7+row*.075)+.012*math.sin(mid*1.8+row*.03)
  # Keep metal drains clear. Fit a separate annular collar around the manhole.
  hole=math.hypot(center+wave-34.2,mid-.7)<.59
  drain=any(abs(center-v)<.30 and abs(mid)>3.46 for v in [27.4,41.7])
  repair=(28.55<center<30.0 and -.9<mid<.95) or (37.2<center<38.1 and -2.7<mid<-1.5)
  if not hole and not drain:rect(center+wave,mid,depth-.005,width-.005,repair)
  l+=width
 t+=depth;row+=1
# Radial collar, fitting the existing round drain cover and breaking the courses.
for i in range(25):
 a=i*math.tau/25+.008;b=(i+1)*math.tau/25-.008
 poly=[(34.2+math.cos(a)*.35,.7+math.sin(a)*.35),(34.2+math.cos(b)*.35,.7+math.sin(b)*.35),(34.2+math.cos(b)*.61,.7+math.sin(b)*.61),(34.2+math.cos(a)*.61,.7+math.sin(a)*.61)]
 stone(poly,34.2,.7,True)
me=bpy.data.meshes.new('Unique staggered granite courses');me.from_pydata(verts,[],faces);me.materials.append(mat);me.update()
uv=me.uv_layers.new(name='Randomized granite face UV')
for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
col=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,v in enumerate(col.data):v.color=colors[i]
me.color_attributes.active_color=col
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
o=bpy.data.objects.new('Arrival_Unique_Granite_Setts',me);bpy.context.collection.objects.link(o)
bpy.context.view_layer.objects.active=o;o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/arrival-setts.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_vertex_color='ACTIVE')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/arrival-setts.blend'))
me.calc_loop_triangles();report={'stones':stone_count,'triangles':len(me.loop_triangles),'drawCalls':1,'rows':row}
(ROOT/'.dream-loop/arrival-setts-report.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
