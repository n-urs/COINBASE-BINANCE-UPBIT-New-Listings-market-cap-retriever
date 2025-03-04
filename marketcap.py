import os
import logging
import re
import time
from decimal import Decimal as D
from datetime import datetime
from telethon import TelegramClient, events
from decimal import ROUND_DOWN # Import rounding mode
from dotenv import load_dotenv
import requests
import asyncio

# Load environment variables
load_dotenv('config.env')

# Telegram client setup
TG_API_ID = int(os.getenv('TG_API_ID'))
TG_API_HASH = os.getenv('TG_API_HASH')
TG_PHONE = os.getenv('TG_PHONE')
CHANNELS = [-1001124574831, -1002307508514]  # Update with correct channel IDs
TARGET_CHAT = os.getenv('TARGET_CHAT')  # Added to send messages to TARGET_CHAT

# CoinMarketCap API key
CMC_API_KEY = os.getenv('CMC_API_KEY')

# Configure logging to INFO level
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Add a helper function to format market cap values.
def format_market_cap(value):
    try:
        # Convert the value to a rounded integer and format with spaces as thousand separators.
        rounded_value = int(round(value))
        formatted_value = format(rounded_value, ",d").replace(",", " ")
        return formatted_value
    except Exception as e:
        logger.error(f"Error formatting market cap value: {e}")
        return str(value)

# Suppress Telethon INFO logs by setting the level to WARNING
logging.getLogger("telethon").setLevel(logging.WARNING)

# Initialize Telegram client with sequential updates set to False and a timeout of 30 seconds
client = TelegramClient('session_name', TG_API_ID, TG_API_HASH, sequential_updates=False, timeout=30)

# Function to clean up ticker for the "futures listing" message type
def clean_ticker_futures(ticker):
    # Remove "1M" prefix if present
    if ticker.startswith("1M"):
        ticker = ticker[2:]
    
    # Remove number prefix if divisible by 10
    if re.match(r'^(\d+)', ticker):
        number_prefix = int(re.match(r'^(\d+)', ticker).group(1))
        if number_prefix % 10 == 0:
            ticker = ticker[len(str(number_prefix)):]

    if ticker.endswith("USDT"):
        base_symbol = ticker[:-4]
        return f"{base_symbol}_USDT"
    return ticker

# Function to clean up ticker for the "spot listing" message type
def clean_ticker_spot(ticker):
    # Remove "1M" prefix if present
    if ticker.startswith("1M"):
        ticker = ticker[2:]
    
    # Remove number prefix if divisible by 10
    if re.match(r'^(\d+)', ticker):
        number_prefix = int(re.match(r'^(\d+)', ticker).group(1))
        if number_prefix % 10 == 0:
            ticker = ticker[len(str(number_prefix)):]

    return f"{ticker}_USDT"

# Function to get market cap from CoinMarketCap
def get_market_cap_from_cmc(symbol):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    parameters = {'symbol': symbol, 'convert': 'USD'}
    try:
        response = requests.get(url, headers=headers, params=parameters)
        if response.status_code == 200:
            data = response.json()
            return data['data'][symbol]['quote']['USD']['market_cap']
        else:
            logger.error(f"Error fetching market cap from CoinMarketCap: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exception fetching market cap from CoinMarketCap for {symbol}: {e}")
        return None

# Function to get contract address from CoinMarketCap
def get_contract_address_from_cmc(symbol):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    parameters = {'symbol': symbol}
    try:
        response = requests.get(url, headers=headers, params=parameters)
        if response.status_code == 200:
            data = response.json()
            contract_address = data['data'][symbol]['platform']['token_address']
            logger.info(f"Contract address for {symbol}: {contract_address}")
            return contract_address
        else:
            logger.error(f"Error fetching contract address from CoinMarketCap: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching contract address from CoinMarketCap for {symbol}: {e}")
        return None

# Function to get the full list of coins from CoinGecko
def get_coingecko_coin_list():
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching CoinGecko coin list: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching CoinGecko coin list: {e}")
        return None

# Function to get market cap from CoinGecko
def get_market_cap_from_coingecko(symbol, coin_list):
    try:
        coin_id = next((coin['id'] for coin in coin_list if coin['symbol'].lower() == symbol.lower()), None)
        if not coin_id:
            logger.error(f"CoinGecko ID for {symbol} not found.")
            return None

        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return D(data['market_data']['market_cap']['usd'])
        else:
            logger.error(f"Error fetching market cap from CoinGecko: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error fetching market cap from CoinGecko for {symbol}: {e}")
        return None

