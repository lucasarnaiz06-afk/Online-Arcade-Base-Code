function Boundary(x, y, w, h) {
    let options = {
      isStatic: true,
      restitution: 1,
      friction: 0,
    };
    this.body = Bodies.rectangle(x, y, w, h, options);
    this.w = w;
    this.h = h;
    Composite.add(world, this.body);
  }
  
  Boundary.prototype.show = function () {
    fill(255);
    stroke(255);
    let pos = this.body.position;
    push();
    translate(pos.x, pos.y);
    rectMode(CENTER);
    rect(0, 0, this.w, this.h);
    pop();
  };
  