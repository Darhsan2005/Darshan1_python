import json, os, threading
from flask import Flask, Response, request, jsonify, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(BASE, "models")
SCORES_FILE = os.path.join(BASE, "scores.json")
os.makedirs(MODELS, exist_ok=True)

CONFIG = {"levels": [
    {"name": "Highway Sprint", "goal": 3000, "gap": 70, "par": 70,
     "zones": ["highway", "highway", "snow", "highway"],
     "car": {"name": "Apex GT", "color": 0xe10600, "accent": 0xffffff, "w": 1.9, "len": 4.4,
             "wing": 0, "max": 62, "acc": 0.22, "brake": 30, "grip": 0.85}},
    {"name": "Mud & Snow Rally", "goal": 5000, "gap": 55, "par": 90,
     "zones": ["mud", "snow", "mud", "highway"],
     "car": {"name": "Vortex R", "color": 0xffb300, "accent": 0x111111, "w": 2.0, "len": 4.5,
             "wing": 1, "max": 75, "acc": 0.30, "brake": 36, "grip": 0.95}},
    {"name": "Ultimate Mix", "goal": 8000, "gap": 42, "par": 110,
     "zones": ["snow", "mud", "highway", "snow", "mud", "highway"],
     "car": {"name": "Phantom X", "color": 0x15151a, "accent": 0x00e5ff, "w": 2.05, "len": 4.7,
             "wing": 1, "max": 90, "acc": 0.38, "brake": 42, "grip": 1.05}},
]}

# ---------- fast in-memory backend ----------
app = Flask(__name__)
_lock = threading.Lock()
try:
    with open(SCORES_FILE) as f:
        SCORES = json.load(f)
except Exception:
    SCORES = []


def _save():
    try:
        with _lock, open(SCORES_FILE, "w") as f:
            json.dump(SCORES, f)
    except Exception:
        pass


@app.get("/")
def index():
    return Response(PAGE, mimetype="text/html", headers={"Cache-Control": "public, max-age=60"})


@app.get("/models/<path:name>")
def models(name):
    return send_from_directory(MODELS, name, max_age=3600)


@app.post("/api/score")
def post_score():
    d = request.get_json(silent=True) or {}
    try:
        sc = max(0, min(int(d.get("score", 0)), 10_000_000))
    except Exception:
        sc = 0
    name = str(d.get("name", "Driver"))[:16] or "Driver"
    with _lock:
        SCORES.append({"name": name, "score": sc})
        SCORES.sort(key=lambda x: x["score"], reverse=True)
        del SCORES[50:]
        rank = next((i + 1 for i, x in enumerate(SCORES) if x["score"] == sc and x["name"] == name), None)
    threading.Thread(target=_save, daemon=True).start()
    return jsonify(ok=True, rank=rank)


@app.get("/api/scores")
def get_scores():
    return jsonify(SCORES[:10])


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Supercar Rush</title>
<style>
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden;background:#000;font-family:Segoe UI,Arial,sans-serif;color:#fff}
canvas{display:block}
#hud{position:fixed;inset:0;pointer-events:none}
.box{position:absolute;background:rgba(10,14,22,.55);padding:8px 14px;border-radius:10px;font-size:14px;letter-spacing:1px}
#tl{top:12px;left:12px}#tr{top:12px;right:12px;text-align:right}
#sp{bottom:18px;left:50%;transform:translateX(-50%);text-align:center}
#spd{font-size:54px;font-weight:800;line-height:1}
.bar{height:8px;background:rgba(255,255,255,.2);border-radius:4px;overflow:hidden;margin-top:6px;width:200px}
.bar i{display:block;height:100%;width:0}
#pg{background:#2ee6a6}#hp{background:#ff4d4d;width:100%}
#fl{position:fixed;inset:0;background:red;opacity:0;pointer-events:none}
#ov{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;background:rgba(5,8,15,.72);text-align:center;padding:20px}
#ov h1{font-size:46px;margin:0 0 8px;letter-spacing:3px}#ov p{max-width:560px;opacity:.85;line-height:1.5;margin:6px 0}
button{margin-top:16px;padding:12px 34px;font-size:18px;font-weight:700;border:0;border-radius:30px;background:#2ee6a6;color:#032;cursor:pointer}
.st{display:flex;gap:10px;align-items:center;justify-content:center;font-size:13px}.st b{width:80px;text-align:right}.st .bar{width:160px}.st .bar i{background:#4da6ff}
#lb{font-size:13px;opacity:.8;margin-top:10px}
</style></head><body>
<div id="hud">
 <div id="tl" class="box"><div id="lv"></div><div id="cn" style="opacity:.7"></div><div class="bar"><i id="pg"></i></div><div class="bar"><i id="hp"></i></div></div>
 <div id="tr" class="box"><div id="zn"></div><div id="ds" style="opacity:.7"></div></div>
 <div id="sp" class="box"><div id="spd">0</div><div>KM/H</div></div>
</div>
<div id="fl"></div>
<div id="ov"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const CFG=__CFG__;
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>'&#'+c.charCodeAt(0)+';');

/* ---------- renderer ---------- */
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x9fd0ff);scene.fog=new THREE.Fog(0x9fd0ff,60,380);
const renderer=new THREE.WebGLRenderer({antialias:true,powerPreference:'high-performance'});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.5));renderer.setSize(innerWidth,innerHeight);
document.body.prepend(renderer.domElement);
const cam=new THREE.PerspectiveCamera(62,innerWidth/innerHeight,0.5,700);
scene.add(new THREE.HemisphereLight(0xffffff,0x667788,0.95));
const sun=new THREE.DirectionalLight(0xffffff,0.8);sun.position.set(30,60,20);scene.add(sun);
addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()});

