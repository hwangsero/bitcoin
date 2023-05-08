import json
import requests
import time
import websocket 
from confluent_kafka import Producer

class KafkaProducer():
    def __init__(self, bootstrap_servers):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def delivery_report(self, err, msg) -> None:
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def send_message_to_kafka(self, ws, message) -> None:
        self.producer.poll(0)
        self.producer.produce("coin-prices", message, callback=self.delivery_report)
        self.producer.flush()

def main() -> None:
    websocket.enableTrace(True)
    kafka_producer = KafkaProducer('192.168.127.38:9092')
    assets = "bitcoin,ethereum,tether,binance-coin,usd-coin,xrp,cardano,dogecoin,polygon,solana"
    ws = websocket.WebSocketApp(f"wss://ws.coincap.io/prices?assets={assets}",
                                on_message = kafka_producer.send_message_to_kafka)
    ws.run_forever()

if __name__ == "__main__":
    main()
