# This is a simple models.py file for the Plinko game

class User:
    """
    A simple User class to manage user data.
    In a real application, this would likely integrate with a database.
    """
    def __init__(self, user_id, username, balance=1000):
        self.id = user_id
        self.username = username
        self.balance = balance
    
    def update_balance(self, new_balance):
        """Update the user's balance."""
        self.balance = new_balance
        return self.balance
    
    def deduct_amount(self, amount):
        """Deduct an amount from the user's balance."""
        if amount > self.balance:
            return False
        self.balance -= amount
        return True
    
    def add_amount(self, amount):
        """Add an amount to the user's balance."""
        self.balance += amount
        return self.balance