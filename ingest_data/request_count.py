import websocket
import time
from datetime import datetime

message_count = 0
start_time = None

def on_message(ws, message):
    global message_count, start_time
    if start_time is None:
        start_time = time.time()

    message_count += 1
    elapsed_time = time.time() - start_time

    if elapsed_time >= 60.0:  # 60 seconds or 1 minute
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open('1.txt', 'a') as f:
            f.write(f"{current_time}, Messages per minute: {message_count}\n")

        message_count = 0  # reset the counter
        start_time = time.time()  # reset the timer

def main() -> None:
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.coincap.io/trades/binance",
                                on_message=on_message)
    ws.run_forever()

if __name__ == "__main__":
    main()