# Function to perform "market cap show" operations
async def marketcap_retrieve_operations(ticker):
    base_currency = ticker.split("_")[0]
            
    # Get market cap from CoinMarketCap
    market_cap_cmc = get_market_cap_from_cmc(base_currency)
    if market_cap_cmc is not None:
        formatted_cmc = format_market_cap(market_cap_cmc)
        logger.info(f"Market cap of {base_currency} from CoinMarketCap: {formatted_cmc} USD")
    else:
        logger.error(f"Failed to retrieve market cap from CoinMarketCap for {base_currency}")

    # Get market cap from CoinGecko
    coin_list = get_coingecko_coin_list()
    if coin_list:
        market_cap_gecko = get_market_cap_from_coingecko(base_currency, coin_list)
        if market_cap_gecko is not None:
            formatted_gecko = format_market_cap(market_cap_gecko)
            logger.info(f"Market cap of {base_currency} from CoinGecko: {formatted_gecko} USD")
        else:
            logger.error(f"Failed to retrieve market cap from CoinGecko for {base_currency}")

# Telegram message handler
async def handle_new_message(event):
    try:
        message = event.message.message
        logger.info(f"Received message: {message}")
        tickers = []
        start_time = time.time()

        # Check for the first message type: "futures will launch"
        if "futures will launch" in message.lower():
            logger.info("Detected 'BINANCE FUTURES' message")
            matches = re.findall(r'\b(\w+USDT)\b', message)
            if matches:
                logger.info(f"Extracted tickers: {matches}")
                for symbol in matches:
                    tickers.append(clean_ticker_futures(symbol))
            else:
                logger.info("No tickers found for 'BINANCE FUTURES' message")
        
        # Check for the first message type: "Coinbase Roadmap"
        if "coinbase roadmap" in message.lower():
            logger.info("Detected 'COINBASE ROADMAP' message")
            matches = re.findall(r'\((\w+)\)', message)
            if matches:
                logger.info(f"Extracted tickers: {matches}")
                for symbol in matches:
                    tickers.append(clean_ticker_spot(symbol))
            else:
                logger.info("No tickers found for 'COINBASE ROADMAP' message")

        # Check for the second message type: "will list"
        elif "will list" in message.lower():
            logger.info("Detected 'BINANCE SPOT' message")
            matches = re.findall(r'\((\w+)\)', message)
            if matches:
                logger.info(f"Extracted tickers: {matches}")
                for symbol in matches:
                    tickers.append(clean_ticker_spot(symbol))
            else:
                logger.info("No tickers found for 'BINANCE SPOT' message")

        # Check for the third message type: "UPBIT LISTING" and "KRW"
        elif "UPBIT LISTING" in message and "KRW" in message:
            logger.info("Detected 'UPBIT LISTING' message with 'KRW'")
            match = re.search(r'\((\w+)\)', message)
            if match:
                ticker = match.group(1)  # Extract the ticker from the first set of round brackets

                # Skip tickers that are BTC, USDC, USDT, or KRW
                if ticker in ["BTC", "USDC", "USDT", "KRW"]:
                    logger.info(f"Skipping ticker: {ticker}")
                else:
                    logger.info(f"Extracted ticker: {ticker}")
                    tickers.append(clean_ticker_spot(ticker))
            else:
                logger.info("No tickers found for 'UPBIT LISTING' message")
        
        # Call marketcap_retrieve_operations for each extracted ticker
        for ticker in tickers:
            logger.debug(f"About to process ticker: {ticker}")
            await marketcap_retrieve_operations(ticker)

    except Exception as e:
        logger.error(f"Error in message handler: {e}")

# Function to run the bot with a restart mechanism
async def run_bot():
    while True:
        try:
            await client.start(phone=TG_PHONE)
            @client.on(events.NewMessage(chats=CHANNELS))
            async def handler(event):
                await handle_new_message(event)
            logger.info("Bot is running. Waiting for messages...")
            await client.run_until_disconnected()
        except asyncio.CancelledError:
            logger.info("Shutdown requested. Disconnecting client...")
            await client.disconnect()
            break
        except Exception as e:
            logger.error(f"Error: {e}. Restarting in 30 seconds...")
            await asyncio.sleep(30)

# Main entry point
if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("Script interrupted by user (Ctrl + C). Stopping...")
