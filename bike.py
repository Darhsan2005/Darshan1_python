"""Super Bike Rush - ONE FILE (Flask backend + full 3D game page) (fast: in-memory state, cached static page, tiny JSON API).
Run:  pip install flask  ->  python app.py   ->  open http://127.0.0.1:5000
"""
import json, os, threading, time
from flask import Flask, jsonify, request, send_from_directory, Response

BASE = os.path.dirname(os.path.abspath(__file__))
SCORE_FILE = os.path.join(BASE, "scores.json")
app = Flask(__name__, static_folder=os.path.join(BASE, "static"), static_url_path="/static")
app.config["JSON_SORT_KEYS"] = False
lock = threading.Lock()

# Every level upgrades the bike (speed, acceleration, handling, nitro, looks).
LEVELS = [
    {"id": 1, "name": "Dawn Highway to Snow Pass", "length": 2400, "traffic": 0.35,
     "zones": [{"until": 1000, "type": "highway"}, {"until": 1800, "type": "snow"}, {"until": 2400, "type": "highway"}],
     "bike": {"name": "Apex R1 (Stock)", "top": 260, "accel": 15, "handling": 11, "nitro": 1.35, "color": "#e11d2e"}},
    {"id": 2, "name": "Mud Run & Frozen Ridge", "length": 3400, "traffic": 0.5,
     "zones": [{"until": 800, "type": "highway"}, {"until": 1900, "type": "mud"}, {"until": 2700, "type": "snow"}, {"until": 3400, "type": "highway"}],
     "bike": {"name": "Apex R1 Tuned (Winglets)", "top": 300, "accel": 18, "handling": 12.5, "nitro": 1.5, "color": "#1d6bff"}},
    {"id": 3, "name": "Blizzard Mud Highway Gauntlet", "length": 4600, "traffic": 0.65,
     "zones": [{"until": 900, "type": "snow"}, {"until": 1900, "type": "mud"}, {"until": 3000, "type": "highway"},
               {"until": 3800, "type": "snow"}, {"until": 4600, "type": "mud"}],
     "bike": {"name": "Apex R1 Hyper (Carbon Wing)", "top": 345, "accel": 22, "handling": 14, "nitro": 1.7, "color": "#f5b400"}},
]

