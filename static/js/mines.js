// Fixed AJAX functionality for tile picking
let gameActive = window.gameActive || false;

// Make pickTile function globally accessible
window.pickTile = pickTile;

function pickTile(tileIndex) {
  if (!gameActive) return;
  
  const tile = document.querySelector(`[data-tile="${tileIndex}"]`);
  if (!tile || tile.classList.contains('revealed') || tile.classList.contains('mine') || tile.classList.contains('selected')) return;
  
  // Add immediate visual feedback
  tile.classList.add('selected', 'loading');
  playClickSound();
  
  // Create ripple effect
  createRipple(tile);
  
  // Get the current page URL and construct the pick URL
  const currentUrl = window.location.href;
  const baseUrl = currentUrl.split('/mines')[0];
  const pickUrl = `${baseUrl}/mines/pick/${tileIndex}`;
  
  // Get CSRF token from meta tag or form
  const csrfToken = getCSRFToken();
  
  // Make AJAX request
  fetch(pickUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})  // <--- This is required!
    })

  .then(response => response.json())
  .then(data => {
    setTimeout(() => {
      tile.classList.remove('loading');
      
      if (data.success) {
        if (data.is_mine) {
          // Hit a mine
          tile.classList.remove('selected');
          tile.classList.add('mine');
          tile.innerHTML = '💣';
          playFailSound();
          gameActive = false;
          
          // Reveal all mines after a delay
          setTimeout(() => {
            if (data.mine_positions) {
              data.mine_positions.forEach(pos => {
                const mineTile = document.querySelector(`[data-tile="${pos}"]`);
                if (mineTile && !mineTile.classList.contains('mine')) {
                  mineTile.classList.add('mine');
                  mineTile.innerHTML = '💣';
                }
              });
            }
            showGameOver(false);
          }, 1000);
          
        } else {
          // Safe tile
          tile.classList.remove('selected');
          tile.classList.add('revealed');
          tile.innerHTML = '✅';
          createParticles(tile);
          playSuccessSound();
          
          // Update stats
          updateGameStats(data);
          
          // Check if won
          if (data.won) {
            gameActive = false;
            setTimeout(() => showGameOver(true), 500);
          }
        }
      } else {
        console.error('Server error:', data.error);
        // Remove visual feedback on error
        tile.classList.remove('selected', 'loading');
      }
    }, 500); // Slightly longer delay for better UX
  })
  .catch(error => {
    console.error('Error:', error);
    tile.classList.remove('loading', 'selected');
  });
}

function getCSRFToken() {
  // Try to get CSRF token from meta tag first
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  if (metaToken) {
    return metaToken.getAttribute('content');
  }
  
  // Try to get from hidden input
  const hiddenToken = document.querySelector('input[name="csrf_token"]');
  if (hiddenToken) {
    return hiddenToken.value;
  }
  
  // Fallback - try to get from any form
  const formToken = document.querySelector('[name="csrf_token"]');
  if (formToken) {
    return formToken.value;
  }
  
  return '';
}

function updateGameStats(data) {
  // Update sidebar stats
  const safeRevealedEl = document.querySelector('.stat-value');
  if (safeRevealedEl) {
    safeRevealedEl.textContent = data.safe_revealed;
  }
  
  // Update multiplier
  const multiplierEl = document.querySelector('.multiplier-display');
  if (multiplierEl && data.multiplier) {
    multiplierEl.textContent = data.multiplier.toFixed(2) + 'x Multiplier';
    multiplierEl.classList.add('glow');
    setTimeout(() => multiplierEl.classList.remove('glow'), 500);
  }
  
  // Update cash out amount
  const cashOutAmount = document.querySelector('.cash-out-amount');
  if (cashOutAmount && data.payout) {
    cashOutAmount.textContent = Math.floor(data.payout) + ' Coins';
  }
  
  // Update mines stats in main area
  const minesStats = document.querySelectorAll('.mines-stats .stat-value');
  if (minesStats.length >= 3) {
    minesStats[0].textContent = data.safe_revealed;
  }
}

