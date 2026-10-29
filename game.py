from flask import Flask, jsonify, request, render_template_string

app = Flask(__name__)

# Highest score stored while the Flask server is running
best_score = 0

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>NO INTERNET — Dino Runner</title>

<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --cyan: #79f7ff;
    --white: #f4f7ff;
    --muted: #91a0bd;
}

body {
    min-height: 100vh;
    background: #03050d;
    color: var(--white);
    font-family: "Segoe UI", Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
}

/* Cinematic background */

.background {
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse at 75% 18%,
            rgba(52, 74, 139, .30), transparent 38%),
        radial-gradient(ellipse at 15% 75%,
            rgba(0, 175, 210, .10), transparent 35%),
        linear-gradient(180deg, #060918 0%, #101a34 55%, #03050d 100%);
    z-index: -3;
}

.background::before {
    content: "";
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(1px 1px at 10% 20%, white 99%, transparent),
        radial-gradient(2px 2px at 35% 40%, #8cecff 99%, transparent),
        radial-gradient(1px 1px at 70% 25%, white 99%, transparent),
        radial-gradient(2px 2px at 90% 60%, white 99%, transparent),
        radial-gradient(1px 1px at 50% 10%, white 99%, transparent);
    background-size: 250px 190px;
    opacity: .8;
    animation: stars 15s linear infinite;
}

@keyframes stars {
    from { transform: translateY(0); }
    to   { transform: translateY(-50px); }
}

.moon {
    position: fixed;
    width: 100px;
    height: 100px;
    border-radius: 50%;
    right: 15%;
    top: 12%;
    background: #e8f7ff;
    box-shadow:
        0 0 25px rgba(160, 225, 255, .4),
        0 0 80px rgba(104, 171, 255, .18);
    opacity: .9;
    z-index: -2;
}

.moon::after {
    content: "";
    position: absolute;
    width: 100px;
    height: 100px;
    top: -8px;
    left: 15px;
    background: #101a34;
    border-radius: 50%;
}

/* Main game container */

.game-container {
    width: min(1050px, 94vw);
    position: relative;
    z-index: 1;
}

.topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-icon {
    font-size: 32px;
    filter: drop-shadow(0 0 12px rgba(121,247,255,.4));
}

.brand h1 {
    font-size: 19px;
    font-weight: 800;
    letter-spacing: 3px;
}

.brand p {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 3px;
    margin-top: 5px;
}

.status {
    display: flex;
    align-items: center;
    gap: 9px;
    color: #b9ffd9;
    font-size: 11px;
    letter-spacing: 2px;
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #53ffac;
    box-shadow: 0 0 12px #53ffac;
}

/* Heading */

.heading {
    text-align: center;
    margin-bottom: 22px;
}

.eyebrow {
    color: var(--cyan);
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 5px;
    margin-bottom: 12px;
}

.heading h2 {
    font-size: clamp(28px, 5vw, 52px);
    font-weight: 900;
    letter-spacing: 5px;
    line-height: 1.15;
    text-shadow: 0 0 30px rgba(121,247,255,.15);
}

.heading h2 span {
    color: var(--cyan);
}

.heading p {
    color: #8c9ab5;
    font-size: 12px;
    letter-spacing: 2px;
    margin-top: 12px;
}

/* Game screen */

.game-screen {
    position: relative;
    border: 1px solid rgba(121,247,255,.22);
    border-radius: 15px;
    overflow: hidden;
    background: rgba(5, 10, 26, .75);
    box-shadow:
        0 0 50px rgba(0, 193, 255, .07),
        0 25px 90px rgba(0, 0, 0, .5);
}

.game-screen::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 15px;
    box-shadow: inset 0 0 70px rgba(0, 0, 0, .3);
    pointer-events: none;
    z-index: 2;
}

.hud {
    position: absolute;
    top: 22px;
    left: 25px;
    right: 25px;
    z-index: 3;
    display: flex;
    justify-content: space-between;
    pointer-events: none;
}