PAGE = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Super Bike Rush</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Black+Ops+One&display=swap" rel="stylesheet">
<style>
:root{--ink:#eef3f7;--bg:#0c1117;--red:#ff3b30;--ice:#9fd8ff;--mud:#b07a3c;--panel:rgba(12,17,23,.78)}
*{box-sizing:border-box;margin:0}
html,body{height:100%;overflow:hidden;background:var(--bg);color:var(--ink);font-family:'Rajdhani',Arial,sans-serif}
canvas{display:block}
#hud{position:fixed;inset:0;pointer-events:none;display:none}
#spd{position:absolute;right:28px;bottom:22px;text-align:right;font-family:'Black Ops One',Impact,sans-serif;font-size:76px;line-height:1;text-shadow:0 2px 12px #000}
#spd small{font:700 20px Rajdhani,sans-serif;margin-left:6px;color:var(--ice)}
#info{position:absolute;left:24px;top:18px;font-size:22px;font-weight:700;text-shadow:0 2px 8px #000}
#zone{display:inline-block;margin-top:4px;padding:2px 12px;border-radius:4px;background:var(--panel)}
#bars{position:absolute;left:24px;bottom:22px;width:min(340px,50vw)}
.bar{height:10px;background:#0008;border-radius:5px;overflow:hidden;margin-top:8px}
.bar i{display:block;height:100%;width:0;background:var(--ice)}
#prog i{background:var(--red)}
#msg{position:absolute;top:30%;width:100%;text-align:center;font:44px 'Black Ops One',Impact;text-shadow:0 3px 14px #000;opacity:0;transition:opacity .3s}
#menu{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:radial-gradient(circle at 50% 30%,#1b2a3a,#07090d)}
.box{width:min(620px,92vw);background:var(--panel);padding:28px;border:1px solid #ffffff22;border-radius:10px}
h1{font:44px 'Black Ops One',Impact;letter-spacing:1px;color:var(--ink)}
h1 span{color:var(--red)}
p{font-size:19px;margin:8px 0;color:#c4ced8}
.lv{display:flex;gap:10px;margin:16px 0}
.lv button{flex:1;padding:12px 6px;font:700 18px Rajdhani;color:var(--ink);background:#1a2430;border:2px solid #ffffff22;border-radius:6px;cursor:pointer}
.lv button.on{border-color:var(--red);background:#2a1a1d}
.lv button:disabled{opacity:.35;cursor:not-allowed}
#go,#again{width:100%;padding:14px;font:700 24px Rajdhani;background:var(--red);color:#fff;border:0;border-radius:6px;cursor:pointer}
#go:focus-visible,.lv button:focus-visible{outline:3px solid var(--ice)}
#board{font-size:18px;margin-top:12px;color:#c4ced8}
#name{width:100%;padding:10px;font:700 20px Rajdhani;margin:8px 0;background:#111a24;color:var(--ink);border:1px solid #ffffff33;border-radius:6px}
</style></head><body>
<div id="hud">
  <div id="info"><div id="lvl"></div><div id="zone"></div><div id="tm">0.0s</div></div>
  <div id="bars"><div class="bar" id="prog"><i></i></div><div class="bar" id="nit"><i></i></div></div>
  <div id="spd">0<small>km/h</small></div>
  <div id="msg"></div>
</div>
<div id="menu"><div class="box" id="mbox">
  <h1>SUPER BIKE <span>RUSH</span></h1>
  <p>Three levels. Every level your superbike gets an upgrade. Highway, snow and mud change your grip.</p>
  <div class="lv" id="lv"></div>
  <p id="binfo"></p>
  <button id="go">Start ride</button>
  <p>W / Up: throttle &nbsp; S / Down: brake &nbsp; A D / Arrows: steer &nbsp; Space: nitro</p>
  <div id="board"></div>
</div></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
"use strict";
/* ---------- Level data (server first, built-in fallback so it never breaks) ---------- */
const FALLBACK=[
 {id:1,name:"Dawn Highway to Snow Pass",length:2400,traffic:.35,zones:[{until:1000,type:"highway"},{until:1800,type:"snow"},{until:2400,type:"highway"}],bike:{name:"Apex R1 (Stock)",top:260,accel:15,handling:11,nitro:1.35,color:"#e11d2e"}},
 {id:2,name:"Mud Run & Frozen Ridge",length:3400,traffic:.5,zones:[{until:800,type:"highway"},{until:1900,type:"mud"},{until:2700,type:"snow"},{until:3400,type:"highway"}],bike:{name:"Apex R1 Tuned (Winglets)",top:300,accel:18,handling:12.5,nitro:1.5,color:"#1d6bff"}},
 {id:3,name:"Blizzard Mud Highway Gauntlet",length:4600,traffic:.65,zones:[{until:900,type:"snow"},{until:1900,type:"mud"},{until:3000,type:"highway"},{until:3800,type:"snow"},{until:4600,type:"mud"}],bike:{name:"Apex R1 Hyper (Carbon Wing)",top:345,accel:22,handling:14,nitro:1.7,color:"#f5b400"}}];
let LEVELS=FALLBACK, unlocked=1, sel=1;
try{unlocked=Math.min(3,+localStorage.getItem("sbr_unlocked")||1)}catch(e){}
const $=id=>document.getElementById(id);

/* Zone physics + look */
const ZONE={
 highway:{label:"Highway",grip:1,top:1,drag:.02,ground:0x3d4a3a,fog:0xaec9e6,sky:0x8fb8e8,road:"#2b2d31"},
 snow:{label:"Snow",grip:.38,top:.82,drag:.035,ground:0xf2f7fb,fog:0xdfe8f0,sky:0xcfd9e3,road:"#aeb6bd"},
 mud:{label:"Mud road",grip:.5,top:.7,drag:.06,ground:0x5a3f25,fog:0xb8a58b,sky:0xa79a88,road:"#6b4a2a"}};

/* ---------- Three.js setup ---------- */
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:"high-performance"});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.75));
renderer.setSize(innerWidth,innerHeight);
document.body.prepend(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(65,innerWidth/innerHeight,.1,700);
scene.add(new THREE.HemisphereLight(0xffffff,0x556070,.95));
const sun=new THREE.DirectionalLight(0xffffff,.8);sun.position.set(30,60,20);scene.add(sun);
addEventListener("resize",()=>{renderer.setSize(innerWidth,innerHeight);camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix()});

/* Road textures (canvas, cheap) */
function roadTex(type){
 const c=document.createElement("canvas");c.width=128;c.height=256;const g=c.getContext("2d");
 g.fillStyle=ZONE[type].road;g.fillRect(0,0,128,256);
 for(let i=0;i<500;i++){g.fillStyle=`rgba(${type=="mud"?"30,15,0":"255,255,255"},${Math.random()*.08})`;g.fillRect(Math.random()*128,Math.random()*256,2+Math.random()*5,2+Math.random()*5)}
 if(type=="highway"){g.fillStyle="#f2f2f2";g.fillRect(2,0,4,256);g.fillRect(122,0,4,256);g.fillStyle="#f5c400";for(const x of[42,84])g.fillRect(x-2,20,4,90),g.fillRect(x-2,150,4,90)}
 else{g.fillStyle=type=="snow"?"rgba(60,70,80,.35)":"rgba(20,10,0,.4)";g.fillRect(30,0,14,256);g.fillRect(84,0,14,256)}
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(1,100/32);t.anisotropy=4;return t}
const ROADMAT={},GROUNDMAT={};
for(const k in ZONE){ROADMAT[k]=new THREE.MeshLambertMaterial({map:roadTex(k)});GROUNDMAT[k]=new THREE.MeshLambertMaterial({color:ZONE[k].ground})}

/* ---------- Bike (procedural superbike + rider). Blender .glb overrides if present ---------- */
const M=(c,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:.45,metalness:.5},o));
function box(w,h,d,m,x,y,z,rx){const b=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);b.position.set(x,y,z);if(rx)b.rotation.x=rx;return b}
function cyl(r,h,m,x,y,z,rx,rz){const b=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h,12),m);b.position.set(x,y,z);b.rotation.x=rx||0;b.rotation.z=rz||0;return b}
function buildBike(level,color){
 const g=new THREE.Group(),body=M(color),dark=M(0x15181c,{metalness:.7}),tire=M(0x0a0a0a,{roughness:.9,metalness:0}),rim=M(0xc9ced4,{metalness:.9});
 const wheels=[];
 for(const z of[-.78,.78]){const w=new THREE.Group();
  w.add(new THREE.Mesh(new THREE.TorusGeometry(.33,.11,10,22).rotateY(Math.PI/2),tire));
  w.add(new THREE.Mesh(new THREE.CylinderGeometry(.24,.24,.1,16).rotateZ(Math.PI/2),rim));
  w.position.set(0,.44,z);g.add(w);wheels.push(w)}
 g.add(box(.34,.34,1.3,dark,0,.72,.05));            // frame/engine
 g.add(box(.42,.3,.55,body,0,1.0,-.12));            // tank
 g.add(box(.46,.52,.34,body,0,.88,-.62,-.5));       // fairing
 g.add(box(.3,.12,.55,body,0,.98,.55,.15));         // tail
 g.add(cyl(.035,.9,dark,-.14,.78,-.78,.35));g.add(cyl(.035,.9,dark,.14,.78,-.78,.35)); // forks
 g.add(box(.7,.04,.04,dark,0,1.15,-.66));           // bars
 g.add(cyl(.06,.7,M(0x888888,{metalness:1}),.2,.55,.75,Math.PI/2));  // exhaust
 // rider (leather suit, helmet, gloves, boots)
 const suit=M(0x16191f,{roughness:.6,metalness:.1}),stripe=M(color,{roughness:.6,metalness:.1}),skin=M(0xd9a27a,{metalness:0,roughness:.8});
 g.add(box(.42,.6,.26,suit,0,1.38,.1,.85));
 g.add(box(.44,.14,.28,stripe,0,1.45,.0,.85));
 const head=new THREE.Mesh(new THREE.SphereGeometry(.2,16,12),M(0xf2f2f2,{metalness:.2}));head.position.set(0,1.68,-.22);g.add(head);
 g.add(box(.26,.1,.1,M(0x111111,{metalness:.9}),0,1.68,-.4));           // visor
 for(const s of[-1,1]){
  g.add(box(.12,.12,.56,suit,s*.27,1.3,-.28,.35));                      // arms
  g.add(box(.09,.09,.09,skin,s*.3,1.17,-.56));                          // hands
  g.add(box(.16,.16,.62,suit,s*.2,.98,.18,-.2));                        // thighs
  g.add(box(.14,.5,.14,suit,s*.22,.66,.3,.1));                          // shins
  g.add(box(.14,.1,.3,dark,s*.22,.42,.2));}                              // boots
 if(level>=2){for(const s of[-1,1])g.add(box(.5,.03,.18,M(0x111111),s*.42,.9,-.62))}     // winglets
 if(level>=3){g.add(box(.9,.04,.28,M(0x0b0b0b,{metalness:.2}),0,1.2,.95));g.add(box(.04,.3,.04,dark,0,1.05,.9));
  const gl=new THREE.Mesh(new THREE.SphereGeometry(.07,8,8),new THREE.MeshBasicMaterial({color:0xff6a00}));gl.position.set(.2,.55,1.12);g.add(gl);g.userData.glow=gl}
 g.userData.wheels=wheels;return g}

