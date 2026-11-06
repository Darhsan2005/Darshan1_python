"""
APEX HIGHWAY - 3D Supercar Racing  (single-file edition)
Run:   python game.py
Needs: only Python 3 (no pip installs). The game opens in your browser.
Progress (unlocked levels / best times) is saved in your browser.
"""
import http.server, os, socketserver, sys, threading, urllib.request, webbrowser

PORT = 8000
HERE = os.path.dirname(os.path.abspath(__file__))
THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
THREE_FILE = os.path.join(HERE, "three.min.js")

# Download Three.js once so the game can also run offline next time.
if not os.path.exists(THREE_FILE):
    try:
        print("Downloading Three.js (one time)...")
        urllib.request.urlretrieve(THREE_URL, THREE_FILE)
    except Exception as e:
        print("Could not download Three.js, will use the CDN instead:", e)

HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no,viewport-fit=cover">
<title>Apex Highway – 3D Supercar Racing</title>
<style>
*{box-sizing:border-box;margin:0;user-select:none;-webkit-user-select:none;touch-action:none}
html,body{height:100%;overflow:hidden;background:#000;font-family:'Segoe UI',system-ui,sans-serif;color:#fff}
canvas{display:block}
#hud{position:fixed;inset:0;pointer-events:none;display:none}
.pan{position:absolute;background:rgba(8,12,24,.62);border:1px solid rgba(120,200,255,.25);border-radius:10px;padding:8px 12px;backdrop-filter:blur(4px)}
#board{left:10px;top:10px;min-width:180px;font-size:13px;line-height:1.5}
#board .me{color:#18e0ff;font-weight:700}#board h3{font-size:22px;color:#ffd23c}
#top{left:50%;top:10px;transform:translateX(-50%);text-align:center;width:min(340px,34vw);min-width:200px}
#dist{font-size:15px;font-weight:600}#tm{font-size:13px;opacity:.8}
.bar{height:8px;background:rgba(255,255,255,.14);border-radius:5px;overflow:hidden;margin:4px 0}
.bar i{display:block;height:100%;width:0;background:#18e0ff}
#info{right:10px;top:10px;font-size:13px;display:flex;gap:8px;align-items:center}
button{font:inherit}
#info button{pointer-events:auto;background:#142038;color:#fff;border:1px solid #3a6;border-radius:6px;padding:4px 9px;cursor:pointer}
#bars{left:10px;bottom:10px;width:210px;font-size:11px;letter-spacing:1px}
#gauge{position:absolute;right:14px;bottom:14px;width:150px;height:150px;border-radius:50%;--p:0;background:conic-gradient(from 225deg,#18e0ff calc(var(--p)*270deg),rgba(255,255,255,.14) 0 270deg,transparent 0)}
#gauge::before{content:'';position:absolute;inset:12px;border-radius:50%;background:rgba(6,10,20,.88)}
#gin{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
#sp{font-size:40px;line-height:1}#gin small{opacity:.7;font-size:11px}
#toast{position:absolute;top:22%;width:100%;text-align:center;font-size:30px;font-weight:800;color:#ffd23c;text-shadow:0 2px 8px #000;opacity:0;transition:opacity .25s}
#touch{display:none}.tb{position:absolute;pointer-events:auto;width:74px;height:74px;border-radius:50%;background:rgba(10,20,40,.6);border:2px solid rgba(120,200,255,.5);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700}
.tb.on{background:rgba(24,224,255,.45)}
@media (pointer:coarse){#touch{display:block}#gauge{bottom:200px;transform:scale(.7);transform-origin:bottom right}#bars{bottom:100px;width:170px}}
#big{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;font-size:min(22vw,200px);font-weight:900;color:#fff;text-shadow:0 0 30px #18e0ff;pointer-events:none;z-index:5}
#flash,#nit{position:fixed;inset:0;pointer-events:none;opacity:0;transition:opacity .25s;z-index:4}
#flash{background:radial-gradient(transparent 30%,rgba(255,0,0,.7))}
#nit{background:radial-gradient(ellipse at center,transparent 45%,rgba(0,170,255,.5))}
#scr{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(3,6,14,.3);z-index:10}
#scr.side{justify-content:flex-start;background:linear-gradient(90deg,rgba(3,6,14,.9),transparent 70%)}
.card{padding:26px 34px;max-width:500px;width:92vw;text-align:left}
.card h1{font-size:clamp(28px,6vw,46px);letter-spacing:2px;background:linear-gradient(90deg,#18e0ff,#ffd23c);-webkit-background-clip:text;color:transparent;margin-bottom:6px}
.card p,.sub{opacity:.88;margin:6px 0;line-height:1.5}.card b{color:#ffd23c}
.btn{display:block;width:100%;margin:10px 0 0;padding:13px;font-size:18px;font-weight:700;letter-spacing:1px;color:#001;background:linear-gradient(90deg,#18e0ff,#7af);border:0;border-radius:8px;cursor:pointer}
.btn.alt{background:#1c2a44;color:#fff;border:1px solid #4a7}.btn:hover{filter:brightness(1.15)}
.help{font-size:12.5px;opacity:.75;margin-top:14px;line-height:1.6}
.st{margin:9px 0;font-size:13px}.st span{opacity:.75;letter-spacing:1px}.st em{color:#5f5;font-style:normal;margin-left:6px}
</style></head><body>
<div id="hud">
 <div id="board" class="pan"></div>
 <div id="top" class="pan"><div id="dist"></div><div class="bar"><i id="prog"></i></div><div id="tm"></div></div>
 <div id="info" class="pan"><span id="lvn"></span><button onclick="pause()">❚❚ Pause</button><button onclick="cycleTod()">☀ / ☾</button></div>
 <div id="bars" class="pan">NITRO<div class="bar"><i id="nb"></i></div>DAMAGE<div class="bar"><i id="hb" style="background:#4e4"></i></div></div>
 <div id="gauge"><div id="gin"><b id="sp">0</b><small>KM/H</small></div></div>
 <div id="touch">
  <div class="tb" data-k="left" style="left:14px;bottom:14px">◀</div><div class="tb" data-k="right" style="left:96px;bottom:14px">▶</div>
  <div class="tb" data-k="down" style="right:96px;bottom:14px">BRAKE</div><div class="tb" data-k="up" style="right:14px;bottom:14px">GAS</div>
  <div class="tb" data-k="nitro" style="right:55px;bottom:96px;background:rgba(0,120,255,.5)">NITRO</div>
 </div><div id="toast"></div>
</div>
<div id="big"></div><div id="flash"></div><div id="nit"></div><div id="scr"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
'use strict';
function showErr(m){let d=document.getElementById('err');if(!d){d=document.createElement('div');d.id='err';d.style.cssText='position:fixed;left:8px;bottom:8px;right:8px;max-height:40%;overflow:auto;z-index:99;background:#400;color:#fff;padding:8px;font:12px monospace;white-space:pre-wrap;user-select:text';document.body.appendChild(d)}d.textContent+=m+'\n'}
addEventListener('error',e=>showErr('Error: '+e.message+' (line '+e.lineno+')'));addEventListener('unhandledrejection',e=>showErr('Error: '+(e.reason&&e.reason.message||e.reason)));
const ce=console.error;console.error=(...a)=>{showErr(a.join(' ').slice(0,400));ce.apply(console,a)};
const $=id=>document.getElementById(id),C=h=>new THREE.Color(h),rnd=(a,b)=>a+Math.random()*(b-a),clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const LW=3.6,NL=5,RW=LW*NL,LX=i=>(i-2)*LW,CH=40,NCH=20,BG=(w,h,d)=>new THREE.BoxGeometry(w,h,d);
/* ---------------- level data ---------------- */
const LV=[
{n:'LEVEL 1 – BEGINNER',car:'Taurus Veloce (Lamborghini-style)',style:0,color:0xffc400,max:70,acc:18,brk:40,hnd:9,dist:4000,opp:5,oppSpd:61,traffic:14,obs:0,tod:0,need:3,tr:[16,28],weave:0},
{n:'LEVEL 2 – PROFESSIONAL',car:'Cavallo Rosso (Ferrari-style)',style:1,color:0xd90000,max:82,acc:24,brk:50,hnd:11,dist:6000,opp:6,oppSpd:73,traffic:22,obs:6,tod:.5,need:3,tr:[20,34],weave:.5},
{n:'LEVEL 3 – ULTIMATE RACING',car:'Veyron Noir (Bugatti-style hypercar)',style:2,color:0x1636c8,max:100,acc:32,brk:60,hnd:13,dist:8000,opp:7,oppSpd:91,traffic:30,obs:10,tod:1,need:2,tr:[24,40],weave:1}];
const OPP=[{n:'VIPER',col:0xe8e8e8,s:1,a:.9},{n:'BLAZE',col:0xff6a00,s:.97,a:.6},{n:'GHOST',col:0x20d0b0,s:.94,a:.8},{n:'NOVA',col:0xa020f0,s:.99,a:.4},{n:'RAZOR',col:0x151515,s:1.01,a:1},{n:'COBRA',col:0x22aa44,s:.92,a:.5},{n:'TITAN',col:0xf5d000,s:.96,a:.7}];
const STY=[
{L:4.5,W:1.95,b:[[0,.3],[0,.78],[1.3,.98],[2.9,.8],[4.4,.5],[4.5,.38],[4.4,.3]],c:[[1.4,.95],[2.1,1.22],[2.7,1.18],[3.3,.8]],wing:1,gr:0},
{L:4.6,W:1.95,b:[[0,.32],[0,.8],[1,.95],[2.2,.92],[3.8,.72],[4.6,.5],[4.55,.34]],c:[[1.3,.92],[2,1.25],[2.9,1.25],[3.4,.85]],wing:.6,gr:0},
{L:4.8,W:2.05,b:[[0,.32],[0,.95],[1.2,1.12],[3.2,1.0],[4.6,.68],[4.8,.45],[4.7,.32]],c:[[1.5,1.1],[2.2,1.45],[3,1.42],[3.7,.95]],wing:.3,gr:1}];
/* ---------------- renderer / scene ---------------- */
const R=new THREE.WebGLRenderer({antialias:true});R.setPixelRatio(Math.min(devicePixelRatio,2));R.setSize(innerWidth,innerHeight);
R.shadowMap.enabled=true;R.shadowMap.type=THREE.PCFSoftShadowMap;R.outputEncoding=THREE.sRGBEncoding;R.toneMapping=THREE.ACESFilmicToneMapping;R.toneMappingExposure=1.05;
document.body.prepend(R.domElement);
const S=new THREE.Scene(),cam=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.1,1500);S.fog=new THREE.Fog(0xbfd8ee,90,720);
addEventListener('resize',()=>{R.setSize(innerWidth,innerHeight);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()});
const skyC=document.createElement('canvas');skyC.width=2;skyC.height=256;const skyX=skyC.getContext('2d'),skyT=new THREE.CanvasTexture(skyC);skyT.encoding=THREE.sRGBEncoding;S.background=skyT;
function paintSky(t,b){const g=skyX.createLinearGradient(0,0,0,256);g.addColorStop(0,'#'+t.getHexString());g.addColorStop(.55,'#'+b.getHexString());g.addColorStop(1,'#'+b.getHexString());skyX.fillStyle=g;skyX.fillRect(0,0,2,256);skyT.needsUpdate=true}
const hemi=new THREE.HemisphereLight(0xffffff,0x445566,.6),sun=new THREE.DirectionalLight(0xfff2d8,1.2),glow=new THREE.PointLight(0xffc880,0,70,2);
sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-32,right:32,top:55,bottom:-55,near:1,far:300});sun.shadow.bias=-.0004;sun.shadow.normalBias=.05;sun.shadow.camera.updateProjectionMatrix();
S.add(hemi,sun,sun.target,glow);
const spos=new Float32Array(3600);for(let i=0;i<1200;i++){const a=rnd(0,6.283),e=Math.acos(rnd(.05,1));spos.set([850*Math.sin(e)*Math.cos(a),850*Math.cos(e),850*Math.sin(e)*Math.sin(a)],i*3)}
const sgeo=new THREE.BufferGeometry();sgeo.setAttribute('position',new THREE.BufferAttribute(spos,3));
const stars=new THREE.Points(sgeo,new THREE.PointsMaterial({color:0xffffff,size:2,sizeAttenuation:false,transparent:true,opacity:0,fog:false,depthWrite:false}));S.add(stars);
/* day / night */
const TOD=[{t:0x2a6fd6,b:0xbfe3ff,f:0xbfd8ee,s:1.25,sc:0xfff2d8,h:.65,p:[40,90,30]},{t:0x3a3a86,b:0xff9a5c,f:0xc98a72,s:.85,sc:0xff9a5a,h:.4,p:[60,32,40]},{t:0x02040f,b:0x101d3a,f:0x0b1428,s:.32,sc:0x8fa8ff,h:.22,p:[-40,70,20]}];
const lampMat=new THREE.MeshStandardMaterial({color:0xfff2cc,emissive:0xffd88a,emissiveIntensity:.2}),poleMat=new THREE.MeshStandardMaterial({color:0x666a70,metalness:.6,roughness:.5});
const carMats=[],spots=[];let tod=0,todT=0,sunP=[40,90,30];
function winTex(i){const mk=lit=>{const c=document.createElement('canvas');c.width=128;c.height=256;const x=c.getContext('2d');x.fillStyle=lit?'#000':['#59606b','#7a6f66','#4c5663','#6b7480'][i];x.fillRect(0,0,128,256);
 for(let r=0;r<16;r++)for(let q=0;q<8;q++){const on=((r*13+q*7+i*5)%5)<2;x.fillStyle=lit?(on?'#fff':'#000'):(on?'#ffd98a':'#26364f');x.fillRect(q*16+3,r*16+3,10,10)}
 const t=new THREE.CanvasTexture(c);t.encoding=THREE.sRGBEncoding;return t};return[mk(0),mk(1)]}
const winMat=[0,1,2,3].map(i=>{const[a,b]=winTex(i);return new THREE.MeshStandardMaterial({map:a,emissiveMap:b,emissive:0xffe0a0,emissiveIntensity:0,roughness:.6})});
function setTod(t){tod=t;const i=t<.5?0:1,k=t<.5?t*2:t*2-1,A=TOD[i],B=TOD[i+1],L=(a,b)=>a+(b-a)*k,CL=(a,b)=>C(a).lerp(C(b),k);
 paintSky(CL(A.t,B.t),CL(A.b,B.b));S.fog.color.copy(CL(A.f,B.f));
 sun.intensity=L(A.s,B.s);sun.color.copy(CL(A.sc,B.sc));hemi.intensity=L(A.h,B.h);sunP=A.p.map((v,j)=>L(v,B.p[j]));
 const n=clamp((t-.4)/.6,0,1);lampMat.emissiveIntensity=.15+n*3;winMat.forEach(m=>m.emissiveIntensity=n*1.3);
 stars.material.opacity=clamp((t-.55)*2.5,0,1);glow.intensity=n*1.5;spots.forEach(s=>s.intensity=n*3+.25);carMats.forEach(m=>m.envMapIntensity=1-.85*n)}
function cycleTod(){todT=todT<.25?.5:todT<.75?1:0}
/* ---------------- road, scenery ---------------- */
function roadTex(){const c=document.createElement('canvas');c.width=c.height=512;const x=c.getContext('2d');x.fillStyle='#2a2b30';x.fillRect(0,0,512,512);
 for(let i=0;i<6000;i++){const g=rnd(30,72)|0;x.fillStyle=`rgb(${g},${g},${g+4})`;x.fillRect(rnd(0,512),rnd(0,512),2,2)}
 x.fillStyle='#f2f2f2';for(let i=1;i<NL;i++)x.fillRect(i*512/NL-4,0,8,256);x.fillRect(502,0,10,512);x.fillStyle='#ffc400';x.fillRect(0,0,10,512);
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(1,700/12);t.anisotropy=8;t.encoding=THREE.sRGBEncoding;return t}
const rg=new THREE.Group(),flat=(w,h,col,y)=>{const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshStandardMaterial({color:col,roughness:1}));m.rotation.x=-Math.PI/2;m.position.y=y;m.receiveShadow=true;return m};
const rd=new THREE.Mesh(new THREE.PlaneGeometry(RW,700),new THREE.MeshStandardMaterial({map:roadTex(),roughness:.9}));rd.rotation.x=-Math.PI/2;rd.position.y=.02;rd.receiveShadow=true;
rg.add(rd,flat(700,700,0x3c5a2b,-.05));S.add(rg);
[-1,1].forEach(s=>{const sh=flat(3,700,0x303135,.02);sh.position.x=s*(RW/2+1.5);const br=new THREE.Mesh(BG(.6,.95,700),new THREE.MeshStandardMaterial({color:0xb4b4ac,roughness:.8}));
 br.position.set(s*(RW/2+3.3),.47,0);br.castShadow=br.receiveShadow=true;const st=new THREE.Mesh(BG(.62,.1,700),new THREE.MeshStandardMaterial({color:0xd02828}));st.position.set(s*(RW/2+3.3),.8,0);rg.add(sh,br,st)});
const chunks=[],TG=[new THREE.CylinderGeometry(.25,.35,2.4,6),new THREE.ConeGeometry(2,4.5,8)],BX=BG(1,1,1),trunkM=new THREE.MeshStandardMaterial({color:0x5a3b22}),leafM=[0x1f5a2a,0x2f7a35,0x276b30].map(c=>new THREE.MeshStandardMaterial({color:c,roughness:.9}));
function scatter(g){g.userData.tr.forEach(t=>{t.position.set(t.userData.s*rnd(15,36),0,rnd(-CH/2,CH/2));t.scale.setScalar(rnd(.8,1.5))});
 g.userData.bl.forEach(b=>{const w=rnd(14,26),h=rnd(14,75),d=rnd(14,26);b.scale.set(w,h,d);b.position.set(b.userData.s*(rnd(40,55)+w/2),h/2,rnd(-8,8))})}
for(let i=0;i<NCH;i++){const g=new THREE.Group();g.userData={tr:[],bl:[]};
 for(const s of[-1,1]){const lp=new THREE.Group();lp.position.x=s*(RW/2+3.9);
  const po=new THREE.Mesh(new THREE.CylinderGeometry(.1,.16,9,8),poleMat);po.position.y=4.5;const ar=new THREE.Mesh(BG(2.8,.12,.12),poleMat);ar.position.set(-s*1.4,9,0);
  const la=new THREE.Mesh(BG(.9,.12,.4),lampMat);la.position.set(-s*2.7,8.92,0);lp.add(po,ar,la);g.add(lp);
  for(let k=0;k<3;k++){const t=new THREE.Group(),tr=new THREE.Mesh(TG[0],trunkM),l1=new THREE.Mesh(TG[1],leafM[k]),l2=l1.clone();tr.position.y=1.2;l1.position.y=4;l2.scale.setScalar(.7);l2.position.y=5.8;t.add(tr,l1,l2);t.userData.s=s;g.add(t);g.userData.tr.push(t)}
  const b=new THREE.Mesh(BX,winMat[(Math.random()*4)|0]);b.userData.s=s;g.add(b);g.userData.bl.push(b)}
 scatter(g);g.position.z=CH*4-i*CH;S.add(g);chunks.push(g)}
/* ---------------- cars ---------------- */
function makeCar(si,col,me){
 const s=STY[si],g=new THREE.Group(),L=s.L,W=s.W,bs=.1,M=o=>new THREE.MeshStandardMaterial(o);
 const bm=new THREE.MeshStandardMaterial({color:col,emissive:col,emissiveIntensity:.12,metalness:.3,roughness:.35}),gm=M({color:0x24344a,metalness:.4,roughness:.12}),dk=M({color:0x0b0b0d,roughness:.7}),
 ch=M({color:0xd8dce2,metalness:1,roughness:.15}),hl=M({color:0xffffff,emissive:0xcfe8ff,emissiveIntensity:2.5}),tl=M({color:0x330000,emissive:0xff1010,emissiveIntensity:1.4});carMats.push(bm,gm,ch);
 const ex=(pts,d)=>{const sh=new THREE.Shape();pts.forEach((p,i)=>i?sh.lineTo(p[0],p[1]):sh.moveTo(p[0],p[1]));const dd=d-2*bs,ge=new THREE.ExtrudeGeometry(sh,{depth:dd,bevelEnabled:true,bevelSize:bs,bevelThickness:bs,bevelSegments:3,curveSegments:6});ge.translate(-L/2,0,-dd/2);ge.rotateY(Math.PI/2);return ge};
 const add=(ge,m,x,y,z)=>{const o=new THREE.Mesh(ge,m);o.position.set(x,y,z);g.add(o);return o},top=s.b[1][1];
 add(ex(s.b,W),bm,0,0,0);add(ex(s.c,W*.8),gm,0,0,0);add(BG(W*.96,.1,L*.96),dk,0,.27,0);add(BG(W*.9,.05,.5),dk,0,.28,-L/2-.1);
 if(s.gr){add(BG(.9,.5,.12),ch,0,.55,-L/2-.05);add(BG(.7,.38,.12),dk,0,.55,-L/2-.1)}
 [-1,1].forEach(sx=>{add(BG(.5,.09,.1),hl,sx*W*.32,.46+si*.02,-L/2-.05);add(BG(.25,.1,.15),bm,sx*(W/2+.03),.98,-.9);
  add(new THREE.CylinderGeometry(.07,.07,.2,10),ch,sx*.42,.42,L/2+.05).rotation.x=Math.PI/2;
  if(s.wing)add(BG(.06,.3,.1),dk,sx*W*.3,top+.15,L/2-.2)});
 add(BG(W*.85,.08,.08),tl,0,top-.1,L/2+.08);if(s.wing)add(BG(W*.92,.05,.22+.4*s.wing),bm,0,top+.3,L/2-.25);
 const fm=new THREE.MeshBasicMaterial({color:0xff8a20,transparent:true,opacity:.85}),fl=[-1,1].map(sx=>{const f=add(new THREE.ConeGeometry(.1,1,8).rotateX(Math.PI/2),fm,sx*.42,.42,L/2+.65);f.visible=false;return f});
 const tm=M({color:0x111111,roughness:.85}),rm=M({color:0x2a2d33,metalness:.9,roughness:.3}),sm=M({color:0xdde1e8,metalness:1,roughness:.15}),wheels=[];
 const tg=new THREE.CylinderGeometry(.36,.36,.32,24),rgm=new THREE.CylinderGeometry(.27,.27,.33,20),spg=BG(.35,.04,.52);
 [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(([sx,sz])=>{const w=new THREE.Group(),wr=new THREE.Group(),t=new THREE.Mesh(tg,tm),r=new THREE.Mesh(rgm,rm);t.rotation.z=r.rotation.z=Math.PI/2;wr.add(t,r);
  for(let i=0;i<5;i++){const p=new THREE.Mesh(spg,sm);p.rotation.x=i*Math.PI/5;wr.add(p)}w.add(wr);w.position.set(sx*(W/2-.08),.36,sz*L*.3);g.add(w);wheels.push({w,wr,front:sz<0})});
 if(me)[-1,1].forEach(sx=>{const sl=new THREE.SpotLight(0xdff0ff,0,80,.5,.6,1.2),tg2=new THREE.Object3D();sl.position.set(sx*.6,.6,-L/2);tg2.position.set(sx*.8,0,-40);g.add(tg2,sl);sl.target=tg2;spots.push(sl)});
 g.traverse(o=>{if(o.isMesh)o.castShadow=true});g.userData={tail:tl,fl};return{g,wheels,L,W}}
const TC=[0xb0b4ba,0x2b2e33,0xd9d9d9,0x8c1c1c,0x1f3d6b,0x3c5a40,0xc9a227],mc={},mat=c=>mc[c]||(mc[c]=new THREE.MeshStandardMaterial({color:c,metalness:.4,roughness:.4}));
const glassM=new THREE.MeshStandardMaterial({color:0x10141c,metalness:.9,roughness:.1}),tireM=new THREE.MeshStandardMaterial({color:0x111111}),tailM=new THREE.MeshStandardMaterial({color:0x330000,emissive:0xff1010,emissiveIntensity:1.5}),WGm=new THREE.CylinderGeometry(.38,.38,.28,12);
function makeTraffic(truck){const g=new THREE.Group(),L=truck?9:4.3,W=truck?2.5:1.85,col=TC[(Math.random()*TC.length)|0];
 const add=(ge,m,x,y,z)=>{const o=new THREE.Mesh(ge,m);o.position.set(x,y,z);o.castShadow=true;g.add(o);return o};
 if(truck){add(BG(W,2.3,2.5),mat(col),0,1.6,-L/2+1.25);add(BG(W,2.9,6.3),mat(0xdfe3e8),0,2.15,1.1)}else{add(BG(W,.75,L),mat(col),0,.65,0);add(BG(W*.86,.6,2.2),glassM,0,1.3,.3)}
 [[-1,-1],[1,-1],[-1,1],[1,1]].forEach(([sx,sz])=>{add(WGm,tireM,sx*(W/2-.1),.38,sz*L*.32).rotation.z=Math.PI/2});add(BG(W*.8,.12,.06),tailM,0,truck?.9:.8,L/2+.02);return{g,L,W}}
function makeObs(st){const g=new THREE.Group();let W=1.2,L=1.2;const add=(ge,m,x,y,z)=>{const o=new THREE.Mesh(ge,m);o.position.set(x,y,z);o.castShadow=true;g.add(o)};
 const or=new THREE.MeshStandardMaterial({color:0xff6a00,emissive:0x331400}),wh=new THREE.MeshStandardMaterial({color:0xffffff});
 if(st==1){for(let i=0;i<3;i++)add(new THREE.ConeGeometry(.32,.85,10),or,rnd(-.4,.4),.42,i-1);W=1.6;L=3}
 else if(Math.random()<.5){add(new THREE.CylinderGeometry(.45,.45,1.1,12),new THREE.MeshStandardMaterial({color:0xc01818}),0,.55,0);add(new THREE.CylinderGeometry(.46,.46,.2,12),wh,0,.7,0);W=L=1}
 else{add(BG(3.4,.9,.6),or,0,.45,0);add(BG(3.4,.2,.62),wh,0,.6,0);W=3.4;L=.8}return{g,W,L}}
/* ---------------- game state ---------------- */
let state='menu',lvl=0,c=LV[0],shake=0,cd=0,frame=0,rank=1,prevRank=1,carObj=null,showA=0,prog={unlocked:0,best:{}};
const keys={},P={kind:'p',x:0,tx:0,z:0,v:0,sv:0,w:1.95,l:4.5,hp:100,nitro:100,t:0,cd:0,pt:0},ents=[],cp={x:0,y:3,z:8};
function addEnt(kind,o,x,z,v){o.g.position.set(x,0,z);S.add(o.g);const e={kind,g:o.g,x,tx:x,z,v,w:o.W,l:o.L,cool:rnd(0,2),top:v,acc:5,hnd:3,aggr:.3};ents.push(e);return e}
function clearAt(z,x,s){for(const o of ents){if(o===s||o===P)continue;const dz=Math.abs(o.z-z);if(dz<18&&Math.abs(o.x-x)<2.7)return false;if((s.kind=='o'||o.kind=='o')&&dz<24)return false}return true}
function place(e,a,b){for(let k=0;k<10;k++){const ln=(Math.random()*NL)|0,x=LX(ln),z=P.z-rnd(a,b);if(clearAt(z,x,e)){e.x=e.tx=x;e.z=z;if(e.kind=='t'){e.v=e.top=(rnd(c.tr[0],c.tr[1])-ln*1.2)*(e.truck?.75:1)}return}}e.z=P.z-b-rnd(50,150);e.tx=e.x}
function initLevel(i){lvl=i;c=LV[i];ents.forEach(e=>S.remove(e.g));ents.length=0;carMats.length=0;spots.length=0;if(carObj)S.remove(carObj.g);
 carObj=makeCar(c.style,c.color,true);const ST=STY[c.style];Object.assign(P,{x:0,tx:0,z:0,v:0,sv:0,w:ST.W,l:ST.L,hp:100,nitro:100,t:0,cd:0,g:carObj.g});S.add(carObj.g);ents.push(P);
 const lanes=[1,3,0,4,2,0,4,1,3];
 for(let k=0;k<c.opp;k++){const o=OPP[k],car=makeCar(k%3,o.col),z=k<4?((k*5)%7)-5:-12-(k-4)*10,e=addEnt('a',car,LX(lanes[k]),z,0);
  Object.assign(e,{name:o.n,top:c.oppSpd*rnd(.95,1.03)*o.s,acc:c.acc*rnd(.75,1),hnd:rnd(5,8),aggr:o.a,wr:car.wheels,fin:false})}
 for(let k=0;k<c.traffic;k++){const tk=Math.random()<.12,e=addEnt('t',makeTraffic(tk),0,0,0);e.truck=tk;place(e,50,750)}
 for(let k=0;k<c.obs;k++){const e=addEnt('o',makeObs(c.style),0,0,0);place(e,150,800)}
 todT=c.tod;setTod(tod);rank=prevRank=1;shake=0}
const fmt=t=>`${t/60|0}:${(t%60).toFixed(1).padStart(4,'0')}`,showHud=on=>$('hud').style.display=on?'block':'none';
function scr(h,cls){const s=$('scr');s.className=cls||'';s.innerHTML=h?`<div class="card pan">${h}</div>`:'';s.style.display=h?'flex':'none'}
function toast(t){const e=$('toast');e.textContent=t;e.style.opacity=1;clearTimeout(toast.h);toast.h=setTimeout(()=>e.style.opacity=0,1200)}
/* ---------------- AI ---------------- */
function free(lx,e){for(const g of ents){if(g===e)continue;const m=(e.w+g.w)/2+.3;if(Math.abs(g.x-lx)>m&&Math.abs(g.tx-lx)>m)continue;const dz=g.z-e.z,a=(e.l+g.l)/2+10+Math.max(0,e.v-g.v)*.9,b=(e.l+g.l)/2+7+Math.max(0,g.v-e.v)*.9;if(dz>-a&&dz<b)return false}return true}
function ai(e,dt){let nr=null,ng=1e9;const look=14+e.v*.9;
 for(const f of ents){if(f===e)continue;const dz=e.z-f.z;if(dz<=0)continue;const g=dz-(e.l+f.l)/2;if(g>look||g>=ng||Math.abs(f.x-e.x)>(e.w+f.w)/2+.5)continue;nr=f;ng=g}
 let tv=e.top;if(e.kind=='a'){const d=P.z-e.z;tv*=1-clamp(d-80,0,400)/400*.09+clamp(-d-40,0,300)/300*-.06}
 e.cool-=dt;const nl=Math.round(e.x/LW)+2,go=l=>{if(l>=0&&l<NL&&free(LX(l),e)){e.tx=LX(l);e.cool=rnd(1.5,3);return true}return false};
 if(nr){if(e.cool<=0&&(nr.kind=='o'||nr.v<e.v-1.5||(e.aggr>.8&&nr.v<e.top))){[nl-1,nl+1].sort(()=>Math.random()-.5).some(go)}
  if(ng<8+e.v*.3&&Math.abs(e.tx-e.x)<1)tv=Math.min(tv,nr.v-(ng<4?10:0))}
 else if(e.cool<=0){if(e.kind=='a'&&e.aggr>.7){const d=P.z-e.z;if(d>4&&d<28&&Math.abs(P.x-e.x)>1.8)go(nl+Math.sign(P.x-e.x))}
  else if(Math.random()<dt*(e.kind=='a'?.12*e.aggr:c.weave*.08))go(nl+(Math.random()<.5?-1:1))}
 e.v+=clamp(Math.max(0,tv)-e.v,-45*dt,e.acc*dt);e.x+=clamp(e.tx-e.x,-e.hnd*dt,e.hnd*dt);
 for(const f of ents){if(f===e)continue;if(Math.abs(f.x-e.x)<(e.w+f.w)/2*.9&&Math.abs(f.z-e.z)<(e.l+f.l)/2*.95&&e.z>f.z){e.z=f.z+(e.l+f.l)/2*.95;e.v=Math.min(e.v,f.v)}}}
/* ---------------- collisions / flow ---------------- */
function collide(){for(const e of ents){if(e===P)continue;const ox=(P.w+e.w)/2*.9-Math.abs(P.x-e.x),oz=(P.l+e.l)/2*.95-Math.abs(P.z-e.z);if(ox<=0||oz<=0)continue;
 if(oz<ox*1.5){const s=P.z>e.z?1:-1;P.z+=s*oz;if(s>0)P.v=Math.min(P.v,e.v*.9);else e.v=Math.min(e.v,P.v*.9)}
 else{const s=P.x>e.x?1:-1;P.x+=s*ox*.6;P.sv=s*5;if(e.kind!='o'){e.x-=s*ox*.4;e.tx=e.x}}
 if(P.cd<=0){P.cd=.8;P.hp-=e.kind=='t'?18:e.kind=='o'?12:7;P.v*=.85;shake=.7;$('flash').style.opacity=.7;setTimeout(()=>$('flash').style.opacity=0,130);toast(e.kind=='a'?'CONTACT!':'CRASH!');
  if(P.hp<=0){P.hp=0;end('WRECKED','Your car was destroyed. Keep clear of traffic and obstacles!')}}}}
function end(t,m){state='over';scr(`<h1>${t}</h1><p>${m}</p><p>Distance <b>${Math.floor(-P.z)} m</b> · Position <b>${rank}/${c.opp+1}</b></p><button class="btn" onclick="restartLevel()">↻ RESTART</button><button class="btn alt" onclick="toMenu()">MAIN MENU</button>`)}
function finish(){state='done';const win=rank<=c.need,t=P.t,st=`<p>Position <b>${rank} / ${c.opp+1}</b> · Time <b>${fmt(t)}</b> · Avg <b>${Math.round(c.dist/t*3.6)} km/h</b></p>`;
 if(!win)return end('RACE LOST',`You finished P${rank}. You need the top ${c.need} to advance.`);
 if(lvl<2)prog.unlocked=Math.max(prog.unlocked,lvl+1);const b=prog.best[lvl];if(!b||t<b)prog.best[lvl]=+t.toFixed(2);save();
 scr(lvl<2?`<h1>LEVEL COMPLETE!</h1>${st}<p>🔓 <b>New car unlocked:</b> ${LV[lvl+1].car}<br>Engine, top speed, handling &amp; brakes upgraded.</p><button class="btn" onclick="showcase(${lvl+1})">NEXT LEVEL ▶</button><button class="btn alt" onclick="toMenu()">MAIN MENU</button>`
 :`<h1>🏆 CHAMPION!</h1>${st}<p>You conquered all three levels with the ultimate hypercar.</p><button class="btn" onclick="newGame()">PLAY AGAIN</button><button class="btn alt" onclick="toMenu()">MAIN MENU</button>`)}
function startCount(){scr('');showHud(1);state='count';cd=3.99;for(const k in keys)keys[k]=0}
function restartLevel(){initLevel(lvl);startCount()}
function pause(){if(state=='race'){state='pause';scr(`<h1>PAUSED</h1><button class="btn" onclick="resume()">▶ RESUME</button><button class="btn alt" onclick="restartLevel()">↻ RESTART LEVEL</button><button class="btn alt" onclick="toMenu()">MAIN MENU</button>`)}else if(state=='pause')resume()}
function resume(){scr('');state='race'}
function toMenu(){initLevel(0);todT=tod=0;setTod(0);state='menu';showHud(0);
 const bt=Object.keys(prog.best).map(k=>`L${+k+1}: ${fmt(prog.best[k])}`).join(' · ');
 scr(`<h1>APEX HIGHWAY</h1><p class="sub">3D supercar highway racing · 3 levels · 5+ AI rivals</p><button class="btn" onclick="newGame()">▶ START GAME</button>${prog.unlocked>0?`<button class="btn alt" onclick="showcase(${prog.unlocked})">CONTINUE – LEVEL ${prog.unlocked+1}</button>`:''}
 <div class="help"><b>W / ↑</b> accelerate · <b>S / ↓</b> brake · <b>A D / ← →</b> steer · <b>SPACE</b> nitro · <b>P / Esc</b> pause · <b>N</b> day/night<br>Touch screens show on-screen controls.${bt?`<br>Best times – ${bt}`:''}</div>`)}
function newGame(){showcase(0)}
function showcase(i){initLevel(i);state='show';showHud(0);const p=LV[i-1]||{max:0,acc:0,brk:0,hnd:0},d=(a,b,u,m)=>i?`<em>+${((a-b)*m).toFixed(u)}</em>`:'',
 bar=(l,v,mx,txt,dl)=>`<div class="st"><span>${l}</span> <b>${txt}</b>${dl}<div class="bar"><i style="width:${v/mx*100}%"></i></div></div>`;
 scr(`<p class="sub">${i?'🔓 NEW CAR UNLOCKED':'STARTER CAR'}</p><h1 style="font-size:30px">${c.n}</h1><p><b>${c.car}</b></p>
 ${bar('TOP SPEED',c.max,110,Math.round(c.max*3.6)+' km/h',d(c.max,p.max,0,3.6))}${bar('ACCELERATION',c.acc,35,c.acc,d(c.acc,p.acc,0,1))}${bar('BRAKING',c.brk,65,c.brk,d(c.brk,p.brk,0,1))}${bar('HANDLING',c.hnd,14,c.hnd,d(c.hnd,p.hnd,0,1))}
 <p>Race <b>${c.dist/1000} km</b> vs <b>${c.opp}</b> rivals · finish top <b>${c.need}</b> · ${['sunny day, normal traffic','dusk, heavy traffic + cones','night, weaving traffic + roadblocks'][i]}.</p><button class="btn" onclick="startCount()">START RACE ▶</button>`,'side')}
async function load(){try{prog=JSON.parse(localStorage.getItem('apex'))||prog}catch(e){}}
function save(){try{localStorage.setItem('apex',JSON.stringify(prog))}catch(e){}}
/* ---------------- input ---------------- */
const KM={KeyW:'up',ArrowUp:'up',KeyS:'down',ArrowDown:'down',KeyA:'left',ArrowLeft:'left',KeyD:'right',ArrowRight:'right',Space:'nitro'};
addEventListener('keydown',e=>{if(KM[e.code]){keys[KM[e.code]]=1;e.preventDefault()}if(e.code=='KeyP'||e.code=='Escape')pause();if(e.code=='KeyN')cycleTod()});
addEventListener('keyup',e=>{if(KM[e.code])keys[KM[e.code]]=0});document.addEventListener('visibilitychange',()=>{if(document.hidden&&state=='race')pause()});
document.querySelectorAll('[data-k]').forEach(b=>{const k=b.dataset.k;b.addEventListener('pointerdown',e=>{e.preventDefault();keys[k]=1;b.classList.add('on')});['pointerup','pointercancel','pointerleave'].forEach(t=>b.addEventListener(t,()=>{keys[k]=0;b.classList.remove('on')}))});
/* ---------------- main update ---------------- */
function update(dt){frame++;if(Math.abs(todT-tod)>.002)setTod(tod+clamp(todT-tod,-dt*.35,dt*.35));
 const live=state=='race',run=live||state=='done'||state=='over';let nit=false,acc=0;
 if(state=='count'){cd-=dt;if(cd<=0){state='race';$('big').textContent='GO!';setTimeout(()=>$('big').textContent='',800)}else $('big').textContent=Math.ceil(cd)}
 if(run){nit=live&&keys.nitro&&P.nitro>1&&P.v>8;const mx=c.max*(nit?1.25:1);
  if(live){if(keys.down)acc=-c.brk;else if(keys.up)acc=P.v<mx?c.acc*(nit?2.3:1)*Math.max(.12,1.15-P.v/mx):-15;else acc=-(3+P.v*.025);
   P.v=Math.max(0,P.v+acc*dt);if(P.v>mx)P.v=Math.max(mx,P.v-30*dt);
   if(nit)P.nitro=Math.max(0,P.nitro-28*dt);else if(!keys.nitro)P.nitro=Math.min(100,P.nitro+7*dt);
   const d=(keys.right?1:0)-(keys.left?1:0),hf=c.hnd*(1-.35*P.v/c.max)*clamp(P.v/12,0,1);P.sv+=(d*hf-P.sv)*Math.min(1,dt*9);P.x+=P.sv*dt;
   const lim=RW/2+.9;if(Math.abs(P.x)>lim){P.x=Math.sign(P.x)*lim;P.sv=0;P.v*=1-.6*dt}P.t+=dt}
  else{P.v=Math.max(0,P.v-(state=='over'?30:14)*dt);P.sv*=.9}
  P.z-=P.v*dt;P.tx=P.x;P.cd-=dt;
  for(const e of ents){if(e===P)continue;ai(e,dt);e.z-=e.v*dt;if(e.kind=='a'&&-e.z>=c.dist)e.fin=true;if(e.kind!='a'&&e.z>P.z+40)place(e,320,650);
   if(e.wr)e.wr.forEach(w=>w.wr.rotation.x-=e.v*dt/.36)}
  if(live){collide();const pd=-P.z;rank=1+ents.filter(e=>e.kind=='a'&&-e.z>pd).length;if(rank<prevRank)toast('▲ POSITION '+rank);prevRank=rank;if(pd>=c.dist)finish()}}
 for(const e of ents){if(e===P)continue;e.g.position.set(e.x,0,e.z);e.g.rotation.y=-clamp((e.tx-e.x)*.08,-.12,.12)}
 const g=P.g;g.position.set(P.x,0,P.z);g.rotation.y=-P.sv*.02;g.rotation.z=P.sv*.004;P.pt+=((acc>8?.03:acc<-10?-.04:0)-P.pt)*Math.min(1,dt*6);g.rotation.x=P.pt;
 carObj.wheels.forEach(w=>{w.wr.rotation.x-=P.v*dt/.36;if(w.front)w.w.rotation.y=-P.sv/c.hnd*.4});
 g.userData.tail.emissiveIntensity=keys.down&&run?4:1.4;g.userData.fl.forEach(f=>{f.visible=nit;f.scale.z=rnd(.8,1.4)});$('nit').style.opacity=nit?.9:0;
 /* camera */
 if(state=='menu'||state=='show'){showA+=dt*.45;cam.position.set(P.x+Math.sin(showA)*7.5,1.9+Math.sin(showA*.5)*.4,P.z+Math.cos(showA)*7.5);cam.lookAt(P.x,.8,P.z);cp.x=cam.position.x;cp.y=cam.position.y;cp.z=cam.position.z;cam.fov=45;cam.updateProjectionMatrix()}
 else{cp.x+=(P.x*.8-cp.x)*Math.min(1,dt*6);cp.y+=(3-cp.y)*Math.min(1,dt*4);cp.z+=(P.z+7.5+P.v*.02-cp.z)*Math.min(1,dt*8);
  cam.position.set(cp.x+(shake?rnd(-1,1)*shake*.3:0),cp.y+(shake?rnd(-1,1)*shake*.2:0),cp.z);shake=Math.max(0,shake-dt*2);cam.lookAt(P.x*.9,1.1,P.z-14);
  cam.fov+=(62+P.v/c.max*8+(nit?12:0)-cam.fov)*Math.min(1,dt*3);cam.updateProjectionMatrix()}
 sun.position.set(P.x+sunP[0],sunP[1],P.z+sunP[2]);sun.target.position.set(P.x,0,P.z-8);glow.position.set(P.x,7,P.z-8);stars.position.copy(cam.position);
 rg.position.z=Math.round(P.z/12)*12-150;for(const ch of chunks)if(ch.position.z>P.z+CH*4+10){ch.position.z-=NCH*CH;scatter(ch)}
 /* HUD */
 $('gauge').style.setProperty('--p',clamp(P.v/(c.max*1.25),0,1));
 if(frame%4==0&&$('hud').style.display=='block'){$('sp').textContent=Math.round(P.v*3.6);$('dist').textContent=`${Math.min(c.dist,Math.floor(-P.z))} / ${c.dist} m`;$('prog').style.width=clamp(-P.z/c.dist*100,0,100)+'%';
  $('tm').textContent='⏱ '+fmt(P.t);$('nb').style.width=P.nitro+'%';$('hb').style.width=P.hp+'%';$('lvn').textContent=c.n.split('–')[0];
  const rs=[{n:'YOU',d:-P.z,me:1},...ents.filter(e=>e.kind=='a').map(e=>({n:e.name,d:-e.z,f:e.fin}))].sort((a,b)=>b.d-a.d);
  $('board').innerHTML=`<h3>P${rank}/${c.opp+1}</h3>`+rs.map((r,i)=>`<div class="${r.me?'me':''}">${i+1}. ${r.n} ${r.me?'':(r.f?'🏁':(r.d>=-P.z?'+':'')+Math.round(r.d+P.z)+'m')}</div>`).join('')}}
let last=performance.now();function loop(now){requestAnimationFrame(loop);const dt=Math.min(.05,(now-last)/1000);last=now;try{if(state!='pause')update(dt)}catch(e){if(!loop.e){loop.e=1;showErr('update: '+e.stack)}}R.render(S,cam)}
load().then(()=>{try{toMenu()}catch(e){showErr('init: '+e.stack)}requestAnimationFrame(loop)});
</script></body></html>
'''
if os.path.exists(THREE_FILE):
    HTML = HTML.replace(THREE_URL, "/three.min.js")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            body, ctype = HTML.encode("utf-8"), "text/html; charset=utf-8"
        elif path == "/three.min.js" and os.path.exists(THREE_FILE):
            body, ctype = open(THREE_FILE, "rb").read(), "application/javascript"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    port = PORT
    while True:
        try:
            srv = Server(("127.0.0.1", port), Handler)
            break
        except OSError:
            port += 1
    url = "http://localhost:%d" % port
    print("Apex Highway running at", url, "  (press Ctrl+C to stop)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)