.hud-label {
    font-size: 9px;
    letter-spacing: 3px;
    color: #91a0bd;
    margin-bottom: 5px;
}

.hud-value {
    font-size: 25px;
    font-weight: 800;
    color: white;
    font-variant-numeric: tabular-nums;
}

#best {
    color: var(--cyan);
}

canvas {
    display: block;
    width: 100%;
    height: auto;
    aspect-ratio: 1000 / 360;
}

/* Start / game over overlay */

.overlay {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    text-align: center;
    z-index: 4;
    background: rgba(3, 5, 16, .24);
    padding: 20px;
}

.overlay.hidden {
    display: none;
}

.overlay h3 {
    font-size: clamp(22px, 4vw, 36px);
    font-weight: 900;
    letter-spacing: 4px;
    text-shadow: 0 0 25px rgba(121,247,255,.25);
}

.overlay p {
    margin-top: 12px;
    color: #b1bed5;
    font-size: 12px;
    letter-spacing: 1px;
    line-height: 1.8;
}

.primary-btn {
    margin-top: 25px;
    border: 1px solid var(--cyan);
    color: #06111d;
    background: var(--cyan);
    padding: 13px 32px;
    border-radius: 5px;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 3px;
    cursor: pointer;
    transition: .25s;
    box-shadow: 0 0 25px rgba(121,247,255,.17);
}

.primary-btn:hover {
    background: white;
    border-color: white;
    transform: translateY(-2px);
    box-shadow: 0 0 35px rgba(121,247,255,.4);
}

/* Bottom controls */

.bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    margin-top: 22px;
    color: #8e9bb4;
    font-size: 10px;
    letter-spacing: 1.5px;
}