let bikeG=null,bikeModelTried={};
const loader=THREE.GLTFLoader?new THREE.GLTFLoader():null;
function loadBlenderModel(level,onDone){ // optional: static/models/bike1.glb ... exported from Blender, facing -Z
 if(!loader||bikeModelTried[level]===false)return;
 loader.load(`/static/models/bike${level}.glb`,gl=>{bikeModelTried[level]=true;onDone(gl.scene)},undefined,()=>{bikeModelTried[level]=false});
}

/* ---------- World ---------- */
const SCENERY=false; // no trees, rocks or poles
const ROAD_OBSTACLES=false; // clear road: no blocks or cars on the track
let world=null,obstacles=[],L=null,snowPts=null;
function disposeWorld(){if(world){scene.remove(world);world.traverse(o=>{if(o.geometry&&!o.userData.shared)o.geometry.dispose()})}world=null}
function zoneAt(d){for(const z of L.zones)if(d<=z.until)return z.type;return L.zones[L.zones.length-1].type}
function rnd(a,b){return a+Math.random()*(b-a)}
function buildWorld(){
 disposeWorld();obstacles=[];world=new THREE.Group();scene.add(world);
 const SEG=100,n=Math.ceil(L.length/SEG)+3,RW=14;
 const roadG=new THREE.PlaneGeometry(RW,SEG).rotateX(-Math.PI/2),gndG=new THREE.PlaneGeometry(500,SEG).rotateX(-Math.PI/2);
 const trees=[],poles=[],rocks=[];
 for(let i=0;i<n;i++){
  const z0=-i*SEG,zc=z0-SEG/2,t=zoneAt(Math.min(-zc,L.length));
  const r=new THREE.Mesh(roadG,ROADMAT[t]);r.position.set(0,.02,zc);r.userData.shared=1;world.add(r);
  const gd=new THREE.Mesh(gndG,GROUNDMAT[t]);gd.position.set(0,0,zc);gd.userData.shared=1;world.add(gd);
  for(let k=0;k<7;k++){const z=z0-k*14-rnd(0,8);for(const s of[-1,1]){const x=s*rnd(10,40);
   if(t=="snow")trees.push([x,z,rnd(.8,1.6)]);else if(t=="mud")rocks.push([x,z,rnd(.6,1.8)]);else if(k%2==0)poles.push([s*9,z,1])}}
  if(ROAD_OBSTACLES&&i>0&&i<n-3)for(let k=0;k<Math.round(SEG/22*L.traffic);k++){ // obstacles (disabled: clear road)
   const z=z0-rnd(8,SEG-8),x=rnd(-5.4,5.4),car=Math.random()<.6,w=car?1.9:1.1,d=car?4:1.1,h=car?1.3:.8;
   const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),new THREE.MeshLambertMaterial({color:car?new THREE.Color().setHSL(Math.random(),.6,.45):0xff7a00}));
   m.position.set(x,h/2,z);world.add(m);obstacles.push({m,x,z,w,d,hit:false,car});
   if(car)m.add(box(w*.8,.45,d*.45,new THREE.MeshLambertMaterial({color:0x222a33}),0,h*.7,0));}
 }
 const inst=(geo,mat,arr,fn)=>{if(!arr.length)return;const im=new THREE.InstancedMesh(geo,mat,arr.length),m4=new THREE.Matrix4();
  arr.forEach((a,i)=>{fn(m4,a);im.setMatrixAt(i,m4)});world.add(im)};
 if(SCENERY)inst(new THREE.ConeGeometry(2,7,7).translate(0,3.5,0),new THREE.MeshLambertMaterial({color:0x2f5d3f}),trees,(m,a)=>m.makeScale(a[2],a[2],a[2]).setPosition(a[0],0,a[1]));
 if(SCENERY)inst(new THREE.CylinderGeometry(.12,.15,8,6).translate(0,4,0),new THREE.MeshLambertMaterial({color:0x888e96}),poles,(m,a)=>m.makeTranslation(a[0],0,a[1]));
 if(SCENERY)inst(new THREE.DodecahedronGeometry(1,0).translate(0,.5,0),new THREE.MeshLambertMaterial({color:0x6f6558}),rocks,(m,a)=>m.makeScale(a[2],a[2]*.8,a[2]).setPosition(a[0],0,a[1]));
 // finish: flat line on the road (nothing standing)
 const fl=new THREE.Mesh(new THREE.PlaneGeometry(14,2).rotateX(-Math.PI/2),new THREE.MeshBasicMaterial({color:0xffffff}));
 fl.position.set(0,.05,-L.length);world.add(fl);
 // snow particles
 const N=900,p=new Float32Array(N*3);for(let i=0;i<N*3;i+=3){p[i]=rnd(-40,40);p[i+1]=rnd(0,30);p[i+2]=rnd(-50,10)}
 const pg=new THREE.BufferGeometry();pg.setAttribute("position",new THREE.BufferAttribute(p,3));
 if(snowPts)scene.remove(snowPts);snowPts=new THREE.Points(pg,new THREE.PointsMaterial({color:0xffffff,size:.25,transparent:true,opacity:.9}));
 snowPts.frustumCulled=false;scene.add(snowPts);
}