function showGameOver(won) {
  const gameCard = document.querySelector('.game-card');
  if (!gameCard) return;
  
  const overlay = document.createElement('div');
  overlay.className = 'game-over-overlay';
  
  // Get current URL for the play again link
  const currentUrl = window.location.href;
  const resetUrl = currentUrl.includes('?') ? `${currentUrl}&reset=true` : `${currentUrl}?reset=true`;
  
  overlay.innerHTML = `
    <div class="text-center text-white">
      <div class="game-over-icon mb-3">
        <i class="bi bi-${won ? 'trophy-fill text-warning' : 'exclamation-triangle-fill text-danger'}" style="font-size: 3rem;"></i>
      </div>
      <h3>Game Over!</h3>
      <p class="mb-4">
        ${won ? '🎉 Congratulations! You successfully avoided all mines!' : '💥 You hit a mine! Better luck next time in the minefield!'}
      </p>
      <a href="${resetUrl}" class="btn btn-primary btn-lg">
        <i class="bi bi-arrow-clockwise"></i> Play Again
      </a>
    </div>
  `;
  
  gameCard.style.position = 'relative';
  gameCard.appendChild(overlay);
}

// Particle effects
function createParticles(element) {
  for (let i = 0; i < 8; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 0.5 + 's';
    element.appendChild(particle);
    
    setTimeout(() => particle.remove(), 2000);
  }
}

// Ripple effect
function createRipple(element) {
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
  
  element.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
}

// Sound effects
function playClickSound() {
  try {
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
  } catch(e) {
    // Ignore audio errors
  }
}

function playSuccessSound() {
  try {
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
  } catch(e) {
    // Ignore audio errors
  }
}

function playFailSound() {
  try {
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
  } catch(e) {
    // Ignore audio errors
  }
}

// Enhanced welcome icon animation
document.addEventListener('DOMContentLoaded', function() {
  const welcomeIcon = document.querySelector('.welcome-icon');
  if (welcomeIcon) {
    welcomeIcon.addEventListener('mouseenter', function() {
      this.style.transform = 'scale(1.1) rotate(5deg)';
    });
    welcomeIcon.addEventListener('mouseleave', function() {
      this.style.transform = 'scale(1) rotate(0deg)';
    });
  }
  
  // Auto-focus bet input when page loads
  const betInput = document.querySelector('input[name="bet"]');
  if (betInput) {
    betInput.focus();
  }
  
  // Add click event listeners to mine tiles (backup to onclick)
  const mineTiles = document.querySelectorAll('.mine-tile[data-tile]');
  mineTiles.forEach(tile => {
    const tileIndex = parseInt(tile.dataset.tile);
    tile.addEventListener('click', () => {
      if (gameActive) {
        pickTile(tileIndex);
      }
    });
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const mineTiles = document.querySelectorAll('.mine-tile[data-tile]');
  mineTiles.forEach(tile => {
    const tileIndex = parseInt(tile.dataset.tile);
    tile.addEventListener('click', () => {
      if (gameActive) {
        pickTile(tileIndex);
      }
    });
  });
});

// Cash out button enhancement
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

// Prevent double-clicks on cash out button
document.querySelectorAll('.btn-cash-out').forEach(btn => {
  btn.addEventListener('click', function() {
    this.disabled = true;
    setTimeout(() => {
      this.disabled = false;
    }, 1000);
  });
});

// Add loading state to forms
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function() {
    const submitBtn = this.querySelector('button[type="submit"], button:not([type])');
    if (submitBtn) {
      setTimeout(() => {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Loading...';
      }, 100);
    }
  });
});

// Keyboard controls for accessibility
document.addEventListener('keydown', function(event) {
  if (gameActive && event.key >= '1' && event.key <= '9') {
    const tileIndex = parseInt(event.key) - 1;
    if (tileIndex < 25) { // 5x5 grid
      pickTile(tileIndex);
    }
  }
});

function getCSRFToken() {
  const metaToken = document.querySelector('meta[name="csrf-token"]');
  return metaToken ? metaToken.getAttribute('content') : '';
}