.controls {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.key {
    display: inline-flex;
    min-width: 31px;
    height: 28px;
    padding: 0 8px;
    align-items: center;
    justify-content: center;
    border: 1px solid #35435d;
    background: rgba(255,255,255,.04);
    color: white;
    border-radius: 5px;
    margin-right: 5px;
    font-size: 11px;
}

.bottom-note {
    text-align: right;
    line-height: 1.8;
}

.bottom-note span {
    color: var(--cyan);
}

/* Mobile layout */

@media (max-width: 600px) {
    .topbar {
        margin-bottom: 22px;
    }

    .brand h1 {
        font-size: 14px;
        letter-spacing: 2px;
    }

    .brand p {
        font-size: 8px;
        letter-spacing: 1px;
    }

    .moon {
        width: 65px;
        height: 65px;
    }

    .moon::after {
        width: 65px;
        height: 65px;
    }

    .heading h2 {
        letter-spacing: 3px;
    }

    .bottom {
        align-items: flex-start;
        flex-direction: column;
    }

    .bottom-note {
        text-align: left;
    }

    .hud {
        top: 12px;
        left: 14px;
        right: 14px;
    }

    .hud-value {
        font-size: 19px;
    }
}
</style>
</head>

<body>

<div class="background"></div>
<div class="moon"></div>

<main class="game-container">

    <header class="topbar">
        <div class="brand">
            <div class="brand-icon">🦖</div>
            <div>
                <h1>NEON RUNNER</h1>
                <p>OFFLINE SURVIVAL SYSTEM</p>
            </div>
        </div>

        <div class="status">
            <span class="status-dot"></span>
            SYSTEM READY
        </div>
    </header>

    <section class="heading">
        <div class="eyebrow">THE LAST SURVIVOR</div>
        <h2>RUN BEYOND <span>LIMITS</span></h2>
        <p>ONE DINOSAUR. ENDLESS NIGHT. NO SECOND CHANCES.</p>
    </section>

    <section class="game-screen">

        <div class="hud">
            <div>
                <div class="hud-label">DISTANCE SCORE</div>
                <div class="hud-value" id="score">00000</div>
            </div>

            <div style="text-align:right">
                <div class="hud-label">PERSONAL BEST</div>
                <div class="hud-value" id="best">00000</div>
            </div>
        </div>

        <canvas id="game" width="1000" height="360"></canvas>

        <div class="overlay" id="overlay">
            <h3 id="overlayTitle">THE NIGHT IS YOURS</h3>
            <p id="overlayText">
                The world has gone silent.<br>
                Your survival begins now.
            </p>
            <button class="primary-btn" id="startBtn">
                START RUNNING &nbsp; →
            </button>
        </div>

    </section>

    <footer class="bottom">
        <div class="controls">
            <span><b class="key">SPACE</b> JUMP</span>
            <span><b class="key">↑</b> JUMP</span>
            <span><b class="key">↓</b> DUCK</span>
        </div>

        <div class="bottom-note">
            BUILT FOR THE <span>FEARLESS</span><br>
            SURVIVE AS LONG AS YOU CAN
        </div>
    </footer>

</main>

<script>
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const scoreElement = document.getElementById("score");
const bestElement = document.getElementById("best");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlayTitle");
const overlayText = document.getElementById("overlayText");
const startBtn = document.getElementById("startBtn");

const W = canvas.width;
const H = canvas.height;
const groundY = 290;

let running = false;
let gameOver = false;
let score = 0;
let best = 0;
let speed = 6;
let frame = 0;
let groundOffset = 0;
let spawnTimer = 0;
let lastTime = 0;
let animationId = null;
let ducking = false;

const dino = {
    x: 115,
    y: groundY - 54,
    w: 48,
    h: 54,
    vy: 0,
    jumping: false
};

let obstacles = [];
let particles = [];
let stars = [];
let hills = [];

function random(min, max) {
    return Math.random() * (max - min) + min;
}

function makeStars() {
    stars = [];

    for (let i = 0; i < 85; i++) {
        stars.push({
            x: random(0, W),
            y: random(0, 210),
            r: random(.5, 1.8),
            a: random(.25, 1)
        });
    }
}

function makeHills() {
    hills = [];

    for (let layer = 0; layer < 3; layer++) {
        const points = [];
        const spacing = 100;

        for (let x = -100; x <= W + 100; x += spacing) {
            points.push({
                x,
                y: 175 + layer * 28 + random(-35, 35)
            });
        }

        hills.push({
            points,
            speed: .25 + layer * .25,
            color: [
                "#121e3b",
                "#0b142b",
                "#080e20"
            ][layer]
        });
    }
}

function resetGame() {
    score = 0;
    speed = 6;
    frame = 0;
    spawnTimer = 0;
    groundOffset = 0;

    obstacles = [];
    particles = [];

    dino.y = groundY - dino.h;
    dino.vy = 0;
    dino.jumping = false;

    ducking = false;
    gameOver = false;

    updateHUD();
}

function updateHUD() {
    scoreElement.textContent =
        String(Math.floor(score)).padStart(5, "0");

    bestElement.textContent =
        String(best).padStart(5, "0");
}

async function loadBestScore() {
    try {
        const response = await fetch("/api/best");
        const data = await response.json();

        best = data.best || 0;
        updateHUD();
    } catch (error) {
        console.log("Using local score until the server responds.");
    }
}

async function saveBestScore() {
    try {
        const response = await fetch("/api/score", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                score: Math.floor(score)
            })
        });

        const data = await response.json();

        best = Math.max(best, data.best || 0);
        updateHUD();
    } catch (error) {
        console.log("Score could not be sent to the server.");
    }
}

function startGame() {
    if (running) return;

    resetGame();

    running = true;
    gameOver = false;
    overlay.classList.add("hidden");

    lastTime = performance.now();

    if (animationId !== null) {
        cancelAnimationFrame(animationId);
    }

    animationId = requestAnimationFrame(loop);
}

