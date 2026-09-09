"""Four original bare island trees, with original trunks/roots and newly sculpted branch paths.
Uses the original authored trunk coordinates and root flare, longitudinal bark UV scale;
outputs exact Tree_0_Bark through Tree_3_Bark replacement groups only.
"""
import bpy,math,random,ast,json
from mathutils import Vector
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
groups=defaultdict(lambda:[[],[],[],[]]);collisions=[];calls=[]
def capture(mat,points,radii,n=8,group='Environment'):
 calls.append((mat,[Vector(p) for p in points],list(radii),n,group))
ns={'math':math,'random':random,'Vector':Vector,'groups':groups,'collisions':collisions,'tube':capture}
source=ast.parse((ROOT/'scripts/build_environment.py').read_text())
for name in ['mesh','bark_tube','tree']:
 definition=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[definition],type_ignores=[]),'original_'+name,'exec'),ns)
mesh=ns['mesh'];original_bark_tube=ns['bark_tube']
def cubic(p0,p1,p2,p3,t):return p0*((1-t)**3)+p1*(3*t*(1-t)**2)+p2*(3*t*t*(1-t))+p3*(t**3)
def tube(points,radii,n,g):
 # Parallel-transported cross section keeps bark fibres running along the limb.
 vv=[];uv=[];distance=0;u=None;around=max(1,math.tau*max(radii)/.65)
 for i,p in enumerate(points):
  if i:distance+=(p-points[i-1]).length
  direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
  if u is None:
   u=direction.cross(Vector((0,1,0)))
   if u.length<.02:u=direction.cross(Vector((1,0,0)))
  else:u=u-direction*u.dot(direction)
  u.normalize();v=direction.cross(u).normalized()
  for j in range(n+1):
   a=j*math.tau/n;rad=radii[i]*(1+.055*math.sin(a*3+distance*.43)+.025*math.sin(a*5-distance*.6))
   rad+=min(.003,rad*.035)*math.sin(a*7+distance*.65)
   vv.append(p+rad*(math.cos(a)*u+math.sin(a)*v));uv.append((j/n*around,distance/1.3))
 fs=[tuple(range(n-1,-1,-1))]
 for i in range(len(points)-1):
  for j in range(n):fs.append((i*(n+1)+j,i*(n+1)+j+1,(i+1)*(n+1)+j+1,(i+1)*(n+1)+j))
 fs.append(tuple((len(points)-1)*(n+1)+j for j in range(n)))
 mesh('Bark',vv,fs,g,uv)
def samplepath(pts,t):
 at=t*(len(pts)-1);i=min(len(pts)-2,int(at));return pts[i].lerp(pts[i+1],at-i)
