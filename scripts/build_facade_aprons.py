"""Original jointed raised sidewalks following Malmö's existing facade arcs.
Author x east, y north, z up; glTF exports Three.js x east, z south, Y up.
"""
import bpy, math, random
import numpy as np
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
rng=random.Random(14191);parts=defaultdict(lambda:[[],[],[],[]]);mats={}
for name,color,rough in [('Apron_Concrete',(.33,.335,.305),.98),('Apron_Curb',(.38,.392,.368),.94)]:
    mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.2
    # Packed authored mineral grain survives glTF; no procedural-node dependency.
    N=256;gen=np.random.default_rng(sum(map(ord,name)));noise=gen.uniform(.86,1.10,(N,N));noise+=gen.choice([0,-.15,.15],(N,N),p=[.95,.035,.015]);pix=np.ones((N,N,4),dtype=np.float32)
    for c in range(3):pix[:,:,c]=color[c]*noise
    im=bpy.data.images.new(name+' mineral grain',width=N,height=N);im.pixels.foreach_set(pix.ravel());im.pack();tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color']);vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Color';mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mat.node_tree.links.new(tx.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(vc.outputs['Color'],mix.inputs[2]);mat.node_tree.links.new(mix.outputs['Color'],bs.inputs['Base Color']);mats[name]=mat

def add(group,mat,verts,faces,color):
    vs,fs,uvs,cols=parts[(group,mat)];off=len(vs);vs.extend(verts)
    for f in faces:
        fs.append(tuple(i+off for i in f))
        for i in f:uvs.append((verts[i][0]/.8,verts[i][1]/.8));cols.append((*color,1))

def slab(group,mat,r0,r1,a0,a1,z=.14,bevel=.004,tint=1,tilt=0):
    # A curved wedge per slab has physically open joints, top bevel, vertical sides.
    # Bottom faces omitted, as buried. Clockwise coordinates would invert top normals.
    xy=[(r0,a0),(r1,a0),(r1,a1),(r0,a1)]
    outer=[(r*math.cos(a),r*math.sin(a)) for r,a in xy]
    ac=(a0+a1)/2;rc=(r0+r1)/2
    inner=[(r0+bevel,a0+bevel/rc),(r1-bevel,a0+bevel/rc),(r1-bevel,a1-bevel/rc),(r0+bevel,a1-bevel/rc)]
    def height(a):return z+tilt*(a-ac)/max(.001,(a1-a0))
    verts=[(x,y,.008) for x,y in outer]+[(x,y,height(a)-bevel) for (x,y),(r,a) in zip(outer,xy)]+[(r*math.cos(a),r*math.sin(a),height(a)) for r,a in inner]
    faces=[(8,9,10,11)]
    for j in range(4):k=(j+1)%4;faces.extend([(j,k,k+4,j+4),(j+4,k+4,k+8,j+8)])
    add(group,mat,verts,faces,(tint,tint,tint))

slabs=0;curbs=0
for group,rmin,rmax,start,end in [('North',24.7,27.08,39,134),('West',26.65,29.08,151,218)]:
    astart=math.radians(start);aend=math.radians(end)
    # Recessed joint bed also closes the raised apron at its two ends.
    count=math.ceil((aend-astart)*(rmin+rmax)/2/.6)
    for i in range(count):
        a0=astart+(aend-astart)*i/count;a1=astart+(aend-astart)*(i+1)/count
        slab(group,'Apron_Concrete',rmin,rmax,a0,a1,z=.115,bevel=.001,tint=.48)
    # Individual granite street-side curbs, slightly taller than paving.
    count=math.ceil((aend-astart)*(rmin+.11)/.61)
    for i in range(count):
        a0=astart+(aend-astart)*i/count+.004/(rmin+.11);a1=astart+(aend-astart)*(i+1)/count-.004/(rmin+.11)
        slab(group,'Apron_Curb',rmin,rmin+.215,a0,a1,z=.159+rng.uniform(-.002,.002),bevel=.009,tint=rng.uniform(.85,1.1));curbs+=1
    # Five radial courses, roughly 60 x 45cm. Alternate joints offset half a slab.
    inside=rmin+.226;rows=5;dr=(rmax-inside)/rows
    for row in range(rows):
        r0=inside+row*dr+.004;r1=inside+(row+1)*dr-.004;rm=(r0+r1)/2;step=.6/rm
        a=astart-(step*.5 if row%2 else 0)
        while a<aend:
            lo=max(astart,a)+.004/rm;hi=min(aend,a+step)-.004/rm
            if hi-lo>.035/rm:
                irregular=rng.random()<.045
                slab(group,'Apron_Concrete',r0,r1,lo,hi,z=.14+(rng.uniform(.009,.014) if irregular else rng.uniform(-.0015,.0015)),bevel=.004,tint=rng.uniform(.86,1.08),tilt=rng.uniform(-.015,.015) if irregular else 0);slabs+=1
            a+=step
triangles=0
for (group,mat),(verts,faces,uvs,colors) in parts.items():
    name='Facade_Apron_'+group+'_'+mat;data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.materials.append(mats[mat]);data.update();uv=data.uv_layers.new(name='UVMap');ca=data.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER')
    for u,c,v,col in zip(uv.data,ca.data,uvs,colors):u.uv=v;c.color=col
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);triangles+=sum(len(f)-2 for f in faces)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/facade-aprons.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/facade-aprons.glb'),export_format='GLB',export_vertex_color='NAME',export_vertex_color_name='Color',export_yup=True,export_apply=True,export_cameras=False,export_lights=False)
print('APRON COMPLETE:',len(parts),'meshes;',triangles,'triangles;',slabs,'individual paving slabs;',curbs,'individual curbs')