/* ---------- environments ---------- */
function mk(kind){
 const c=document.createElement('canvas');c.width=128;c.height=256;const x=c.getContext('2d');
 if(kind==='highway'){
  x.fillStyle='#2b2d31';x.fillRect(0,0,128,256);
  for(let i=0;i<500;i++){x.fillStyle='rgba(255,255,255,.04)';x.fillRect(Math.random()*128,Math.random()*256,2,2)}
  x.fillStyle='#e8e8e8';x.fillRect(3,0,4,256);x.fillRect(121,0,4,256);
  x.fillRect(30,0,4,120);x.fillRect(94,0,4,120);
  x.fillStyle='#ffd24a';x.fillRect(59,0,3,256);x.fillRect(66,0,3,256);
 }else{
  const m=kind==='mud';
  x.fillStyle=m?'#6b4a2b':'#eef3f8';x.fillRect(0,0,128,256);
  for(let i=0;i<900;i++){x.fillStyle=m?(Math.random()<.5?'rgba(30,18,8,.35)':'rgba(140,100,60,.3)'):'rgba(150,170,190,.25)';x.fillRect(Math.random()*128,Math.random()*256,3,3)}
  x.fillStyle=m?'rgba(25,14,6,.55)':'rgba(110,125,140,.5)';x.fillRect(28,0,16,256);x.fillRect(84,0,16,256);
 }
 const t=new THREE.CanvasTexture(c);t.anisotropy=4;return t;
}
const ENV={
 highway:{sky:0x9fd0ff,ground:0x4f8a3f,road:'highway',tree:0x2e5f2e,ts:0.28,grip:1,cap:1,name:'HIGHWAY'},
 snow:{sky:0xcdd9e6,ground:0xf4f8fc,road:'snow',tree:0xdfe9f2,ts:1,grip:0.4,cap:0.86,name:'SNOW'},
 mud:{sky:0xa39881,ground:0x5a4429,road:'mud',tree:0x3b3a1f,ts:0.9,grip:0.62,cap:0.72,name:'MUD ROAD'}
};
const tex={highway:mk('highway'),snow:mk('snow'),mud:mk('mud')};
for(const k in ENV){const e=ENV[k];e.g=new THREE.MeshLambertMaterial({color:e.ground});e.r=new THREE.MeshLambertMaterial({map:tex[e.road]});e.t=new THREE.MeshLambertMaterial({color:e.tree});e.skyC=new THREE.Color(e.sky)}

