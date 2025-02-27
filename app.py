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

# Initialize trading bot (simulation mode only)
simulation_mode = True  # Always simulation mode
bot = TradingBot(
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
    simulation_mode=True
)

# Bot control thread
bot_thread = None
bot_running = False

def bot_loop():
    global bot_running
    last_scan_time = 0
    
    while bot_running:
        try:
            current_time = time.time()
            
            # Always check open positions (every second)
            bot.check_open_positions()
            
            # Scan market for new entries every 10 seconds
            if current_time - last_scan_time >= 10:
                bot.scan_market()
                last_scan_time = current_time
                
            # Sleep for 1 second
            time.sleep(1)
            
        except Exception as e:
            print(f"Error in bot loop: {e}")
    
    print("Bot stopped")

@app.route('/')
def index():
    return render_template('index.html', 
                          bot_status=bot_running,
                          positions=bot.get_open_positions(),
                          simulation_mode=True,  # Always True
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
        flash("Bot started in SIMULATION mode with REAL market data. No real orders will be executed.")
    else:
        flash("Bot is already running!")
    
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_bot():
    global bot_running
    bot_running = False
    flash("Bot has been stopped.")
    return redirect(url_for('index'))

# Remove the toggle-mode route since we're always in simulation mode

@app.route('/positions')
def positions():
    return jsonify(bot.get_open_positions())

@app.route('/stats')
def stats():
    return jsonify(bot.get_performance_stats())

@app.route('/history')
def history():
    return jsonify(bot.get_trade_history())

@app.route('/entry-conditions')
def entry_conditions():
    return jsonify(bot.get_entry_conditions())

# Add JavaScript endpoint for stopping the bot
@app.route('/api/stop', methods=['POST'])
def api_stop_bot():
    global bot_running
    bot_running = False
    return jsonify({"status": "success", "message": "Bot stopped successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