function endGame() {
    running = false;
    gameOver = true;

    best = Math.max(best, Math.floor(score));
    updateHUD();

    saveBestScore();

    overlayTitle.textContent = "RUN TERMINATED";

    overlayText.innerHTML =
        "Your journey ends here.<br>" +
        "Distance covered: " + Math.floor(score) +
        "<br>Can you survive longer?";

    startBtn.textContent = "RESTART MISSION  ↻";

    overlay.classList.remove("hidden");
}

function jump() {
    if (!running) {
        if (!gameOver) {
            startGame();
        }
        return;
    }

    if (!dino.jumping) {
        dino.vy = -14.5;
        dino.jumping = true;
        createParticles(dino.x + 20, groundY, 9);
    }
}

function createParticles(x, y, amount) {
    for (let i = 0; i < amount; i++) {
        particles.push({
            x,
            y,
            vx: random(-2.5, 2.5),
            vy: random(-3, 0),
            life: random(12, 28),
            size: random(1, 4)
        });
    }
}

/* Draw the cinematic sky */

function drawSky() {
    const sky = ctx.createLinearGradient(0, 0, 0, H);

    sky.addColorStop(0, "#080d20");
    sky.addColorStop(.65, "#111d3a");
    sky.addColorStop(1, "#10182c");

    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    // Stars
    stars.forEach(star => {
        ctx.globalAlpha =
            star.a * (.65 + Math.sin(frame * .03 + star.x) * .3);

        ctx.fillStyle = "#d7f7ff";

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
        ctx.fill();
    });

    ctx.globalAlpha = 1;

    // Distant moon
    const moonGlow = ctx.createRadialGradient(
        785, 95, 4,
        785, 95, 95
    );

    moonGlow.addColorStop(0, "rgba(131,207,255,.15)");
    moonGlow.addColorStop(1, "rgba(131,207,255,0)");

    ctx.fillStyle = moonGlow;
    ctx.fillRect(680, 0, 210, 200);

    ctx.beginPath();
    ctx.arc(785, 95, 30, 0, Math.PI * 2);
    ctx.fillStyle = "#d6e9ff";
    ctx.fill();

    // Moon craters
    ctx.fillStyle = "rgba(95,130,170,.25)";

    ctx.beginPath();
    ctx.arc(775, 88, 5, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(795, 103, 7, 0, Math.PI * 2);
    ctx.fill();

    ctx.beginPath();
    ctx.arc(793, 81, 3, 0, Math.PI * 2);
    ctx.fill();
}

/* Moving mountain silhouettes */

function drawHills(dt) {
    hills.forEach((hill, index) => {
        ctx.fillStyle = hill.color;
        ctx.beginPath();

        ctx.moveTo(0, H);

        hill.points.forEach(point => {
            point.x -= hill.speed * speed * dt;

            if (point.x < -120) {
                point.x = W + random(0, 80);
                point.y = 175 + index * 28 + random(-35, 35);
            }

            ctx.lineTo(point.x, point.y);
        });

        ctx.lineTo(W, H);
        ctx.closePath();
        ctx.fill();
    });
}

/* Ground with glowing neon line */

function drawGround(dt) {
    ctx.fillStyle = "#070c19";
    ctx.fillRect(0, groundY, W, H - groundY);

    ctx.strokeStyle = "rgba(121,247,255,.65)";
    ctx.lineWidth = 2;
    ctx.shadowBlur = 12;
    ctx.shadowColor = "#48dfff";

    ctx.beginPath();
    ctx.moveTo(0, groundY);
    ctx.lineTo(W, groundY);
    ctx.stroke();

    ctx.shadowBlur = 0;

    // Scrolling ground marks
    groundOffset += speed * dt;

    ctx.strokeStyle = "rgba(121,247,255,.17)";
    ctx.lineWidth = 1;

    for (let x = -(groundOffset % 70); x < W; x += 70) {
        ctx.beginPath();
        ctx.moveTo(x, groundY + 19);
        ctx.lineTo(x - 25, groundY + 19);
        ctx.stroke();
    }

    // Ground glow
    const glow = ctx.createLinearGradient(
        0, groundY, 0, groundY + 50
    );

    glow.addColorStop(0, "rgba(30,185,220,.09)");
    glow.addColorStop(1, "rgba(0,0,0,0)");

    ctx.fillStyle = glow;
    ctx.fillRect(0, groundY, W, 50);
}

/* Dinosaur drawing */

function drawDino() {
    const x = dino.x;
    const y = dino.y;
    const h = dino.h;

    const bodyColor = "#b5fbff";

    ctx.save();

    ctx.shadowBlur = 15;
    ctx.shadowColor = "rgba(87,238,255,.5)";
    ctx.fillStyle = bodyColor;

    // Tail
    ctx.beginPath();
    ctx.moveTo(x + 8, y + 31);
    ctx.lineTo(x - 12, y + 39);
    ctx.lineTo(x + 9, y + 43);
    ctx.closePath();
    ctx.fill();

    // Body
    ctx.fillRect(x + 7, y + 21, 29, 23);

    // Head
    ctx.fillRect(x + 23, y + 4, 27, 24);
    ctx.fillRect(x + 37, y + 20, 15, 8);

    // Eye
    ctx.shadowBlur = 0;
    ctx.fillStyle = "#08111f";
    ctx.fillRect(x + 41, y + 10, 4, 5);

    // Mouth
    ctx.fillRect(x + 45, y + 23, 7, 2);

    // Legs
    ctx.fillStyle = bodyColor;

    const runningLeg = running && !dino.jumping
        ? Math.sin(frame * .4) * 5
        : 0;

    ctx.fillRect(x + 11, y + 40, 9, 14 + runningLeg);
    ctx.fillRect(x + 27, y + 40, 9, 14 - runningLeg);

    // Feet
    ctx.fillRect(x + 7, y + 50 + runningLeg, 14, 4);
    ctx.fillRect(x + 25, y + 50 - runningLeg, 14, 4);

    // Chest detail
    ctx.strokeStyle = "rgba(5,45,60,.5)";
    ctx.lineWidth = 2;

    ctx.beginPath();
    ctx.moveTo(x + 16, y + 27);
    ctx.lineTo(x + 16, y + 37);
    ctx.moveTo(x + 23, y + 27);
    ctx.lineTo(x + 23, y + 37);
    ctx.stroke();

    ctx.restore();
}

/* Obstacle drawing */

function spawnObstacle() {
    const type = Math.random() > .30 ? "cactus" : "rock";

    const obstacle = {
        x: W + 30,
        type,
        w: type === "cactus" ? random(24, 35) : 34,
        h: type === "cactus" ? random(35, 59) : 24
    };

    obstacle.y = groundY - obstacle.h;

    obstacles.push(obstacle);
}

function drawObstacle(obstacle) {
    ctx.save();

    ctx.fillStyle = obstacle.type === "cactus"
        ? "#6cf0a8"
        : "#a1b5d4";

    ctx.shadowBlur = 12;
    ctx.shadowColor = obstacle.type === "cactus"
        ? "#38ffae"
        : "#6f9bda";

    if (obstacle.type === "cactus") {
        const x = obstacle.x;
        const y = obstacle.y;
        const h = obstacle.h;

        ctx.fillRect(x + 9, y, 12, h);
        ctx.fillRect(x, y + h * .40, 10, 7);
        ctx.fillRect(x, y + h * .24, 7, h * .20);
        ctx.fillRect(x + 21, y + h * .55, 10, 7);
        ctx.fillRect(x + 24, y + h * .35, 7, h * .23);
    } else {
        ctx.beginPath();
        ctx.moveTo(obstacle.x, groundY);
        ctx.lineTo(obstacle.x + 7, obstacle.y + 5);
        ctx.lineTo(obstacle.x + 20, obstacle.y);
        ctx.lineTo(obstacle.x + obstacle.w, groundY);
        ctx.closePath();
        ctx.fill();
    }

    ctx.restore();
}

/* Dust particles */

function updateParticles(dt) {
    for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];

        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vy += .12 * dt;
        p.life -= dt;

        ctx.globalAlpha = Math.max(0, p.life / 28);
        ctx.fillStyle = "#9befff";

        ctx.fillRect(p.x, p.y, p.size, p.size);

        if (p.life <= 0) {
            particles.splice(i, 1);
        }
    }

    ctx.globalAlpha = 1;
}

