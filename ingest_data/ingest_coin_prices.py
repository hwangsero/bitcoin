import json
import requests
import websocket 
from confluent_kafka import Producer
import time

def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

producer = Producer({'bootstrap.servers': '192.168.127.38:9092'})

def on_message(ws, message):
    #json_data = json.dumps(message)
    json_data = message
    producer.poll(0)
    producer.produce("coin-prices", json_data, callback=delivery_report)
    producer.flush()
    #time.sleep(1)

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://ws.coincap.io/prices?assets=bitcoin,ethereum,monero,litecoi",
                                on_message = on_message)
    ws.run_forever()