def localdirection(pts,t):return(samplepath(pts,min(.999,t+.03))-samplepath(pts,max(0,t-.03))).normalized()
trunk_report=[]
for i,(x,y,h) in enumerate([(-7,8,7.7),(6,9,8.8),(9,-6,7.5),(-8,-6,8.1)]):
 g='Tree_'+str(i);calls.clear();ns['tree'](x,y,h,981+i,group=g);assert len(calls)==149
 # The original central bole and five roots remain bit-for-bit geometrically authored.
 for record in [calls[0],*calls[-5:]]:
  mat,pts,rads,n,group=record;original_bark_tube(pts,rads,n,group)
 rng=random.Random(72310+i)
 for j in range(11):
  record=calls[1+j*13];_,old,oldr,_,_=record;collar,origin,shoulder,oldmid,oldtip=old
  run=oldtip-origin;length=run.length;out=run.normalized();side=out.cross(Vector((0,0,1))).normalized()
  # Long S-shaped grown limbs rise smoothly out of the stem, then lift at their tips.
  start=origin-Vector((0,0,.17));p1=origin+Vector((0,0,.32))+out*.12
  bend=rng.uniform(-.20,.20);p2=origin+out*length*.66+side*bend-Vector((0,0,.12))
  tip=oldtip+side*rng.uniform(-.12,.12)+Vector((0,0,rng.uniform(-.08,.18)))
  main=[cubic(start,p1,p2,tip,k/12) for k in range(13)]
  # A lifted terminal shoot avoids a straight telegraph-pole silhouette.
  for k in range(1,len(main)-1):main[k]+=side*(math.sin(k/12*math.pi*2)*.035*(length/2))
  base_r=oldr[0]*1.04
  radii=[max(.0007,base_r*((1-k/12)**1.11)) for k in range(13)]
  # Collar swells only inside the actual trunk junction; no exterior tube plug.
  radii[0]=base_r*.85;radii[1]=base_r*1.0;radii[-1]=.0007
  tube(main,radii,12,g)
  # Asymmetric secondary branching starts on the actual curved parent centreline.
  for k in range(4):
   t=.27+k*.17+rng.uniform(-.025,.025);start=samplepath(main,t);parentdir=localdirection(main,t)
   az=math.atan2(out.y,out.x)+(-1 if k%2 else 1)*rng.uniform(.38,.95)
   enddir=Vector((math.cos(az),math.sin(az),rng.uniform(.95,1.55))).normalized();length2=length*rng.uniform(.36,.54)*(1-k*.025)
   end=start+enddir*length2;perp=enddir.cross(Vector((0,0,1))).normalized()
   c1=start+parentdir*length2*.20;c2=start+enddir*length2*.60+perp*rng.uniform(-.07,.07)+Vector((0,0,.055))
   pts=[cubic(start,c1,c2,end,u/6) for u in range(7)]
   rr=.024*(1-k*.10)*rng.uniform(.92,1.1);rads=[max(.00055,rr*((1-u/6)**1.02)) for u in range(7)];rads[-1]=.00055
   tube(pts,rads,5,g)
   for sign in [-1,1]:
    at=rng.uniform(.50,.77);p0=samplepath(pts,at);tan=localdirection(pts,at);azi=az+sign*rng.uniform(.5,.88)
    twigdir=Vector((math.cos(azi),math.sin(azi),rng.uniform(1.35,1.95))).normalized();twiglength=length*rng.uniform(.14,.235)
    end=p0+twigdir*twiglength;c1=p0+tan*twiglength*.30;c2=end-twigdir*twiglength*.35+perp*sign*.033
    twig=[cubic(p0,c1,c2,end,u/3) for u in range(4)]
    tube(twig,[.0072,.0045,.0020,.00028],4,g)
 trunk_report.append({'name':g+'_Bark','base':[x,y,.03],'height':h,'originalTrunkAndFiveRootsPreserved':True,'mainBranches':11,'secondaryBranches':44,'twigs':88})
m=bpy.data.materials.new('Bark');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.98;bs.inputs['Specular IOR Level'].default_value=.08
img=bpy.data.images.load(str(ROOT/'public/assets/tree-bark.png'));img.pack();tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=img;m.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
tri=0
for (g,mat),(verts,faces,uvs,smooth) in groups.items():
 me=bpy.data.meshes.new(g+'_Bark');me.from_pydata(verts,[],faces);me.materials.append(m);me.update();uv=me.uv_layers.new(name='UVMap')
 for u,v in zip(uv.data,uvs):u.uv=v
 for p in me.polygons:p.use_smooth=True
 ob=bpy.data.objects.new(g+'_Bark',me);bpy.context.collection.objects.link(ob);tri+=sum(len(f)-2 for f in faces)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'.dream-loop/trees-polish.blend'))
bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/assets/trees-polish.glb'),export_format='GLB',export_apply=True,export_yup=True,export_cameras=False,export_lights=False)
report={'trees':trunk_report,'triangles':tri,'previousTriangles':39408,'meshes':len(groups),'replaceNames':['Tree_'+str(i)+'_Bark' for i in range(4)],'tipRadiiMeters':{'main':.0007,'secondary':.00055,'twig':.00028},'barkUV':'Original1.3m longitudinal scale; transported frames on new limbs; original trunk/root UVs unchanged'}
(ROOT/'.dream-loop/trees-polish-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
