import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class MarketSimulator:
    """Simulates market data for testing trading strategies"""
    
    def __init__(self, initial_prices=None):
        """Initialize simulator with optional initial prices dictionary"""
        # Default prices if none provided
        self.prices = initial_prices or {
            'BTCUSDT': 30000.0,
            'ETHUSDT': 1800.0,
            'SOLUSDT': 45.0,
            'DOGEUSDT': 0.08,
            'BNBUSDT': 250.0,
            'XRPUSDT': 0.5,
            'ADAUSDT': 0.3,
            'DOTUSDT': 5.0,
            'AVAXUSDT': 15.0,
            'LINKUSDT': 8.0,
        }
        
        # Store historical data for each symbol
        self.history = {}
        for symbol in self.prices:
            self.history[symbol] = self._generate_initial_history(symbol)
            
        # Store volatility factors for different coins
        self.volatility = {
            'BTCUSDT': 0.015,
            'ETHUSDT': 0.02,
            'SOLUSDT': 0.035,
            'DOGEUSDT': 0.04,
            'BNBUSDT': 0.02,
            'XRPUSDT': 0.025,
            'ADAUSDT': 0.025,
            'DOTUSDT': 0.03,
            'AVAXUSDT': 0.035,
            'LINKUSDT': 0.03,
        }
        
        # Default volatility for any symbol not in the list
        self.default_volatility = 0.03
        
        # Overall market trend direction (-1 to 1)
        self.market_trend = 0.0
        
        # Track last update time
        self.last_update = datetime.now()
        
    def _generate_initial_history(self, symbol):
        """Generate initial price history for a symbol"""
        current_price = self.prices[symbol]
        volatility = self.volatility.get(symbol, self.default_volatility)
        
        # Generate 100 candles of historical data
        n_candles = 100
        
        # Start with current price and work backwards
        closes = [current_price]
        for _ in range(n_candles - 1):
            # Random walk with slight downward bias for realistic backfilling
            change = np.random.normal(0, volatility) - 0.0002
            prev_close = closes[-1] * (1 + change)
            closes.append(prev_close)
        
        closes.reverse()  # Put in chronological order
        
        # Create OHLC data
        data = []
        now = datetime.now()
        for i in range(n_candles):
            close = closes[i]
            # Generate realistic OHLC relationships
            high_factor = 1 + abs(np.random.normal(0, volatility * 0.5))
            low_factor = 1 - abs(np.random.normal(0, volatility * 0.5))
            open_factor = 1 + np.random.normal(0, volatility * 0.3)
            
            candle = {
                'open_time': int((now - timedelta(minutes=(n_candles - i) * 5)).timestamp() * 1000),
                'open': close * open_factor,
                'high': close * high_factor,
                'low': close * low_factor,
                'close': close,
                'volume': random.uniform(100, 10000),
                'close_time': int((now - timedelta(minutes=(n_candles - i - 1) * 5)).timestamp() * 1000),
                'quote_volume': random.uniform(1000000, 100000000),
                'trades': random.randint(500, 5000),
                'taker_buy_base': random.uniform(50, 5000),
                'taker_buy_quote': random.uniform(500000, 50000000),
                'ignore': 0
            }
            data.append(candle)
            
        return data
    
    def update_prices(self):
        """Update all prices based on time elapsed since last update"""
        now = datetime.now()
        seconds_elapsed = (now - self.last_update).total_seconds()
        
        # Don't update if less than 1 second has passed
        if seconds_elapsed < 1:
            return
            
        self.last_update = now
        
        # Occasionally shift the overall market trend
        if random.random() < 0.05:
            # Gradually shift market trend, bounded between -1 (bearish) and 1 (bullish)
            self.market_trend += np.random.normal(0, 0.2)
            self.market_trend = max(min(self.market_trend, 1), -1)
        
        # Update each symbol's price
        for symbol in self.prices:
            # Get symbol-specific volatility
            volatility = self.volatility.get(symbol, self.default_volatility)
            
            # Calculate price change (random + market trend influence)
            change_pct = np.random.normal(0, volatility) + (self.market_trend * volatility * 0.5)
            
            # Apply change
            self.prices[symbol] *= (1 + change_pct)
            
            # Update history every 5 minutes
            latest_candle_time = self.history[symbol][-1]['close_time'] / 1000
            if now.timestamp() - latest_candle_time >= 300:  # 5 minutes in seconds
                self._add_new_candle(symbol)
    
    def _add_new_candle(self, symbol):
        """Add a new candle to the historical data"""
        current_price = self.prices[symbol]
        volatility = self.volatility.get(symbol, self.default_volatility)
        
        last_candle = self.history[symbol][-1]
        new_open_time = last_candle['close_time']
        new_close_time = new_open_time + (5 * 60 * 1000)  # 5 minutes in milliseconds
        
        # Generate OHLC data
        high_factor = 1 + abs(np.random.normal(0, volatility * 0.5))
        low_factor = 1 - abs(np.random.normal(0, volatility * 0.5))
        
        new_candle = {
            'open_time': new_open_time,
            'open': last_candle['close'],
            'high': current_price * high_factor,
            'low': current_price * low_factor,
            'close': current_price,
            'volume': random.uniform(100, 10000),
            'close_time': new_close_time,
            'quote_volume': random.uniform(1000000, 100000000),
            'trades': random.randint(500, 5000),
            'taker_buy_base': random.uniform(50, 5000),
            'taker_buy_quote': random.uniform(500000, 50000000),
            'ignore': 0
        }
        
        self.history[symbol].append(new_candle)
    
    def get_price(self, symbol):
        """Get current price for a symbol"""
        self.update_prices()
        
        # If symbol not in our list, create it
        if symbol not in self.prices:
            self.prices[symbol] = 1.0  # Default starting price
            self.volatility[symbol] = self.default_volatility
            self.history[symbol] = self._generate_initial_history(symbol)
            
        return self.prices[symbol]
    
    def get_ticker(self, symbol):
        """Simulate Binance ticker response"""
        price = self.get_price(symbol)
        
        return {
            'symbol': symbol,
            'priceChange': str(price * np.random.normal(0, 0.01)),
            'priceChangePercent': str(np.random.normal(0, 1)),
            'weightedAvgPrice': str(price * random.uniform(0.995, 1.005)),
            'prevClosePrice': str(price * random.uniform(0.99, 1.01)),
            'lastPrice': str(price),
            'lastQty': str(random.uniform(0.1, 10)),
            'bidPrice': str(price * 0.999),
            'bidQty': str(random.uniform(1, 10)),
            'askPrice': str(price * 1.001),
            'askQty': str(random.uniform(1, 10))
        }
    
    def get_klines(self, symbol, interval, limit):
        """Simulate Binance klines response"""
        self.update_prices()
        
        # If symbol not in our list, create it
        if symbol not in self.history:
            self.prices[symbol] = 1.0  # Default starting price
            self.volatility[symbol] = self.default_volatility
            self.history[symbol] = self._generate_initial_history(symbol)
        
        # Return last 'limit' candles
        klines = self.history[symbol][-limit:]
        
        # Format like Binance response (list of lists)
        formatted_klines = []
        for candle in klines:
            formatted = [
                candle['open_time'],
                str(candle['open']),
                str(candle['high']),
                str(candle['low']),
                str(candle['close']),
                str(candle['volume']),
                candle['close_time'],
                str(candle['quote_volume']),
                candle['trades'],
                str(candle['taker_buy_base']),
                str(candle['taker_buy_quote']),
                str(candle['ignore'])
            ]
            formatted_klines.append(formatted)
            
        return formatted_klines