/* Collision detection */

function collides(a, b) {
    const padding = 8;

    return (
        a.x + padding < b.x + b.w &&
        a.x + a.w - padding > b.x &&
        a.y + padding < b.y + b.h &&
        a.y + a.h - padding > b.y
    );
}

/* Main game loop */

function update(dt) {
    frame += dt;
    score += dt * speed * .09;

    speed = Math.min(13, 6 + score / 250);

    // Jump physics
    dino.vy += .72 * dt;
    dino.y += dino.vy * dt;

    if (dino.y >= groundY - dino.h) {
        dino.y = groundY - dino.h;
        dino.vy = 0;
        dino.jumping = false;
    }

    // Spawn obstacles
    spawnTimer -= dt;

    if (spawnTimer <= 0) {
        spawnObstacle();
        spawnTimer = random(65, 115) / (speed / 6);
    }

    // Move obstacles
    for (let i = obstacles.length - 1; i >= 0; i--) {
        const o = obstacles[i];

        o.x -= speed * dt;

        if (o.x + o.w < 0) {
            obstacles.splice(i, 1);
            continue;
        }

        if (collides(dino, o)) {
            endGame();
            return;
        }
    }

    updateHUD();
}

function render(dt) {
    drawSky();
    drawHills(dt);
    drawGround(dt);

    obstacles.forEach(drawObstacle);

    updateParticles(dt);
    drawDino();

    // Vignette effect
    const vignette = ctx.createRadialGradient(
        W / 2, H / 2, 80,
        W / 2, H / 2, 570
    );

    vignette.addColorStop(0, "rgba(0,0,0,0)");
    vignette.addColorStop(1, "rgba(0,0,0,.42)");

    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, W, H);
}

