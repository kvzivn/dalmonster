"""Original chipped granite setts for efficient instancing on the island paths."""
import bpy,math,random,os,bmesh
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('Path granite');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.72
random.seed(337)
for index in range(6):
 w=.238;d=.135;ch=.007+random.random()*.007
 outline=[(-w/2+ch,-d/2),(w/2-ch,-d/2),(w/2,-d/2+ch),(w/2,d/2-ch),(w/2-ch,d/2),(-w/2+ch,d/2),(-w/2,d/2-ch),(-w/2,-d/2+ch)]
 vs=[];fs=[]
 for j,(x,y) in enumerate(outline):vs.append((x,y,-.029+random.uniform(-.002,.002)))
 for j,(x,y) in enumerate(outline):vs.append((x*.94+random.uniform(-.0015,.0015),y*.94+random.uniform(-.001,.001),.008+random.uniform(-.0025,.0025)))
 for j in range(8):fs.append((j,(j+1)%8,(j+1)%8+8,j+8))
 fs.append(tuple(range(8,16)))
 me=bpy.data.meshes.new('Chipped granite template');me.from_pydata(vs,[],fs);me.materials.append(mat);me.update()
 o=bpy.data.objects.new('Paver_'+str(index),me);bpy.context.collection.objects.link(o)
 uv=me.uv_layers.new(name='Granite atlas')
 # Each template samples the unjointed center of a different real granite face from the supplied generated texture.
 centers=[(.11,.055),(.43,.17),(.74,.39),(.28,.65),(.57,.82),(.88,.94)]
 cu,cv=centers[index]
 for poly in me.polygons:
  for li in poly.loop_indices:
   v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(cu+v.x*.25,cv+v.y*.28)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
# Long individual granite curb block, beveled and subtly uneven.
w=.57;d=.25
bpy.ops.mesh.primitive_cube_add(size=1);o=bpy.context.object;o.name='CurbBlock';o.dimensions=(w,d,.22);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
o.data.materials.append(mat);bev=o.modifiers.new('Worn stone edges','BEVEL');bev.width=.009;bev.segments=1;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bev.name)
for v in o.data.vertices:v.co.z+=random.uniform(-.003,.003)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'public/assets/pavers.glb'),export_format='GLB',export_yup=True,export_apply=True,use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'.dream-loop/pavers.blend'))
print('Six 22-triangle chipped sett templates and one beveled curb block exported.')
