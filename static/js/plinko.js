function Plinko(x, y, r) {
    let options = {
      isStatic: true,
      restitution: 0,
      friction: 0.04,
    };
    this.body = Bodies.circle(x, y, r, options);
    this.r = r;
    Composite.add(world, this.body);
  }
  
  Plinko.prototype.show = function () {
    fill(0, 255, 0);
    stroke(255);
    let pos = this.body.position;
    push();
    translate(pos.x, pos.y);
    ellipse(0, 0, this.r * 2);
    pop();
  };
  