function loop(timestamp) {
    if (!running) return;

    const dt = Math.min((timestamp - lastTime) / 16.67, 2.5);
    lastTime = timestamp;

    update(dt);
    render(dt);

    if (running) {
        animationId = requestAnimationFrame(loop);
    }
}

/* Keyboard controls */

document.addEventListener("keydown", function(event) {
    if (
        event.code === "Space" ||
        event.code === "ArrowUp"
    ) {
        event.preventDefault();

        if (!event.repeat) {
            jump();
        }
    }

    if (event.code === "ArrowDown") {
        event.preventDefault();

        if (running && !dino.jumping) {
            ducking = true;
        }
    }

    if (event.code === "KeyR" && gameOver) {
        startGame();
    }
});

document.addEventListener("keyup", function(event) {
    if (event.code === "ArrowDown") {
        ducking = false;
    }
});

canvas.addEventListener("pointerdown", function() {
    jump();
});

startBtn.addEventListener("click", startGame);

/* Initial scene */

makeStars();
makeHills();
resetGame();
render(0);
loadBestScore();

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/best", methods=["GET"])
def get_best():
    return jsonify({"best": best_score})


@app.route("/api/score", methods=["POST"])
def save_score():
    global best_score

    data = request.get_json(silent=True) or {}

    try:
        score = int(data.get("score", 0))
        score = max(0, min(score, 100000000))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid score"}), 400

    best_score = max(best_score, score)

    return jsonify({"best": best_score})


if __name__ == "__main__":
    app.run(debug=True)
