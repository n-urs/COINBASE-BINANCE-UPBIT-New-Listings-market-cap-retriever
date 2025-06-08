# Crypto Listings Market Cap Bot

A Telegram bot that monitors specified channels for cryptocurrency listing announcements (Binance futures/spot, and Upbit KRW listings) and automatically retrieves market capitalization data from CoinMarketCap and CoinGecko. Useful for tracking new listings and getting instant market cap insights.

## Features

* **Automated Monitoring**: Listens to predefined Telegram channels for listing announcements.
* **Ticker Extraction & Cleaning**: Parses and formats tickers for futures (`USDT` pairs), spot listings, and Upbit `KRW` listings.
* **Dual API Support**: Fetches market cap data from both CoinMarketCap and CoinGecko for redundancy.
* **Formatted Output**: Logs market cap values with thousands separators for readability.
* **Robust Logging**: Configurable logging at INFO level, with Telethon logs suppressed to WARNING.
* **Auto-Restart**: Gracefully handles errors and automatically restarts after a delay.

## Table of Contents

* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Configuration](#configuration)
* [Usage](#usage)
* [Environment Variables](#environment-variables)
* [Logging](#logging)
* [Contributing](#contributing)
* [License](#license)

## Prerequisites

* Python 3.7 or higher
* A Telegram account with API credentials
* A CoinMarketCap API key
* Internet access to reach the Telegram and Coin APIs

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/crypto-listings-bot.git
   cd crypto-listings-bot
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create a `.env` file** at the project root (or rename `config.env.example` to `config.env`):

   ```dotenv
   TG_API_ID=<your-telegram-api-id>
   TG_API_HASH=<your-telegram-api-hash>
   TG_PHONE=<your-telegram-phone-number>
   TARGET_CHAT=<chat-id-to-forward-or-log>
   CMC_API_KEY=<your-coinmarketcap-api-key>
   ```

2. **Update channel IDs** in `main.py` (if necessary):

   ```python
   CHANNELS = [
       -1001124574831,  # Coin listings announcements
       -1002307508514,  # test channel
       # add more channels as needed, add your own test channel
   ]
   ```

## Usage

Run the bot with:

```bash
python main.py
```

* The bot will connect to Telegram, listen for new messages in the specified channels, extract relevant tickers, fetch market cap data, and log the results.
* To stop the bot, press `Ctrl+C`.

## Environment Variables

| Variable      | Description                                          |
| ------------- | ---------------------------------------------------- |
| `TG_API_ID`   | Your Telegram API ID                                 |
| `TG_API_HASH` | Your Telegram API Hash                               |
| `TG_PHONE`    | Phone number associated with your Telegram account   |
| `TARGET_CHAT` | (Optional) Chat ID where processed messages are sent |
| `CMC_API_KEY` | Your CoinMarketCap Pro API key                       |

## Logging

* The bot uses Python's built-in `logging` module at the INFO level.
* Telethon logs are suppressed to WARNING to reduce noise.
* Format: timestamps, log level, and message content.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to open a pull request or issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