/* ---------- road ---------- */
const SEG=12,NS=52,segs=[];
const cx=s=>Math.sin(s/180)*26+Math.sin(s/67)*7;
const cd=s=>Math.cos(s/180)*26/180+Math.cos(s/67)*7/67;
const cdd=s=>-Math.sin(s/180)*26/32400-Math.sin(s/67)*7/4489;
const gGeo=new THREE.PlaneGeometry(500,SEG*1.03),rGeo=new THREE.PlaneGeometry(16,SEG*1.06),tGeo=new THREE.ConeGeometry(2,9,6);
let lv=0;
const zoneAt=s=>{const z=CFG.levels[lv].zones;return z[Math.floor(Math.max(0,s)/450)%z.length]};
function mkSeg(){
 const g=new THREE.Group();
 const ground=new THREE.Mesh(gGeo,ENV.highway.g);ground.rotation.x=-Math.PI/2;
 const road=new THREE.Mesh(rGeo,ENV.highway.r);road.rotation.x=-Math.PI/2;road.position.y=0.03;
 g.add(ground,road);
 const t=[0,1].map(()=>{const m=new THREE.Mesh(tGeo,ENV.highway.t);g.add(m);return m});
 scene.add(g);return {g,ground,road,t,idx:0};
}
function setSeg(sg,idx){
 const s=(idx+.5)*SEG,e=ENV[zoneAt(idx*SEG)];
 sg.idx=idx;sg.g.position.set(cx(s),0,-s);sg.g.rotation.y=-Math.atan(cd(s));
 sg.ground.material=e.g;sg.road.material=e.r;sg.ground.position.y=-0.02*(idx&1);
 sg.t.forEach((m,i)=>{m.material=e.t;m.scale.set(e.ts,1,e.ts);m.position.set((i?1:-1)*(11+Math.random()*35),4.5,(Math.random()-.5)*SEG)});
}
for(let i=0;i<NS;i++)segs.push(mkSeg());

/* ---------- snow particles ---------- */
const NP=1800,pp=new Float32Array(NP*3);
for(let i=0;i<NP;i++){pp[i*3]=(Math.random()-.5)*80;pp[i*3+1]=Math.random()*30;pp[i*3+2]=(Math.random()-.5)*80}
const pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(pp,3));
const snowM=new THREE.PointsMaterial({color:0xffffff,size:0.28,transparent:true,opacity:0,depthWrite:false});
const snowP=new THREE.Points(pg,snowM);snowP.frustumCulled=false;snowP.visible=false;scene.add(snowP);

