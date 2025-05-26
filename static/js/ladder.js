// Add particle effects when revealing steps
    function createParticles(element) {
      for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 0.5 + 's';
        element.appendChild(particle);
        
        setTimeout(() => particle.remove(), 2000);
      }
    }
    
    // Add particle effects to revealed steps
    document.addEventListener('DOMContentLoaded', function() {
      const revealedSteps = document.querySelectorAll('.ladder-step.revealed');
      revealedSteps.forEach(step => {
        if (step.classList.contains('safe-step') || step.classList.contains('fail-step')) {
          createParticles(step);
        }
      });
      
      // Add subtle animation to welcome icon
      const welcomeIcon = document.querySelector('.welcome-icon');
      if (welcomeIcon) {
        welcomeIcon.addEventListener('mouseenter', function() {
          this.style.transform = 'scale(1.1) rotate(5deg)';
        });
        welcomeIcon.addEventListener('mouseleave', function() {
          this.style.transform = 'scale(1) rotate(0deg)';
        });
      }
    });
    
    // Enhanced click feedback for choice buttons
    document.querySelectorAll('.btn-choice').forEach(btn => {
      btn.addEventListener('click', function() {
        // Add click feedback
        this.style.transform = 'scale(0.95)';
        
        // Create ripple effect
        const ripple = document.createElement('div');
        ripple.style.position = 'absolute';
        ripple.style.borderRadius = '50%';
        ripple.style.background = 'rgba(255,255,255,0.6)';
        ripple.style.transform = 'scale(0)';
        ripple.style.animation = 'ripple 0.6s linear';
        ripple.style.left = '50%';
        ripple.style.top = '50%';
        ripple.style.width = '10px';
        ripple.style.height = '10px';
        ripple.style.marginLeft = '-5px';
        ripple.style.marginTop = '-5px';
        
        this.appendChild(ripple);
        
        setTimeout(() => {
          this.style.transform = '';
          ripple.remove();
        }, 600);
      });
    });
    
    // Add ripple animation keyframes
    const style = document.createElement('style');
    style.textContent = `
      @keyframes
      ripple {
        0% { transform: scale(0); opacity: 1; }
        100% { transform: scale(4); opacity: 0; }
      }
    `;
    document.head.appendChild(style);
    
    // Auto-focus bet input when page loads
    document.addEventListener('DOMContentLoaded', function() {
      const betInput = document.querySelector('input[name="bet"]');
      if (betInput) {
        betInput.focus();
      }
    });
    
    // Add smooth scrolling to ladder board
    function scrollToLatestRow() {
      const latestRow = document.querySelector('.ladder-row:last-child');
      if (latestRow) {
        latestRow.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }
    }
    
    // Call scroll function if there are ladder rows
    if (document.querySelector('.ladder-row')) {
      setTimeout(scrollToLatestRow, 500);
    }
    
    // Add sound effects (using Web Audio API)
    function playClickSound() {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.1);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.1);
    }
    
    function playSuccessSound() {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(523, audioContext.currentTime);
      oscillator.frequency.setValueAtTime(659, audioContext.currentTime + 0.1);
      oscillator.frequency.setValueAtTime(784, audioContext.currentTime + 0.2);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    }
    
    function playFailSound() {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(100, audioContext.currentTime + 0.5);
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    }
    
    // Add sound to buttons
    document.querySelectorAll('.btn-choice').forEach(btn => {
      btn.addEventListener('click', playClickSound);
    });
    
    // Play appropriate sounds based on game state
    const safeSteps = document.querySelectorAll('.safe-step');
    const failSteps = document.querySelectorAll('.fail-step');
    
    if (safeSteps.length > 0) {
      setTimeout(playSuccessSound, 300);
    }
    
    if (failSteps.length > 0) {
      setTimeout(playFailSound, 300);
    }
    
    // Add keyboard controls
    document.addEventListener('keydown', function(event) {
      if (document.querySelector('.choice-buttons')) {
        switch(event.key) {
          case 'ArrowLeft':
          case 'a':
          case 'A':
            event.preventDefault();
            document.querySelector('form[action*="left"] button')?.click();
            break;
          case 'ArrowUp':
          case 'w':
          case 'W':
            event.preventDefault();
            document.querySelector('form[action*="middle"] button')?.click();
            break;
          case 'ArrowRight':
          case 'd':
          case 'D':
            event.preventDefault();
            document.querySelector('form[action*="right"] button')?.click();
            break;
        }
      }
    });
    
    // Add tooltips for keyboard controls
    const choiceButtons = document.querySelectorAll('.btn-choice');
    if (choiceButtons.length > 0) {
      choiceButtons[0].title = 'Left Arrow or A key';
      choiceButtons[1].title = 'Up Arrow or W key';
      choiceButtons[2].title = 'Right Arrow or D key';
    }
    
    // Prevent double-clicks without blocking form submission
    document.querySelectorAll('.btn-cash-out').forEach(btn => {
      btn.addEventListener('click', function() {
        this.disabled = true;
        setTimeout(() => {
          this.disabled = false;
        }, 1000);
      });
    });
    
// Add safe loading state to forms (without blocking submit)
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"], button:not([type])');
        if (submitBtn) {
          // Delay changes to allow form to submit properly
          setTimeout(() => {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Loading...';
          }, 100);
        }
      });
    });

    
    // Add dynamic multiplier counter animation
    const multiplierElement = document.querySelector('.multiplier-glow');
    if (multiplierElement) {
      let currentMultiplier = parseFloat(multiplierElement.textContent);
      let targetMultiplier = currentMultiplier;
      
      function animateMultiplier() {
        if (Math.abs(currentMultiplier - targetMultiplier) > 0.01) {
          currentMultiplier += (targetMultiplier - currentMultiplier) * 0.1;
          multiplierElement.textContent = currentMultiplier.toFixed(2) + 'x';
          requestAnimationFrame(animateMultiplier);
        }
      }
      
      // Start animation if needed
      animateMultiplier();
    }
    
    // Add visual feedback for successful cash out
    const cashOutBtn = document.querySelector('.btn-cash-out');
    if (cashOutBtn) {
      cashOutBtn.addEventListener('click', function(e) {
        // Add success animation
        this.innerHTML = '<i class="bi bi-check-circle"></i> Cashing Out...';
        this.style.background = 'rgba(40,167,69,0.8)';
        
        // Create celebration particles
        for (let i = 0; i < 10; i++) {
          const particle = document.createElement('div');
          particle.style.position = 'fixed';
          particle.style.left = e.clientX + 'px';
          particle.style.top = e.clientY + 'px';
          particle.style.width = '6px';
          particle.style.height = '6px';
          particle.style.background = '#ffd700';
          particle.style.borderRadius = '50%';
          particle.style.pointerEvents = 'none';
          particle.style.zIndex = '9999';
          
          const angle = (i / 10) * Math.PI * 2;
          const velocity = 100;
          const vx = Math.cos(angle) * velocity;
          const vy = Math.sin(angle) * velocity;
          
          particle.style.animation = `
            particle-burst 1s ease-out forwards
          `;
          
          document.body.appendChild(particle);
          
          setTimeout(() => particle.remove(), 1000);
        }
      });
    }
    
    // Add particle burst animation
    const particleBurstStyle = document.createElement('style');
    particleBurstStyle.textContent = `
      @keyframes particle-burst {
        0% {
          transform: translate(0, 0) scale(1);
          opacity: 1;
        }
        100% {
          transform: translate(var(--dx, 50px), var(--dy, -50px)) scale(0);
          opacity: 0;
        }
      }
    `;
    document.head.appendChild(particleBurstStyle);