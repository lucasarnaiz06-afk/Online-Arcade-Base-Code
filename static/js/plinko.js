document.addEventListener('DOMContentLoaded', function() {
    // Game configuration
    const config = {
        rows: 8,
        pins: 9,
        ballRadius: 10,
        betAmount: 5,
        minBet: 1,
        maxBet: 100
    };
    
    // DOM elements
    const plinkoBoard = document.getElementById('plinko-board');
    const dropBallBtn = document.getElementById('drop-ball');
    const decreaseBetBtn = document.getElementById('decrease-bet');
    const increaseBetBtn = document.getElementById('increase-bet');
    const currentBetDisplay = document.getElementById('current-bet');
    const betAmountInput = document.getElementById('bet_amount_input');
    const landingPositionInput = document.getElementById('landing_position');
    const resultMessage = document.getElementById('result-message');
    const balanceDisplay = document.getElementById('balance');
    
    // Initialize the game board
    initializeBoard();
    
    // Set up event listeners
    dropBallBtn.addEventListener('click', dropBall);
    decreaseBetBtn.addEventListener('click', decreaseBet);
    increaseBetBtn.addEventListener('click', increaseBet);
    
    function initializeBoard() {
        // Clear the board
        plinkoBoard.innerHTML = '';
        
        // Create pins
        for (let row = 0; row < config.rows; row++) {
            const pinRow = document.createElement('div');
            pinRow.className = 'pin-row';
            
            const pinsInRow = row + 1;
            for (let pin = 0; pin < pinsInRow; pin++) {
                const pinElement = document.createElement('div');
                pinElement.className = 'pin';
                pinRow.appendChild(pinElement);
            }
            
            plinkoBoard.appendChild(pinRow);
        }
        
        // Create slots at the bottom
        const slotsRow = document.createElement('div');
        slotsRow.className = 'slots-row';
        
        for (let slot = 0; slot <= config.rows; slot++) {
            const slotElement = document.createElement('div');
            slotElement.className = 'slot';
            slotElement.textContent = getPayoutForSlot(slot);
            slotsRow.appendChild(slotElement);
        }
        
        plinkoBoard.appendChild(slotsRow);
    }
    
    function getPayoutForSlot(slot) {
        // This is a simple payout scheme; you might want to adjust based on your game design
        const payouts = [10, 2, 1.5, 1, 0.5, 1, 1.5, 2, 10];
        return payouts[slot] || 1;
    }
    
    function dropBall() {
        // Disable the drop button while the ball is falling
        dropBallBtn.disabled = true;
        
        // Create the ball element
        const ball = document.createElement('div');
        ball.className = 'ball';
        plinkoBoard.appendChild(ball);
        
        // Position the ball at the top center of the board
        const boardWidth = plinkoBoard.offsetWidth;
        ball.style.left = (boardWidth / 2 - config.ballRadius) + 'px';
        ball.style.top = '0px';
        
        // Animate the ball falling through the pins
        let currentRow = 0;
        let horizontalPosition = config.rows / 2; // Start in the middle
        
        const fallInterval = setInterval(() => {
            if (currentRow >= config.rows) {
                clearInterval(fallInterval);
                const finalSlot = Math.round(horizontalPosition);
                const payout = getPayoutForSlot(finalSlot);
                
                // Update the landing position input for form submission
                landingPositionInput.value = finalSlot;
                
                // Submit the form via AJAX with CSRF token
                submitResult(finalSlot, payout);
                return;
            }
            
            // Calculate new vertical position
            const verticalPosition = (currentRow + 1) * (plinkoBoard.offsetHeight / (config.rows + 2));
            ball.style.top = verticalPosition + 'px';
            
            // Randomly decide if the ball goes left or right
            const goesLeft = Math.random() > 0.5;
            horizontalPosition += goesLeft ? -0.5 : 0.5;
            horizontalPosition = Math.max(0, Math.min(horizontalPosition, config.rows));
            
            // Calculate new horizontal position
            const horizontalPixelPosition = (horizontalPosition / config.rows) * boardWidth;
            ball.style.left = (horizontalPixelPosition - config.ballRadius) + 'px';
            
            currentRow++;
        }, 300);
    }
    
    function submitResult(landingSlot, payout) {
        // Get the CSRF token value
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;
        
        // Prepare the form data
        const formData = new FormData();
        formData.append('csrf_token', csrfToken);
        formData.append('bet_amount', betAmountInput.value);
        formData.append('landing_position', landingSlot);
        
        // Send AJAX request
        fetch(document.getElementById('plinko-form').action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Update the game UI with the result
            if (data.success) {
                const winAmount = data.win_amount;
                balanceDisplay.textContent = data.new_balance;
                
                if (winAmount > 0) {
                    resultMessage.textContent = `You won $${winAmount}!`;
                    resultMessage.className = 'result-message win';
                } else {
                    resultMessage.textContent = 'Better luck next time!';
                    resultMessage.className = 'result-message lose';
                }
            } else {
                resultMessage.textContent = data.message || 'An error occurred';
                resultMessage.className = 'result-message error';
            }
            
            // Re-enable the drop button
            dropBallBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            resultMessage.textContent = 'An error occurred. Please try again.';
            resultMessage.className = 'result-message error';
            dropBallBtn.disabled = false;
        });
    }
    
    function decreaseBet() {
        if (config.betAmount > config.minBet) {
            config.betAmount -= 1;
            updateBetDisplay();
        }
    }
    
    function increaseBet() {
        if (config.betAmount < config.maxBet) {
            config.betAmount += 1;
            updateBetDisplay();
        }
    }
    
    function updateBetDisplay() {
        currentBetDisplay.textContent = `$${config.betAmount}`;
        betAmountInput.value = config.betAmount;
    }
});
