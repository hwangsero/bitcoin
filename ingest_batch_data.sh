#!/bin/bash

# activate vertualenv
source .venv/bin/activate

# ingest market data
python ingest_data/ingest_coin_markets.py

# processing market data
python processing_data/coin_market_processor.py

# deactivate vertualenv
deactivate


