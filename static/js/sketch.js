
let Engine = Matter.Engine,
  Composite = Matter.Composite,
  Bodies = Matter.Bodies;

let engine;
let world;
let particles = [];
let plinkos = [];
let bounds = [];
let rows = 13;
let spacing = 40;
let topPlinkoPos;
let cols;
let fixedPayouts = [4, 2, 1.4, 1, 0.8, 0.5, 0.5, 0.3, 0.5, 0.5, 0.8, 1, 1.4, 2, 4];

function setup() {
  let canvas = createCanvas(600, 600);
  canvas.parent("plinko-canvas-container");
  engine = Engine.create();
  world = engine.world;

  cols = fixedPayouts.length - 1;

  for (let row = 0; row < rows - 1; row++) {
    let pinsInRow = row + 3;
    for (let col = 0; col < pinsInRow; col++) {
      let x = width / 2 - ((pinsInRow - 1) * spacing) / 2 + col * spacing;
      let y = 100 + row * spacing;
      let plinko = new Plinko(x, y, 5);
      plinkos.push(plinko);
      if (row === 0 && col === 1) {
        topPlinkoPos = { x, y };
      }
    }
  }

  let slotCount = fixedPayouts.length;
  let slotWidth = width * 0.9 / slotCount;
  let xOffset = width * 0.05;
  

  
  const container = document.getElementById("plinko-button-wrapper");
  const dropBtn = createButton('Drop Ball');
  dropBtn.parent(container);
  dropBtn.id('drop-ball-button');
  dropBtn.mousePressed((e) => {
    console.log(e)
    const bet = getCurrentBet();
    if (topPlinkoPos && currentUserCoins() >= bet) {
      const csrf = document.querySelector('input[name="csrf_token"]').value;

      fetch('/games/plinko/start', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf },
        body: new URLSearchParams({
          'csrf_token': csrf,
          'bet_amount': bet,
        })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            let jitter = random(-2, 2);
            particles.push(new Particle(topPlinkoPos.x + jitter, topPlinkoPos.y - 90, 5));
            document.getElementById('balance').textContent = data.new_balance;
          } else {
            alert(data.message);
          }
        });
    }
  });
}

function draw() {
  animateSlots();
  background(0);
  Engine.update(engine);

  for (let p of plinkos) p.show();
  for (let b of bounds) b.show();

  for (let i = particles.length - 1; i >= 0; i--) {
    let particle = particles[i];
    particle.show();
    if (particle.body.position.y > height - 30) {
      let x = particle.body.position.x;
      let bet = getCurrentBet();
      processPlinkoResult(x, bet);
      Composite.remove(world, particle.body);
      particles.splice(i, 1);
    }
  }

  textAlign(CENTER);
  textSize(16);
  let slotWidth = width * 0.9 / (cols + 1);
  let xOffset = width * 0.05;
  
for (let i = 0; i < fixedPayouts.length; i++) {
    let x = xOffset + i * slotWidth + slotWidth / 2;
    let y = height - 20;
    let mult = fixedPayouts[i];
    fill(mult >= 5 ? '#e74c3c' : mult >= 2 ? '#e67e22' : mult >= 1 ? '#f1c40f' : '#3498db');
    rectMode(CENTER);
    
    let bounce = 1 + slotAnimations[i] * 0.3;
    rect(x, y + slotAnimations[i] * 5, 40 * bounce, 25 * bounce, 8);

    fill(255);
    text(`${mult}x`, x, y + 5);
  }
}

function processPlinkoResult(x, bet) {
  let slotWidth = width * 0.9 / (cols + 1);
  let xOffset = width * 0.05;
  let slotIndex = Math.floor((x - xOffset) / slotWidth);
  slotIndex = Math.max(0, Math.min(fixedPayouts.length - 1, slotIndex));
  let multiplier = fixedPayouts[slotIndex];
  let payout = Math.floor(bet * multiplier);
  slotAnimations[slotIndex] = 1;

  const csrf = document.querySelector('input[name="csrf_token"]').value;

  fetch('/games/plinko/payout', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf },
    body: new URLSearchParams({
      'csrf_token': csrf,
      'payout': payout,
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const balanceElem = document.getElementById('balance');
        balanceElem.textContent = data.new_balance;

        const plus = document.createElement("span");
        plus.textContent = ` +${payout}`;
        plus.style.color = "lime";
        plus.style.marginLeft = "10px";
        plus.style.transition = "opacity 1s ease";
        plus.style.opacity = 1;
        plus.style.fontWeight = 'bold';
        balanceElem.parentNode.appendChild(plus);
        setTimeout(() => plus.style.opacity = 0, 800);
        setTimeout(() => plus.remove(), 1800);
      } else {
        alert(data.message);
      }
    });
}

function getCurrentBet() {
  return parseInt(document.getElementById('bet_amount_input').value || '1');
}

function currentUserCoins() {
  return parseInt(document.getElementById('balance').textContent || '0');
}


let slotAnimations = new Array(fixedPayouts.length).fill(0);

function animateSlots() {
  for (let i = 0; i < slotAnimations.length; i++) {
    if (slotAnimations[i] > 0) {
      slotAnimations[i] -= 0.05;
      if (slotAnimations[i] < 0) slotAnimations[i] = 0;
    }
  }
}