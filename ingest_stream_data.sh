#!/bin/bash

# activate vertualenv
source .venv/bin/activate

# ingest market data
nohup python ingest_data/ingest_coin_prices.py &
nohup python ingest_data/ingest_coin_trades.py &

# processing market data
nohup python processing_data/coin_prices_processor.py &
nohup python processing_data/coin_trades_processor.py & 

# deactivate vertualenv
deactivate


