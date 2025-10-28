function Particle(x, y, r) {
    let options = {
      restitution: 0.4,
      friction: 0.8,
      collisionFilter: {
        group: -1 // ensures particles don't collide with each other
      }
    };
    this.body = Bodies.circle(x, y, r, options);
    this.r = r;
    Composite.add(world, this.body);
  }
  
  Particle.prototype.show = function () {
    fill(255);
    stroke(255);
    let pos = this.body.position;
    push();
    translate(pos.x, pos.y);
    ellipse(0, 0, this.r * 2);
    pop();
  };
  
  Particle.prototype.isOffscreen = function () {
    let { x, y } = this.body.position;
    return x < -50 || x > width + 50 || y > height + 50;
  };