/* ---------- Game state ---------- */
const S={on:false,fin:false,x:0,z:0,vx:0,sp:0,nitro:100,t:0,hitT:0,zone:"highway",curZone:null,rot:0};
const K={};addEventListener("keydown",e=>{K[e.code]=1;if(e.code=="Space")e.preventDefault()});addEventListener("keyup",e=>K[e.code]=0);
let fogCol=new THREE.Color(),skyCol=new THREE.Color(),tFog=new THREE.Color(),tSky=new THREE.Color();
scene.fog=new THREE.Fog(0xaec9e6,40,300);scene.background=skyCol;

function startLevel(id){
 L=LEVELS.find(l=>l.id==id);buildWorld();
 if(bikeG)scene.remove(bikeG);bikeG=buildBike(L.id,L.bike.color);scene.add(bikeG);
 loadBlenderModel(L.id,model=>{const keep=bikeG;if(S.lvlId!==L.id)return;scene.remove(keep);bikeG=new THREE.Group();bikeG.add(model);bikeG.userData.wheels=[];scene.add(bikeG)});
 Object.assign(S,{on:true,fin:false,x:0,z:0,vx:0,sp:0,nitro:100,t:0,hitT:0,lvlId:L.id});
 $("lvl").textContent=`Level ${L.id}: ${L.name}  |  ${L.bike.name}`;
 $("menu").style.display="none";$("hud").style.display="block";
 let c=3;say("3");const iv=setInterval(()=>{c--;say(c>0?c:"GO!");if(c<0){clearInterval(iv);say("")}},700);
 S.on=false;setTimeout(()=>{S.on=true},2100);
}
function say(t){const m=$("msg");m.textContent=t;m.style.opacity=t?1:0}

