from flask import Flask, render_template_string

app = Flask(__name__)

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SUPERCHARGE 3D | Racing Experience</title>

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{
    background:#050812;color:white;
    font-family:Arial,sans-serif;overflow:hidden
}
#scene{position:fixed;inset:0}
canvas{display:block}
.hud{
    position:fixed;inset:0;pointer-events:none;
    padding:25px;
    display:flex;flex-direction:column;
    justify-content:space-between;
}
.top{
    display:flex;justify-content:space-between;
    align-items:flex-start
}
.logo{
    font-size:12px;letter-spacing:5px;
    color:#55eaff;font-weight:bold
}
h1{
    font-size:clamp(20px,4vw,34px);
    letter-spacing:3px;margin-top:7px
}
.level{
    text-align:right;font-size:12px;
    letter-spacing:2px;color:#65efff;
    line-height:2
}
.panel{
    display:flex;gap:25px;
    background:#06101b99;
    border:1px solid #ffffff20;
    padding:12px 18px;border-radius:10px;
    backdrop-filter:blur(12px);
    width:max-content
}
.label{font-size:9px;color:#9db4c9;letter-spacing:2px}
.value{font-size:23px;font-weight:bold;margin-top:5px}
.bottom{
    display:flex;justify-content:space-between;
    align-items:flex-end
}
.car-name{
    font-size:17px;font-weight:bold;
    letter-spacing:2px
}
.hint{font-size:10px;color:#a9bed1;margin-top:8px;line-height:2}
.nitro{
    width:180px;height:7px;
    background:#26374b;margin-top:8px;
    border-radius:10px;overflow:hidden
}
#nitroBar{height:100%;width:100%;background:#46eaff}
.controls{
    pointer-events:auto;display:flex;gap:7px
}
.controls button,.action{
    border:1px solid #55eaff77;
    color:white;background:#10263bcc;
    padding:12px 16px;border-radius:7px;
    font-weight:bold;cursor:pointer
}
.controls button:active,.action:active{background:#36c9ed}
#overlay{
    position:fixed;inset:0;z-index:5;
    display:flex;align-items:center;
    justify-content:center;
    background:#030814aa;
    backdrop-filter:blur(8px);
    text-align:center;padding:20px
}
.card{
    max-width:530px;width:100%;
    padding:40px 25px;
    background:linear-gradient(145deg,#12243c,#060b17);
    border:1px solid #49dfff77;
    border-radius:18px;
    box-shadow:0 0 60px #00bfff25
}
.tag{color:#5ceaff;letter-spacing:5px;font-size:11px}
.card h2{font-size:clamp(28px,6vw,48px);margin:18px 0}
.card p{color:#a9bfd2;line-height:1.8;font-size:13px}
.action{
    background:#42dff2;color:#03101c;
    margin-top:25px;padding:15px 32px;
    letter-spacing:2px
}
#mobile{
    position:fixed;bottom:100px;left:0;right:0;
    display:none;justify-content:space-between;
    padding:15px;pointer-events:none
}
#mobile button{
    pointer-events:auto;width:65px;height:55px;
    background:#102b46cc;color:white;
    border:1px solid #55eaff;border-radius:10px;
    font-size:22px
}
.hidden{display:none!important}
@media(max-width:650px){
 .hud{padding:12px}
 .panel{gap:12px;padding:9px}
 .value{font-size:17px}
 .controls{display:none}
 #mobile{display:flex}
 .bottom{margin-bottom:100px}
 .hint{font-size:9px}
}
</style>
</head>

<body>
<div id="scene"></div>

<div class="hud">
 <div class="top">
  <div>
   <div class="logo">NEXT GENERATION RACING</div>
   <h1>SUPERCHARGE 3D</h1>
  </div>
  <div class="level">
   <div id="levelText">LEVEL 1 / 3</div>
   <div id="environment">SNOW MOUNTAIN</div>
  </div>
 </div>

 <div class="panel">
  <div>
   <div class="label">SPEED</div>
   <div class="value"><span id="speed">0</span> <small style="font-size:10px">KM/H</small></div>
  </div>
  <div>
   <div class="label">DISTANCE</div>
   <div class="value" id="distance">0</div>
  </div>
  <div>
   <div class="label">SCORE</div>
   <div class="value" id="score">0</div>
  </div>
 </div>

 <div class="bottom">
  <div>
   <div class="car-name" id="carName">SUPERCAR MK-I</div>
   <div class="hint">
    W / ↑ ACCELERATE &nbsp; S / ↓ BRAKE<br>
    A / ← LEFT &nbsp; D / → RIGHT &nbsp; SHIFT NITRO
   </div>
   <div class="nitro"><div id="nitroBar"></div></div>
  </div>
  <div class="controls">
   <button id="leftBtn">◀</button>
   <button id="rightBtn">▶</button>
   <button id="nitroBtn">NITRO</button>
  </div>
 </div>
</div>

<div id="mobile">
 <button id="mLeft">◀</button>
 <button id="mNitro">⚡</button>
 <button id="mRight">▶</button>
</div>

<div id="overlay">
 <div class="card">
  <div class="tag">ULTIMATE DRIVING EXPERIENCE</div>
  <h2 id="overlayTitle">READY TO RACE?</h2>
  <p id="overlayText">
   Drive through snow mountains, muddy roads and
   futuristic highways. Upgrade your supercar
   and conquer all three levels.
  </p>
  <button class="action" id="startBtn">START ENGINE</button>
 </div>
</div>

<script type="importmap">
{
 "imports":{
  "three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
 }
}
</script>

<script type="module">
import * as THREE from 'three';

const sceneElement = document.getElementById('scene');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x91c8ec);
scene.fog = new THREE.Fog(0x91c8ec, 35, 150);

const camera = new THREE.PerspectiveCamera(
 65, innerWidth/innerHeight, 0.1, 500
);
camera.position.set(0,5.5,10);

const renderer = new THREE.WebGLRenderer({
 antialias:true
});
renderer.setSize(innerWidth,innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
sceneElement.appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xcceaff,0x293346,2));

const sun = new THREE.DirectionalLight(0xffffff,3);
sun.position.set(-15,25,10);
sun.castShadow=true;
scene.add(sun);

const mat = (color,roughness=.7,metalness=0)=>
 new THREE.MeshStandardMaterial({color,roughness,metalness});

const roadMat = mat(0x343a45);
const white = mat(0xffffff);
const black = mat(0x080b10,.5);
const glass = new THREE.MeshPhysicalMaterial({
 color:0x10283a,metalness:.7,roughness:.13,
 clearcoat:1,transparent:true,opacity:.9
});

let car, wheels=[];
let obstacles=[];
let scenery=[];
let roadLines=[];
let particles=[];
let running=false;
let level=1;
let distance=0;
let score=0;
let speed=0;
let nitro=100;
let steer=0;
let playerX=0;
let lastTime=0;
let spawnTime=0;
let animationId;
let keys={};
let worldTime=0;

const levels=[
 {
  name:"SNOW MOUNTAIN",
  car:"SUPERCAR MK-I",
  color:0xe8f3ff,
  road:0x667989,
  ground:0xd9efff,
  sky:0x91c8ec,
  fog:0x91c8ec,
  maxSpeed:180,
  power:1
 },
 {
  name:"MUD CHALLENGE",
  car:"SUPERCAR MK-II",
  color:0xff721e,
  road:0x493328,
  ground:0x59402c,
  sky:0xd19b72,
  fog:0xb47b54,
  maxSpeed:260,
  power:1.3
 },
 {
  name:"NEON HIGHWAY",
  car:"SUPERCAR MK-III",
  color:0x17e6ff,
  road:0x202b3c,
  ground:0x101b2d,
  sky:0x080c25,
  fog:0x101b3d,
  maxSpeed:350,
  power:1.7
 }
];

function box(parent,x,y,z,w,h,d,material){
 const mesh=new THREE.Mesh(
  new THREE.BoxGeometry(w,h,d),material
 );
 mesh.position.set(x,y,z);
 mesh.castShadow=true;
 mesh.receiveShadow=true;
 parent.add(mesh);
 return mesh;
}

// Procedurally built supercar.
// Blender GLB models can replace this model later.
function makeCar(color){
 const group=new THREE.Group();
 const paint=new THREE.MeshPhysicalMaterial({
  color,metalness:.75,roughness:.23,
  clearcoat:1,clearcoatRoughness:.15
 });

 box(group,0,.72,0,1.85,.42,3.6,paint);
 box(group,0,1.08,-.35,1.52,.5,1.8,paint);

 const cabin=new THREE.Mesh(
  new THREE.BoxGeometry(1.3,.55,1.65),glass
 );
 cabin.position.set(0,1.4,-.35);
 group.add(cabin);

 // Roof
 box(group,0,1.68,-.35,1.12,.12,.95,black);

 // Spoiler
 box(group,0,1.15,-1.75,1.7,.1,.25,black);
 box(group,-.55,1.02,-1.7,.08,.28,.08,black);
 box(group,.55,1.02,-1.7,.08,.28,.08,black);

 // Front splitter
 box(group,0,.48,1.85,2,.1,.3,black);

 // Headlights
 const lamp=new THREE.MeshStandardMaterial({
  color:0xa8f8ff,emissive:0x54dfff,emissiveIntensity:3
 });
 box(group,-.65,.83,1.83,.35,.12,.06,lamp);
 box(group,.65,.83,1.83,.35,.12,.06,lamp);

 // Wheels
 wheels=[];
 const tireMat=mat(0x090b0e,.8);
 const rimMat=mat(0xb9d5e9,.25,.9);

 for(const x of [-.98,.98]){
  for(const z of [-1.15,1.15]){
   const wheel=new THREE.Group();
   wheel.position.set(x,.52,z);

   const tire=new THREE.Mesh(
    new THREE.CylinderGeometry(.48,.48,.28,24),
    tireMat
   );
   tire.rotation.z=Math.PI/2;
   wheel.add(tire);

   const rim=new THREE.Mesh(
    new THREE.CylinderGeometry(.28,.28,.3,20),
    rimMat
   );
   rim.rotation.z=Math.PI/2;
   wheel.add(rim);

   group.add(wheel);
   wheels.push(wheel);
  }
 }

 // Rear lights
 const rearLight=new THREE.MeshStandardMaterial({
  color:0xff2424,emissive:0xff1010,emissiveIntensity:2
 });
 box(group,-.6,.82,-1.83,.4,.12,.06,rearLight);
 box(group,.6,.82,-1.83,.4,.12,.06,rearLight);

 group.position.set(0,0,3);
 scene.add(group);
 return group;
}

function clearWorld(){
 obstacles.forEach(o=>scene.remove(o));
 scenery.forEach(o=>scene.remove(o));
 roadLines.forEach(o=>scene.remove(o));
 particles.forEach(o=>scene.remove(o));

 obstacles=[];
 scenery=[];
 roadLines=[];
 particles=[];
}

function addMountains(){
 for(let i=0;i<18;i++){
  const h=8+Math.random()*18;
  const m=new THREE.Mesh(
   new THREE.ConeGeometry(6,h,5),
   mat(level===1?0xdcecff:0x514d49)
  );
  m.position.set(
   (Math.random()<.5?-1:1)*(13+Math.random()*22),
   h/2-1,
   -i*13-10
  );
  scene.add(m);
  scenery.push(m);
 }
}

function createEnvironment(){
 clearWorld();

 const config=levels[level-1];

 scene.background=new THREE.Color(config.sky);
 scene.fog=new THREE.Fog(config.fog,35,150);

 const ground=new THREE.Mesh(
  new THREE.PlaneGeometry(500,500),
  mat(config.ground)
 );
 ground.rotation.x=-Math.PI/2;
 ground.position.y=-.15;
 ground.position.z=-100;
 ground.receiveShadow=true;
 scene.add(ground);
 scenery.push(ground);

 const road=new THREE.Mesh(
  new THREE.PlaneGeometry(10,500),
  roadMat
 );
 road.rotation.x=-Math.PI/2;
 road.position.set(0,0,-100);
 scene.add(road);
 scenery.push(road);

 // Road borders
 for(const x of [-5.2,5.2]){
  const border=box(scene,x,.08,-100,.22,.12,500,
    mat(level===3?0x00cfff:0xffffff, .3,.3));
  scenery.push(border);
 }

 // Dashed road markings
 for(let i=0;i<35;i++){
  for(const x of [-1.65,1.65]){
   const line=box(scene,x,.035,-i*14, .09,.04,5,white);
   roadLines.push(line);
  }
 }

 addMountains();

 // Roadside lamps on highway
 if(level===3){
  for(let i=0;i<24;i++){
   for(const side of [-1,1]){
    const z=-i*14;
    const pole=box(scene,side*7,3,z,.13,6,.13,
      mat(0x697d9d));
    const light=new THREE.PointLight(0x26dfff,2,12);
    light.position.set(side*7,5.5,z);
    scene.add(light);
    scenery.push(pole,light);
   }
  }
 }

 // Snow and mud particles
 for(let i=0;i<100;i++){
  const particle=new THREE.Mesh(
   new THREE.SphereGeometry(.035,5,5),
   mat(level===1?0xffffff:0x9a6744)
  );
  particle.position.set(
   (Math.random()-.5)*25,
   Math.random()*12+1,
   -Math.random()*120
  );
  scene.add(particle);
  particles.push(particle);
 }
}

function upgradeCar(){
 if(car) scene.remove(car);
 car=makeCar(levels[level-1].color);
 document.getElementById('carName').textContent=
  levels[level-1].car;
 document.getElementById('environment').textContent=
  levels[level-1].name;
 document.getElementById('levelText').textContent=
  "LEVEL "+level+" / 3";
}

function makeObstacle(){
 const type=level===1?0:level===2?1:2;
 const group=new THREE.Group();

 if(type===0){
  const rock=new THREE.Mesh(
   new THREE.DodecahedronGeometry(.8),
   mat(0x9cb3c5)
  );
  rock.position.y=.7;
  group.add(rock);
 }else if(type===1){
  box(group,0,.55,0,1.5,1.1,1.4,mat(0x765039));
  box(group,0,1.2,0,1.3,.15,1.2,mat(0x3d2a20));
 }else{
  box(group,0,.7,0,1.6,1.4,1.5,mat(0x9a1d32));
  box(group,0,1.48,0,1.4,.12,1.3,mat(0xff5b5b));
 }
 group.position.set(
  [-3.3,0,3.3][Math.floor(Math.random()*3)],
  0,-125
 );
 scene.add(group);
 obstacles.push(group);
}

function resetGame(){
 distance=0;
 score=0;
 speed=0;
 nitro=100;
 playerX=0;
 steer=0;
 spawnTime=0;
 worldTime=0;
 level=1;

 upgradeCar();
 createEnvironment();

 document.getElementById('overlay').classList.add('hidden');
 running=true;
 lastTime=performance.now();

 if(animationId)cancelAnimationFrame(animationId);
 animationId=requestAnimationFrame(loop);
}

function nextLevel(){
 if(level>=3){
  finishGame(true);
  return;
 }
 level++;
 upgradeCar();
 createEnvironment();

 const msg=[
  "LEVEL 1 COMPLETE",
  "LEVEL 2 COMPLETE"
 ];

 document.getElementById('overlayTitle').textContent=
  msg[level-2];
 document.getElementById('overlayText').textContent=
  "Your supercar has been upgraded! Get ready for "+
  levels[level-1].name+".";
 document.getElementById('startBtn').textContent=
  "CONTINUE RACE";
 document.getElementById('overlay').classList.remove('hidden');

 running=false;
}

function finishGame(won=false){
 running=false;
 document.getElementById('overlayTitle').textContent=
  won?"CHAMPION!":"RACE OVER";
 document.getElementById('overlayText').textContent=
  won?"You conquered all three levels! Final score: "+score:
  "You crashed! Your score: "+score+". Try again.";
 document.getElementById('startBtn').textContent=
  "RACE AGAIN";
 document.getElementById('overlay').classList.remove('hidden');
}

function movePlayer(dt){
 let direction=0;
 if(keys.ArrowLeft||keys.KeyA)direction-=1;
 if(keys.ArrowRight||keys.KeyD)direction+=1;

 steer+=(direction-steer)*Math.min(1,dt*9);
 playerX+=steer*8*dt;
 playerX=THREE.MathUtils.clamp(playerX,-3.7,3.7);

 car.position.x=playerX;
 car.rotation.z=-steer*.12;
 car.rotation.y=-steer*.08;

 wheels.forEach(w=>w.rotation.x-=speed*dt*.18);
}

function loop(now){
 if(!running)return;

 const dt=Math.min((now-lastTime)/1000,.04);
 lastTime=now;
 worldTime+=dt;

 const config=levels[level-1];
 const accelerating=keys.ArrowUp||keys.KeyW;
 const braking=keys.ArrowDown||keys.KeyS;
 const usingNitro=keys.ShiftLeft||keys.ShiftRight;

 if(accelerating)speed+=65*dt;
 else speed-=20*dt;

 if(braking)speed-=100*dt;

 if(usingNitro&&nitro>0){
  speed+=100*dt;
  nitro-=25*dt;
 }else{
  nitro=Math.min(100,nitro+8*dt);
 }

 speed=THREE.MathUtils.clamp(
  speed,0,config.maxSpeed*(usingNitro?1.25:1)
 );

 movePlayer(dt);

 const movement=speed*dt*.14;
 distance+=movement;
 score+=Math.floor(movement*10);

 // Environment scrolling
 roadLines.forEach(line=>{
  line.position.z+=movement*3;
  if(line.position.z>10)line.position.z-=490;
 });

 scenery.forEach(obj=>{
  if(obj.geometry && obj.geometry.type==="BoxGeometry"){
   if(obj.position.z>-20 && obj.position.z<0 &&
      obj.geometry.parameters.depth===6){
    // Highway objects stay in place
   }
  }
 });

 obstacles.forEach((obj,i)=>{
  obj.position.z+=movement*3;

  const dx=Math.abs(obj.position.x-playerX);
  if(obj.position.z>1 && obj.position.z<5 && dx<1.3){
   finishGame();
  }

  if(obj.position.z>15){
   scene.remove(obj);
   obstacles.splice(i,1);
  }
 });

 spawnTime+=dt;
 if(spawnTime>Math.max(.65,2-speed/200)){
  makeObstacle();
  spawnTime=0;
 }

 // Weather particles
 particles.forEach(p=>{
  p.position.z+=movement*2+3*dt;
  p.position.x+=Math.sin(worldTime+p.position.z)*.008;
  p.position.y-=dt*(level===1?3:1.5);

  if(p.position.z>8){
   p.position.z=-100-Math.random()*30;
   p.position.y=Math.random()*12+1;
  }
 });

 // Camera follow
 camera.position.x+=(playerX*.3-camera.position.x)*dt*3;
 camera.lookAt(playerX*.2,1,-7);

 document.getElementById('speed').textContent=
  Math.round(speed);
 document.getElementById('distance').textContent=
  Math.floor(distance);
 document.getElementById('score').textContent=score;
 document.getElementById('nitroBar').style.width=nitro+"%";

 // Level completion
 const target=level===1?500:level===2?1100:1800;
 if(distance>=target){
  if(level===3)finishGame(true);
  else nextLevel();
 }

 renderer.render(scene,camera);

 if(running)animationId=requestAnimationFrame(loop);
}

function bindButton(id,key){
 const button=document.getElementById(id);
 button.addEventListener('pointerdown',e=>{
  e.preventDefault();keys[key]=true;
 });
 ['pointerup','pointerleave','pointercancel'].forEach(event=>{
  button.addEventListener(event,()=>keys[key]=false);
 });
}

bindButton('leftBtn','ArrowLeft');
bindButton('rightBtn','ArrowRight');
bindButton('mLeft','ArrowLeft');
bindButton('mRight','ArrowRight');
bindButton('nitroBtn','ShiftLeft');
bindButton('mNitro','ShiftLeft');

window.addEventListener('keydown',e=>{
 keys[e.code]=true;
 if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Space']
 .includes(e.code))e.preventDefault();
});
window.addEventListener('keyup',e=>keys[e.code]=false);
window.addEventListener('blur',()=>keys={});

document.getElementById('startBtn').addEventListener('click',()=>{
 if(level===1 && distance===0){
  resetGame();
 }else if(level<3 && !running){
  document.getElementById('overlay').classList.add('hidden');
  running=true;
  lastTime=performance.now();
  animationId=requestAnimationFrame(loop);
 }else{
  resetGame();
 }
});

function init(){
 upgradeCar();
 createEnvironment();
 renderer.render(scene,camera);
}
init();

window.addEventListener('resize',()=>{
 camera.aspect=innerWidth/innerHeight;
 camera.updateProjectionMatrix();
 renderer.setSize(innerWidth,innerHeight);
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)