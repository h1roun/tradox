# Tradox - Binance Crypto Trading Bot

A Flask-based trading bot that aims to scalp cryptocurrencies on Binance.

## Features

- Trades cryptocurrencies on Binance using real market data
- Simulates trades for testing before going live
- Limits to 2 open positions at a time
- Scans for entry opportunities using technical indicators
- Modern dark-themed web interface for monitoring and control
- Real-time performance tracking

## Setup Instructions

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/tradox.git
   cd tradox
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your Binance API keys:
   ```
   BINANCE_API_KEY=your_api_key_here
   BINANCE_API_SECRET=your_api_secret_here
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and go to `http://127.0.0.1:5000/`

## Usage

1. Enter the coin symbols you want to trade (e.g., BTC,ETH,SOL)
2. Click "Start Bot" to begin trading in simulation mode
3. Monitor open positions and performance in the interface
4. Click "Stop Bot" to halt trading
5. Once satisfied with the strategy, you can switch to live trading mode

## UI Features

The application features a modern dark-themed interface built with Bulma CSS that includes:

- Real-time position monitoring with profit/loss tracking
- Performance statistics dashboard
- Trade history log
- Easy mode switching between simulation and live trading

## Warning

- The goal of 10% profit per day is extremely ambitious and carries high risk
- Never trade with money you cannot afford to lose
- Be aware that trading cryptocurrencies carries significant risk

## Entry/Exit Strategy

The bot currently uses the following simplified strategy:
- **Entry**: RSI below 30 (oversold) and MACD histogram crossing above zero
- **Exit**: 2% profit target or 1% stop loss

You should modify the strategy to suit your risk tolerance and trading style.