function update(dt){
 const zt=zoneAt(Math.min(-S.z,L.length)),Z=ZONE[zt];
 if(zt!==S.curZone){S.curZone=zt;$("zone").textContent=Z.label;$("zone").style.color=zt=="snow"?"#9fd8ff":zt=="mud"?"#d9a15c":"#eef3f7";tFog.set(Z.fog);tSky.set(Z.sky)}
 skyCol.lerp(tSky,dt*1.5);scene.fog.color.copy(skyCol);scene.fog.near=zt=="snow"?15:40;scene.fog.far=zt=="snow"?160:300;
 if(snowPts)snowPts.visible=zt=="snow";
 if(!S.on||S.fin){return}
 S.t+=dt;const B=L.bike,off=Math.abs(S.x)>7.4;
 const thr=K.KeyW||K.ArrowUp,brk=K.KeyS||K.ArrowDown,nit=K.Space&&S.nitro>0&&thr;
 const steer=(K.KeyD||K.ArrowRight?1:0)-(K.KeyA||K.ArrowLeft?1:0);
 let top=B.top/3.6*Z.top*(off?.45:1);if(nit){top*=B.nitro;S.nitro=Math.max(0,S.nitro-28*dt)}else S.nitro=Math.min(100,S.nitro+4*dt);
 if(thr)S.sp+=B.accel*(nit?1.6:1)*(zt=="highway"?1:.75)*dt;
 if(brk)S.sp-=38*dt;
 S.sp-=S.sp*Z.drag*dt+(off?10*dt:0);
 if(S.sp>top)S.sp-=(S.sp-top)*2.5*dt;
 S.sp=Math.max(0,S.sp);
 const sf=Math.min(1,.35+S.sp/25);                       // steering works with speed
 const target=steer*B.handling*sf*(1.1-Math.min(.5,S.sp/180));
 S.vx+=(target-S.vx)*Math.min(1,Z.grip*7*dt);            // low grip on snow/mud = slide
 S.x=Math.max(-28,Math.min(28,S.x+S.vx*dt));S.z-=S.sp*dt;
 // collisions
 S.hitT=Math.max(0,S.hitT-dt);
 for(const o of obstacles){if(o.hit||Math.abs(o.z-S.z)>4)continue;
  if(Math.abs(o.z-S.z)<o.d/2+1&&Math.abs(o.x-S.x)<o.w/2+.4){o.hit=true;o.m.visible=false;S.sp*=.3;S.hitT=.6;S.vx+=(S.x>o.x?1:-1)*3;say("CRASH!");setTimeout(()=>{if(S.on)say("")},500)}}
 // finish
 if(-S.z>=L.length&&!S.fin){S.fin=true;finish()}
 // HUD
 $("spd").firstChild.nodeValue=Math.round(S.sp*3.6);$("tm").textContent=S.t.toFixed(1)+"s";
 $("prog").firstChild.style.width=Math.min(100,-S.z/L.length*100)+"%";$("nit").firstChild.style.width=S.nitro+"%";
}

