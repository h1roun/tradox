from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import numpy as np
import time
from datetime import datetime

class TradingBot:
    def __init__(self, api_key, api_secret, simulation_mode=True):
        # Initialize Binance client (needed for both modes to get real market data)
        self.client = Client(api_key, api_secret)
        
        # Store simulation mode flag
        self.simulation_mode = simulation_mode
        
        if simulation_mode:
            print("Bot initialized in SIMULATION mode with REAL market data. No real trades will be executed.")
        else:
            print("Bot initialized in LIVE mode. Real trades will be executed!")
        
        self.coins = []
        self.open_positions = {}  # Tracking open positions
        self.max_positions = 2
        self.daily_goal = 10  # 10% daily goal
        
        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit_pct = 0.0
        self.trade_history = []
        
        # Verify connection to Binance
        try:
            self.client.ping()
            print("Successfully connected to Binance API!")
        except Exception as e:
            print(f"Warning: Could not connect to Binance API: {e}")
        
    def set_coins(self, coins):
        """Set list of coins to trade"""
        self.coins = coins
        print(f"Bot configured to trade: {', '.join(self.coins)}")
    
    def scan_market(self):
        """Scan market for trading opportunities"""
        if len(self.open_positions) >= self.max_positions:
            print(f"Maximum positions ({self.max_positions}) reached. Skipping scan.")
            return
        
        for coin in self.coins:
            symbol = f"{coin}USDT"
            
            # Skip if we already have a position for this coin
            if symbol in self.open_positions:
                continue
                
            try:
                # Check if we should enter a position
                if self._check_entry_conditions(symbol):
                    self._enter_position(symbol)
                    
                    # Stop scanning if max positions reached
                    if len(self.open_positions) >= self.max_positions:
                        break
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")
        
        # Check existing positions for exit
        self._check_exit_conditions()
    
    def _check_entry_conditions(self, symbol):
        """Check if entry conditions are met"""
        # Get historical data from Binance
        klines = self.client.get_klines(
            symbol=symbol, 
            interval=Client.KLINE_INTERVAL_5MINUTE,
            limit=100
        )
        
        # Convert to dataframe
        df = pd.DataFrame(klines, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        # Convert string values to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Calculate indicators
        # 1. RSI (Relative Strength Index)
        df['price_change'] = df['close'].diff()
        df['gain'] = df['price_change'].clip(lower=0)
        df['loss'] = -df['price_change'].clip(upper=0)
        df['avg_gain'] = df['gain'].rolling(window=14).mean()
        df['avg_loss'] = df['loss'].rolling(window=14).mean()
        df['rs'] = df['avg_gain'] / df['avg_loss'].replace(0, 0.001)
        df['rsi'] = 100 - (100 / (1 + df['rs']))
        
        # 2. MACD (Moving Average Convergence Divergence)
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['signal']
        
        # Get latest values
        current_rsi = df['rsi'].iloc[-1]
        macd_histogram = df['macd_histogram'].iloc[-1]
        prev_macd_histogram = df['macd_histogram'].iloc[-2]
        
        # Entry condition: RSI < 30 (oversold) and MACD histogram turning positive
        entry_condition = (
            current_rsi < 30 and 
            macd_histogram > 0 and 
            prev_macd_histogram < 0
        )
        
        # Print debug info when entry condition is met
        if entry_condition:
            print(f"Entry signal for {symbol}: RSI={current_rsi:.2f}, MACD Hist={macd_histogram:.6f}")
        
        return entry_condition
    
    def _check_exit_conditions(self):
        """Check if any positions should be closed"""
        positions_to_close = []
        
        for symbol, position in self.open_positions.items():
            entry_price = position['entry_price']
            
            try:
                # Get current price
                ticker = self.client.get_ticker(symbol=symbol)
                current_price = float(ticker['lastPrice'])
                
                # Calculate profit percentage
                profit_pct = ((current_price / entry_price) - 1) * 100
                
                # Exit if target reached (2% profit) or stop loss hit (-1%)
                if profit_pct >= 2 or profit_pct <= -1:
                    self._exit_position(symbol, current_price, profit_pct)
                    positions_to_close.append(symbol)
            except Exception as e:
                print(f"Error checking exit conditions for {symbol}: {e}")
        
        # Remove closed positions
        for symbol in positions_to_close:
            if symbol in self.open_positions:
                del self.open_positions[symbol]
    
    def _enter_position(self, symbol):
        """Enter a position for a symbol"""
        try:
            # Get current price from Binance
            ticker = self.client.get_ticker(symbol=symbol)
            price = float(ticker['lastPrice'])
            
            # Calculate position size (would be based on risk in real implementation)
            quantity = self._calculate_position_size(symbol, price)
            
            # For both simulation and real mode, track the position
            self.open_positions[symbol] = {
                'entry_price': price,
                'entry_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'quantity': quantity
            }
            
            mode_tag = "[SIMULATION]" if self.simulation_mode else "[LIVE]"
            print(f"{mode_tag} Entered position for {symbol} at {price}, quantity: {quantity}")
            
            # Only in LIVE mode, place a real order
            if not self.simulation_mode:
                # Real trade code would go here
                # self.client.order_market_buy(symbol=symbol, quantity=quantity)
                pass
            
        except Exception as e:
            print(f"Error entering position for {symbol}: {e}")
    
    def _calculate_position_size(self, symbol, price):
        """Calculate position size based on risk management"""
        # This is a simplified example
        # In a real implementation, you would consider:
        # - Account balance
        # - Risk per trade (e.g., 1% of portfolio)
        # - Stop loss distance
        
        # For now, we'll simulate a fixed amount of USDT per trade
        usdt_amount = 100  # $100 per trade
        
        # Get the minimum quantity precision for the symbol
        info = self.client.get_symbol_info(symbol)
        if info is None:
            # Default precision if symbol info not available
            precision = 5
        else:
            # Extract precision from LOT_SIZE filter
            lot_size = next((f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            if lot_size:
                precision = len(lot_size['stepSize'].rstrip('0').split('.')[1]) if '.' in lot_size['stepSize'] else 0
            else:
                precision = 5
                
        # Calculate and round quantity
        quantity = round(usdt_amount / price, precision)
        return quantity
    
    def _exit_position(self, symbol, price, profit_pct):
        """Exit a position for a symbol"""
        try:
            position = self.open_positions[symbol]
            entry_time = position['entry_time']
            entry_price = position['entry_price']
            quantity = position['quantity']
            
            mode_tag = "[SIMULATION]" if self.simulation_mode else "[LIVE]"
            print(f"{mode_tag} Exited position for {symbol} at {price}. "
                  f"Profit: {profit_pct:.2f}%. "
                  f"Entry: {entry_price}, Exit: {price}, "
                  f"Quantity: {quantity}, "
                  f"Held since: {entry_time}")
                  
            # Record trade for statistics
            self.total_trades += 1
            if profit_pct > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
                
            self.total_profit_pct += profit_pct
            
            # Calculate profit amount (in USDT)
            profit_amount = quantity * price - quantity * entry_price
            
            # Add to trade history
            self.trade_history.append({
                'symbol': symbol,
                'entry_price': entry_price,
                'exit_price': price,
                'quantity': quantity,
                'entry_time': entry_time,
                'exit_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'profit_pct': profit_pct,
                'profit_amount': profit_amount
            })
            
            # Only in LIVE mode, place a real order
            if not self.simulation_mode:
                # Real sell order would go here
                # self.client.order_market_sell(symbol=symbol, quantity=quantity)
                pass
            
        except Exception as e:
            print(f"Error exiting position for {symbol}: {e}")
    
    def get_open_positions(self):
        """Return list of open positions"""
        result = []
        for symbol, data in self.open_positions.items():
            try:
                # Get current price from Binance
                ticker = self.client.get_ticker(symbol=symbol)
                current_price = float(ticker['lastPrice'])
                
                # Calculate profit
                entry_price = data['entry_price']
                profit_pct = ((current_price / entry_price) - 1) * 100
                
                result.append({
                    'symbol': symbol,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'profit_pct': profit_pct,
                    'quantity': data['quantity'],
                    'entry_time': data['entry_time']
                })
            except Exception as e:
                print(f"Error getting data for {symbol}: {e}")
                
        return result
    
    def get_performance_stats(self):
        """Get trading performance statistics"""
        win_rate = 0
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
            
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit_pct': self.total_profit_pct,
            'average_profit_per_trade': self.total_profit_pct / max(1, self.total_trades)
        }
    
    def get_trade_history(self):
        """Return trade history"""
        return self.trade_history