/* ---------- cars ---------- */
function buildCar(c){
 const g=new THREE.Group(),wh=[];
 const M=(col,o)=>new THREE.MeshStandardMaterial(Object.assign({color:col,metalness:.55,roughness:.28},o||{}));
 const body=M(c.color),dark=M(0x0c0c0c,{metalness:.2,roughness:.7}),glass=M(0x1a2a3a,{metalness:.9,roughness:.08}),acc=M(c.accent);
 const add=(geo,m,x,y,z,rx)=>{const o=new THREE.Mesh(geo,m);o.position.set(x,y,z);if(rx)o.rotation.x=rx;g.add(o);return o};
 const W=c.w,L=c.len,B=THREE.BoxGeometry;
 add(new B(W,.42,L),body,0,.5,0);
 add(new B(W*.94,.22,L*.36),body,0,.74,-L*.3,.12);
 add(new B(W*.94,.3,L*.26),body,0,.74,L*.36);
 add(new B(W*.8,.4,L*.34),glass,0,.96,L*.02);
 add(new B(W*.7,.06,L*.2),body,0,1.18,L*.04);
 add(new B(.3,.012,L*.34),acc,0,.86,-L*.3,.12);
 add(new B(W*1.02,.05,.5),dark,0,.28,-L/2);
 add(new B(W*1.02,.08,.35),dark,0,.3,L/2);
 if(c.wing){add(new B(.08,.35,.08),dark,-W*.3,1.0,L/2-.2);add(new B(.08,.35,.08),dark,W*.3,1.0,L/2-.2);add(new B(W*.98,.05,.55),acc,0,1.2,L/2-.2)}
 const hl=new THREE.MeshBasicMaterial({color:0xffffee}),tl=new THREE.MeshBasicMaterial({color:0xff2020});
 add(new B(.4,.1,.05),hl,-W*.32,.62,-L/2);add(new B(.4,.1,.05),hl,W*.32,.62,-L/2);
 add(new B(W*.8,.07,.05),tl,0,.66,L/2);
 const cyl=new THREE.CylinderGeometry(.36,.36,.3,20),rim=new THREE.CylinderGeometry(.22,.22,.31,10);
 [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(p=>{
  const pv=new THREE.Group();pv.position.set(p[0]*W/2,.36,p[1]*L*.32);
  const a=new THREE.Mesh(cyl,dark),b=new THREE.Mesh(rim,acc);a.rotation.z=b.rotation.z=Math.PI/2;
  pv.add(a,b);g.add(pv);wh.push(pv);
 });
 return {g,wh};
}
let carG=null,wheels=[];
function setCar(i){
 if(carG)scene.remove(carG);
 const b=buildCar(CFG.levels[i].car);carG=b.g;wheels=b.wh;scene.add(carG);
 // optional Blender model: /models/car1.glb, car2.glb, car3.glb
 try{
  if(!THREE.GLTFLoader)return;
  const target=carG;
  new THREE.GLTFLoader().load('/models/car'+(i+1)+'.glb',gl=>{
   if(carG!==target)return;
   const m=gl.scene;m.rotation.y=Math.PI;               // if your car drives backwards, remove this line
   const bx=new THREE.Box3().setFromObject(m),sz=bx.getSize(new THREE.Vector3());
   m.scale.setScalar(CFG.levels[i].car.len/Math.max(sz.x,sz.z,.01));
   const b2=new THREE.Box3().setFromObject(m),ct=b2.getCenter(new THREE.Vector3());
   m.position.set(-ct.x,-b2.min.y,-ct.z);
   target.children.forEach(c=>c.visible=false);target.add(m);
  },undefined,()=>{});
 }catch(e){}
}

/* ---------- obstacles ---------- */
const tcG=new THREE.BoxGeometry(1.9,.6,4.2),tcG2=new THREE.BoxGeometry(1.6,.5,2),rockG=new THREE.DodecahedronGeometry(1.4);
const glassM=new THREE.MeshLambertMaterial({color:0x223344}),rockM=new THREE.MeshLambertMaterial({color:0x6b6b70});
const tcCols=[0x2255cc,0xdddddd,0x22aa55,0xcc7a00,0x888888].map(c=>new THREE.MeshLambertMaterial({color:c}));
let obs=[],spawnS=150;
function spawn(s){
 const rock=zoneAt(s)!=='highway'&&Math.random()<.55;
 const o={s,d:(Math.random()-.5)*13,rock,hit:false,v:rock?0:16+Math.random()*10,len:rock?2.6:4.2,w:rock?2.6:1.9};
 const m=new THREE.Group();
 if(rock){const r=new THREE.Mesh(rockG,rockM);r.position.y=.8;r.scale.set(1,.7+Math.random()*.5,1);m.add(r)}
 else{const b=new THREE.Mesh(tcG,tcCols[Math.random()*5|0]);b.position.y=.55;const c=new THREE.Mesh(tcG2,glassM);c.position.set(0,1.05,.3);m.add(b,c)}
 o.m=m;scene.add(m);obs.push(o);
}

/* ---------- game state ---------- */
let mode='menu',S=0,d=0,v=0,vd=0,hp=100,time=0,total=0,flash=0,orb=0;
const k={up:0,dn:0,l:0,r:0};
const map={ArrowUp:'up',KeyW:'up',ArrowDown:'dn',KeyS:'dn',Space:'dn',ArrowLeft:'l',KeyA:'l',ArrowRight:'r',KeyD:'r'};
addEventListener('keydown',e=>{if(map[e.code]){k[map[e.code]]=1;e.preventDefault()}if((e.code==='Enter'||e.code==='Space')&&mode!=='play')act()});
addEventListener('keyup',e=>{if(map[e.code])k[map[e.code]]=0});

function resetWorld(i){
 lv=i;obs.forEach(o=>scene.remove(o.m));obs=[];S=d=v=vd=0;hp=100;time=0;spawnS=150;
 segs.forEach((sg,j)=>setSeg(sg,j-4));
 setCar(i);placeCar(0);
 cam.position.set(cx(0),3,8);
}
function placeCar(dt){
 const yaw=-Math.atan(cd(S))-Math.atan(vd/Math.max(v,8));
 carG.position.set(cx(S)+d,0,-S);carG.rotation.y=yaw;carG.rotation.z=-vd*.006;
 wheels.forEach(w=>w.rotation.x-=v*dt/.36);
 return yaw;
}
function bars(c){
 const row=(n,p)=>`<div class="st"><b>${n}</b><div class="bar"><i style="width:${Math.round(p*100)}%"></i></div></div>`;
 return row('TOP SPEED',c.max/90)+row('ACCEL',c.acc/.4)+row('GRIP',Math.min(1,c.grip))+`<p>${Math.round(c.max*3.6)} km/h</p>`;
}
function show(h){$('ov').innerHTML=h;$('ov').style.display='flex'}
function loadBoard(){
 fetch('/api/scores').then(r=>r.json()).then(a=>{const el=$('lb');if(el)el.innerHTML='<b>TOP DRIVERS</b><br>'+a.slice(0,5).map((x,i)=>`${i+1}. ${esc(x.name)} - ${x.score}`).join('<br>')}).catch(()=>{});
}
function menu(){
 mode='menu';total=0;resetWorld(0);
 show(`<h1>SUPERCAR RUSH</h1><p>3 levels. Snow, mud road and highway. Your supercar is upgraded after every level.</p>
 <p><b>W / UP</b> gas &nbsp; <b>S / DOWN / SPACE</b> brake &nbsp; <b>A D / LEFT RIGHT</b> steer<br>Snow = slippery, Mud = slow, Highway = full grip. Avoid traffic and rocks!</p>
 <button onclick="act()">START (ENTER)</button><div id="lb"></div>`);loadBoard();
}
function act(){
 if(mode==='menu')startLevel(0);
 else if(mode==='clear')startLevel(lv+1);
 else if(mode==='dead')startLevel(lv);
 else if(mode==='win')menu();
}
function startLevel(i){resetWorld(i);mode='play';$('ov').style.display='none'}
function hurt(o){
 hp-=o.rock?14:20;v*=.5;vd+=(d>=o.d?1:-1)*7;flash=.25;
 if(hp<=0){hp=0;mode='dead';show(`<h1>CRASHED</h1><p>Car wrecked on ${esc(CFG.levels[lv].name)}.</p><button onclick="act()">RETRY LEVEL (ENTER)</button>`)}
}
function finish(){
 const L=CFG.levels[lv];
 total+=Math.round(L.goal+hp*20+Math.max(0,L.par-time)*40);
 if(lv>=CFG.levels.length-1){
  mode='win';
  let name='Driver';try{name=(prompt('You won! Enter your name for the leaderboard:','Driver')||'Driver').slice(0,16)}catch(e){}
  fetch('/api/score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,score:total}),keepalive:true})
   .then(r=>r.json()).then(j=>{const el=$('rk');if(el&&j.rank)el.textContent='Leaderboard rank: #'+j.rank}).catch(()=>{});
  show(`<h1>YOU WIN!</h1><p>All 3 levels cleared with the ${esc(L.car.name)}.</p><p style="font-size:26px">SCORE ${total}</p><p id="rk"></p><button onclick="act()">MAIN MENU (ENTER)</button>`);
 }else{
  mode='clear';const nx=CFG.levels[lv+1],p=carG.position.clone(),ry=carG.rotation.y;
  setCar(lv+1);carG.position.copy(p);carG.rotation.y=ry;
  show(`<h1>LEVEL ${lv+1} CLEAR</h1><p>Score so far: ${total}</p><p>CAR UPGRADED: <b>${esc(nx.car.name)}</b> - next: ${esc(nx.name)}</p>${bars(nx.car)}<button onclick="act()">NEXT LEVEL (ENTER)</button>`);
 }
}

/* ---------- physics / step ---------- */
function step(dt){
 time+=dt;
 const L=CFG.levels[lv],C=L.car,E=ENV[zoneAt(S)],off=Math.abs(d)>8.6;
 const g=Math.min(1,E.grip*C.grip*(off?.8:1)),cap=C.max*E.cap*(off?.6:1);
 if(k.up)v+=(cap-v)*C.acc*dt*(v>cap?4:1);else v-=(v*.12+3)*dt;
 if(k.dn)v-=C.brake*dt*(g>.5?1:.6);
 if(v<0)v=0;
 const st=(k.r?1:0)-(k.l?1:0);
 vd+=(st*13*Math.min(1,v/18)-vd)*Math.min(1,g*5*dt);
 vd-=cdd(S)*v*v*(1-g)*dt*.6;
 d+=vd*dt;if(Math.abs(d)>40){d=Math.sign(d)*40;vd=0}
 S+=v*dt;
 while(spawnS<S+420){spawn(spawnS);spawnS+=L.gap*(.6+Math.random()*.8)}
 for(let i=obs.length-1;i>=0;i--){
  const o=obs[i];o.s+=o.v*dt;
  if(o.s<S-40){scene.remove(o.m);obs.splice(i,1);continue}
  o.m.position.set(cx(o.s)+o.d,0,-o.s);o.m.rotation.y=-Math.atan(cd(o.s));
  if(!o.hit&&Math.abs(o.s-S)<o.len/2+2.1&&Math.abs(o.d-d)<o.w/2+1){o.hit=true;hurt(o);if(mode!=='play')break}
 }
 const need=Math.floor(S/SEG)-4;
 while(segs[0].idx<need){const sg=segs.shift();setSeg(sg,segs[segs.length-1].idx+1);segs.push(sg)}
 const yaw=placeCar(dt),fx=-Math.sin(yaw),fz=-Math.cos(yaw),x=cx(S)+d,dist=7+v*.03,a=1-Math.exp(-7*dt);
 cam.position.x+=(x-fx*dist-cam.position.x)*a;
 cam.position.y+=(2.6+v*.01+(off?Math.random()*.06:0)-cam.position.y)*a;
 cam.position.z+=(-S-fz*dist-cam.position.z)*a;
 cam.lookAt(x+fx*12,1.1,-S+fz*12);
 cam.fov=60+(v/C.max)*22;cam.updateProjectionMatrix();
 if(S>=L.goal&&mode==='play')finish();
}
function idle(dt){
 orb+=dt*.5;const p=carG.position;
 cam.position.set(p.x+Math.sin(orb)*7,2.4,p.z+Math.cos(orb)*7);cam.lookAt(p.x,.7,p.z);
}

/* ---------- loop ---------- */
let last=performance.now();
function loop(t){
 requestAnimationFrame(loop);
 const dt=Math.min(.05,(t-last)/1000||.016);last=t;
 if(mode==='play')step(dt);else idle(dt);
 const zn=zoneAt(S),E=ENV[zn],a=1-Math.exp(-2*dt);
 scene.background.lerp(E.skyC,a);scene.fog.color.copy(scene.background);
 snowM.opacity+=((zn==='snow'?.95:0)-snowM.opacity)*a;
 if(snowM.opacity>.02){
  snowP.visible=true;const p=pg.attributes.position.array,cp=cam.position;
  for(let i=0;i<NP;i++){const j=i*3;
   p[j+1]-=7*dt;p[j]+=Math.sin(t*.001+i)*.02;
   if(p[j+1]<0)p[j+1]=30;
   if(p[j]-cp.x>40)p[j]-=80;else if(p[j]-cp.x<-40)p[j]+=80;
   if(p[j+2]-cp.z>40)p[j+2]-=80;else if(p[j+2]-cp.z<-40)p[j+2]+=80;
  }
  pg.attributes.position.needsUpdate=true;
 }else snowP.visible=false;
 const L=CFG.levels[lv];
 $('spd').textContent=Math.round(v*3.6);
 $('lv').textContent='LEVEL '+(lv+1)+' - '+L.name;$('cn').textContent=L.car.name;
 $('zn').textContent=E.name;$('ds').textContent=Math.min(L.goal,Math.round(S))+' / '+L.goal+' m';
 $('pg').style.width=Math.min(100,S/L.goal*100)+'%';$('hp').style.width=hp+'%';
 flash=Math.max(0,flash-dt);$('fl').style.opacity=flash*2.4;
 renderer.render(scene,cam);
}
menu();
requestAnimationFrame(loop);
</script></body></html>
""".replace("__CFG__", json.dumps(CONFIG, separators=(",", ":")))

if __name__ == "__main__":
    try:
        from waitress import serve          # fastest simple option (pip install waitress)
        print("Running on http://localhost:5000 (waitress)")
        serve(app, host="0.0.0.0", port=5000, threads=8)
    except ImportError:
        print("Running on http://localhost:5000 (flask)")
        app.run(host="0.0.0.0", port=5000, threaded=True)