function render(dt){
 if(!bikeG)return;
 bikeG.position.set(S.x,0,S.z);
 bikeG.rotation.z=-S.vx*.045;bikeG.rotation.y=-S.vx*.02;
 bikeG.position.y=S.hitT>0?Math.random()*.1:0;
 for(const w of bikeG.userData.wheels||[])w.rotation.x-=S.sp*dt/.38;
 if(bikeG.userData.glow)bikeG.userData.glow.scale.setScalar(1+(S.sp>1?Math.random()*2:0)+(K.Space?3:0));
 const shake=Math.abs(S.x)>7.4?(Math.random()-.5)*.08:0;
 camera.position.set(S.x*.7,3+shake,S.z+7.6);camera.lookAt(S.x*.8,1.1,S.z-9);
 camera.fov=65+Math.min(22,S.sp*.12)+(K.Space&&S.nitro>0?6:0);camera.updateProjectionMatrix();
 if(snowPts&&snowPts.visible){const p=snowPts.geometry.attributes.position.array;
  for(let i=0;i<p.length;i+=3){p[i+1]-=dt*(6+Math.random());p[i]+=dt*1.5;if(p[i+1]<0){p[i+1]=30;p[i]=rnd(-40,40)}}
  snowPts.position.set(S.x,0,S.z-20);snowPts.geometry.attributes.position.needsUpdate=true}
}

/* ---------- Server API (fast, failure-safe) ---------- */
async function api(url,opt){try{const r=await fetch(url,opt);if(!r.ok)throw 0;return await r.json()}catch(e){return null}}
async function finish(){
 say("FINISH!");const time=S.t;let best="";
 const html=`<h1>Level ${L.id} <span>complete</span></h1><p>Time: <b>${time.toFixed(2)}s</b></p>
 <input id="name" maxlength="14" placeholder="Your name" value="${localStorage.getItem("sbr_name")||""}">
 <button id="again">Save score ${L.id<3?"& unlock next level":"& finish"}</button><div id="board"></div>`;
 setTimeout(()=>{$("hud").style.display="none";$("mbox").innerHTML=html;$("menu").style.display="flex";
  $("again").onclick=async()=>{const nm=$("name").value.trim()||"Rider";try{localStorage.setItem("sbr_name",nm)}catch(e){}
   $("again").disabled=true;const r=await api("/api/score",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({level:L.id,time,name:nm})});
   if(L.id<3){unlocked=Math.max(unlocked,L.id+1);sel=L.id+1;try{localStorage.setItem("sbr_unlocked",unlocked)}catch(e){}}
   $("board").innerHTML=r?`Rank #${r.rank}<br>`+r.top.map((s,i)=>`${i+1}. ${s.name} - ${s.time}s`).join("<br>"):"Score server offline - progress saved locally.";
   $("again").textContent="Back to menu";$("again").disabled=false;$("again").onclick=()=>location.reload();};},1500);
}

