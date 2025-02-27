from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from bot.trader import TradingBot
import os
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

# Create Flask app with static folder properly configured
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.urandom(24)

# Initialize trading bot (default to simulation mode for safety)
simulation_mode = True  # Default to simulation mode
bot = TradingBot(
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
    simulation_mode=simulation_mode
)

# Bot control thread
bot_thread = None
bot_running = False

def bot_loop():
    global bot_running
    while bot_running:
        try:
            bot.scan_market()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in bot loop: {e}")
    print("Bot stopped")

@app.route('/')
def index():
    return render_template('index.html', 
                          bot_status=bot_running,
                          positions=bot.get_open_positions(),
                          simulation_mode=simulation_mode,
                          stats=bot.get_performance_stats())

@app.route('/start', methods=['POST'])
def start_bot():
    global bot_thread, bot_running
    coins = request.form.get('coins').split(',')
    coins = [coin.strip().upper() for coin in coins]
    
    if not coins:
        flash("Please enter at least one coin")
        return redirect(url_for('index'))
    
    bot.set_coins(coins)
    
    if not bot_running:
        bot_running = True
        bot_thread = threading.Thread(target=bot_loop)
        bot_thread.daemon = True
        bot_thread.start()
        if simulation_mode:
            flash("Bot started with REAL market data but SIMULATED trades. No real orders will be executed.")
        else:
            flash("Bot started in LIVE mode. REAL trades will be executed!")
    else:
        flash("Bot is already running!")
    
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_running
    bot_running = False
    flash("Bot has been stopped.")
    return redirect(url_for('index'))

@app.route('/toggle-mode', methods=['POST'])
def toggle_mode():
    global bot, simulation_mode, bot_running
    
    # Can't change mode while bot is running
    if bot_running:
        flash("Stop the bot before changing simulation mode!")
        return redirect(url_for('index'))
    
    # Toggle mode
    simulation_mode = not simulation_mode
    
    # Re-initialize the bot with new mode
    bot = TradingBot(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
        simulation_mode=simulation_mode
    )
    
    if simulation_mode:
        flash("Switched to SIMULATION mode with real market data. No real trades will be executed.")
    else:
        flash("Switched to LIVE mode. WARNING: Real trades will be executed!")
    
    return redirect(url_for('index'))

@app.route('/positions')
def positions():
    return jsonify(bot.get_open_positions())

@app.route('/stats')
def stats():
    return jsonify(bot.get_performance_stats())

@app.route('/history')
def history():
    return jsonify(bot.get_trade_history())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
