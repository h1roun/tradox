"""
Trading Bot Configuration

This file contains the configuration parameters for the trading strategy.
Modify these values to adjust your trading strategy without changing the core code.
"""

# Trading parameters
TRADING_CONFIG = {
    # Position sizing
    'usdt_per_trade': 100,        # Amount in USDT to use per trade
    'max_positions': 2,           # Maximum number of simultaneous positions
    
    # Profit targets and stop loss
    'take_profit_pct': 2.0,       # Take profit percentage (e.g., 2.0 = 2%)
    'stop_loss_pct': -1.0,        # Stop loss percentage (e.g., -1.0 = -1%)
    
    # Timeframes
    'timeframe': '5m',            # Candle timeframe for analysis
    
    # Technical indicators parameters
    'rsi_period': 14,             # Period for RSI calculation
    'rsi_oversold': 30,           # Oversold threshold for RSI
    'rsi_overbought': 70,         # Overbought threshold for RSI
    'macd_fast': 12,              # Fast period for MACD
    'macd_slow': 26,              # Slow period for MACD
    'macd_signal': 9,             # Signal period for MACD
    
    # Scanning interval
    'scan_interval': 30           # Seconds between market scans
}

# Mapping from config timeframe to Binance API timeframe
TIMEFRAME_MAP = {
    '1m': '1m',
    '3m': '3m',
    '5m': '5m',
    '15m': '15m'
}