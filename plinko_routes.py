from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect

# Assuming you have a user model to track balance
from models import User

plinko_bp = Blueprint('plinko', __name__)

@plinko_bp.route('/plinko')
def plinko():
    """Render the Plinko game page."""
    # Get user balance - this would typically come from your database or user session
    balance = session.get('balance', 1000)  # Default to 1000 if not set
    
    return render_template('plinko.html', balance=balance)

@plinko_bp.route('/plinko/play', methods=['POST'])
def plinko_play():
    """Handle Plinko game play requests."""
    if not request.form.get('csrf_token'):
        # No CSRF token provided
        return jsonify({
            'success': False,
            'message': 'CSRF token missing'
        }), 400
    
    # Get bet amount and landing position from form
    try:
        bet_amount = int(request.form.get('bet_amount', 5))
        landing_position = int(request.form.get('landing_position', 0))
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Invalid bet amount or landing position'
        }), 400
    
    # Get current balance
    balance = session.get('balance', 1000)
    
    # Check if user has enough balance
    if balance < bet_amount:
        return jsonify({
            'success': False,
            'message': 'Insufficient balance'
        }), 400
    
    # Calculate payout based on landing position
    payouts = [10, 5, 3, 2, 1, 2, 3, 5, 10]
    payout_multiplier = payouts[landing_position] if 0 <= landing_position < len(payouts) else 1
    win_amount = bet_amount * payout_multiplier
    
    # Update balance
    new_balance = balance - bet_amount + win_amount
    session['balance'] = new_balance
    
    # In a real app, you would update the user's balance in your database here
    # Example: current_user.update_balance(new_balance)
    
    # Return the result
    return jsonify({
        'success': True,
        'landing_position': landing_position,
        'bet_amount': bet_amount,
        'win_amount': win_amount,
        'new_balance': new_balance
    })

# Add this blueprint to your main app.py file:
# from plinko_routes import plinko_bp
# app.register_blueprint(plinko_bp)