/* ---------- Menu ---------- */
function drawMenu(){
 $("lv").innerHTML=LEVELS.map(l=>`<button data-l="${l.id}" class="${l.id==sel?"on":""}" ${l.id>unlocked?"disabled":""}>Level ${l.id}</button>`).join("");
 document.querySelectorAll("#lv button").forEach(b=>b.onclick=()=>{sel=+b.dataset.l;drawMenu()});
 const l=LEVELS.find(x=>x.id==sel);
 $("binfo").textContent=`${l.name} - ${l.length}m. Bike: ${l.bike.name}, ${l.bike.top} km/h top speed.`;
 api("/api/leaderboard/"+sel).then(b=>{$("board").innerHTML=b&&b.length?"Best times:<br>"+b.map((s,i)=>`${i+1}. ${s.name} - ${s.time}s`).join("<br>"):""});
}
$("go").onclick=()=>startLevel(sel);
api("/api/levels").then(d=>{if(Array.isArray(d)&&d.length==3)LEVELS=d;L=LEVELS[0];drawMenu()});
L=LEVELS[0];drawMenu();

/* preview bike behind menu */
S.curZone=null;bikeG=buildBike(1,LEVELS[0].color);scene.add(bikeG);camera.position.set(2.5,1.6,3);camera.lookAt(0,.9,0);
let last=performance.now();
(function loop(now){requestAnimationFrame(loop);const dt=Math.min(.05,(now-last)/1000);last=now;
 if(!L||!world){bikeG.rotation.y+=dt*.6;renderer.render(scene,camera);return}
 update(dt);render(dt);renderer.render(scene,camera)})(last);
</script></body></html>
'''

try:
    with open(SCORE_FILE) as f:
        SCORES = json.load(f)
except Exception:
    SCORES = {"1": [], "2": [], "3": []}


def save_scores():
    try:
        with open(SCORE_FILE, "w") as f:
            json.dump(SCORES, f)
    except Exception:
        pass


@app.after_request
def headers(r):
    if request.path.startswith("/static/"):
        r.headers["Cache-Control"] = "public, max-age=3600"
    elif request.path.startswith("/api/levels"):
        r.headers["Cache-Control"] = "public, max-age=600"
    else:
        r.headers["Cache-Control"] = "no-cache"
    return r


@app.route("/")
def index():
    return Response(PAGE, mimetype="text/html")


@app.route("/api/levels")
def levels():
    return jsonify(LEVELS)


@app.route("/api/leaderboard/<int:lvl>")
def leaderboard(lvl):
    return jsonify(SCORES.get(str(lvl), [])[:5])


@app.route("/api/score", methods=["POST"])
def score():
    d = request.get_json(silent=True) or {}
    try:
        lvl = int(d.get("level", 1))
        t = round(float(d.get("time", 0)), 2)
        name = str(d.get("name", "Rider"))[:14].strip() or "Rider"
        if lvl not in (1, 2, 3) or not (5 < t < 3600):
            return jsonify({"ok": False}), 400
    except Exception:
        return jsonify({"ok": False}), 400
    with lock:
        board = SCORES.setdefault(str(lvl), [])
        board.append({"name": name, "time": t, "at": int(time.time())})
        board.sort(key=lambda s: s["time"])
        del board[20:]
        save_scores()
        rank = next((i + 1 for i, s in enumerate(board) if s["name"] == name and s["time"] == t), None)
    return jsonify({"ok": True, "rank": rank, "top": board[:5]})


if __name__ == "__main__":
    # For production speed:  pip install waitress  ->  waitress-serve --threads=8 app:app
    app.run(host="0.0.0.0", port=5000, threaded=True, debug=False)