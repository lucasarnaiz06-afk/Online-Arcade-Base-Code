let Engine = Matter.Engine,
  Composite = Matter.Composite,
  Bodies = Matter.Bodies;

let engine;
let world;
let particles = [];
let plinkos = [];
let bounds = [];
let rows = 10;
let spacing = 50;
let topPlinkoPos;
let cols;
let fixedPayouts = [5.6, 2.1, 1.1, 1, 0.5, 1, 1.1, 2.1, 5.6];

function setup() {
  let canvas = createCanvas(600, 700);
  canvas.parent("plinko-canvas-container");
  engine = Engine.create();
  world = engine.world;

  cols = fixedPayouts.length - 1;

  for (let row = 0; row < rows; row++) {
    let pinsInRow = row + 3;
    for (let col = 0; col < pinsInRow; col++) {
      let x = width / 2 - ((pinsInRow - 1) * spacing) / 2 + col * spacing;
      let y = 100 + row * spacing;
      let plinko = new Plinko(x, y, 5);
      plinkos.push(plinko);
      if (row === 0 && col === 1) topPlinkoPos = { x, y };
    }
  }

  let slotCount = cols + 1;
  let slotWidth = width / slotCount;
  let dividerHeight = 140;
  for (let i = 0; i <= slotCount; i++) {
    let x = i * slotWidth;
    bounds.push(new Boundary(x, height - dividerHeight / 2, 10, dividerHeight));
    let cap = Bodies.circle(x, height - dividerHeight - 5, 6, {
      isStatic: true,
      restitution: 1,
      friction: 0
    });
    Composite.add(world, cap);
  }

  bounds.push(new Boundary(width / 2, height + 40, width, 100));

  const dropBtn = createButton('Drop Ball');
  dropBtn.parent("plinko-canvas-container");
  dropBtn.style('margin-top', '10px');
  dropBtn.mousePressed(() => {
    if (topPlinkoPos && currentUserCoins() >= getCurrentBet()) {
      let jitter = random(-2, 2);
      particles.push(new Particle(topPlinkoPos.x + jitter, topPlinkoPos.y - 30, 5));
    }
  });
}

function draw() {
  background(0);
  Engine.update(engine);

  for (let p of plinkos) p.show();
  for (let b of bounds) b.show();

  for (let i = particles.length - 1; i >= 0; i--) {
    let particle = particles[i];
    particle.show();
    if (particle.isOffscreen()) {
      let x = particle.body.position.x;
      let slot = Math.floor((x / width) * (cols + 1));
      let bet = getCurrentBet();
      let multiplier = getPayoutMultiplier(slot);
      let payout = Math.floor(bet * multiplier);
      submitPlinkoResult(slot, bet, payout);
      Composite.remove(world, particle.body);
      particles.splice(i, 1);
    }
  }

  textAlign(CENTER);
  textSize(16);
  let slotWidth = width / (cols + 1);
  for (let i = 0; i < fixedPayouts.length; i++) {
    let x = i * slotWidth + slotWidth / 2;
    let y = height - 10;
    let mult = fixedPayouts[i];
    fill(mult >= 5 ? '#e74c3c' : mult >= 2 ? '#e67e22' : mult >= 1 ? '#f1c40f' : '#3498db');
    rectMode(CENTER);
    rect(x, y, 40, 25, 8);
    fill(255);
    text(`${mult}x`, x, y + 5);
  }
}

function getPayoutMultiplier(slotIndex) {
  return fixedPayouts[slotIndex] || 1;
}

function submitPlinkoResult(slotIndex, bet, winnings) {
  const csrf = document.querySelector('input[name="csrf_token"]').value;

  fetch('/games/plinko/play', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrf },
    body: new URLSearchParams({
      'csrf_token': csrf,
      'bet_amount': bet,
      'landing_position': slotIndex,
    })
  })
    .then(res => res.json())
    .then(data => {
      const msg = document.getElementById('result-message');
      if (data.success) {
        msg.textContent = `Slot ${slotIndex} → Multiplier: ${getPayoutMultiplier(slotIndex)}x → You won ${data.win_amount} coins!`;
        msg.className = 'result-message win';
        document.getElementById('balance').textContent = data.new_balance;
      } else {
        msg.textContent = data.message;
        msg.className = 'result-message lose';
      }
    })
    .catch(err => {
      console.error("Error submitting plinko result:", err);
    });
}

function getCurrentBet() {
  return parseInt(document.getElementById('bet_amount_input').value || '5');
}

function currentUserCoins() {
  return parseInt(document.getElementById('balance').textContent || '0');
}
