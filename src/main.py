import os
import subprocess
import speedtest
import time
import csv
import logging
from logging.handlers import TimedRotatingFileHandler
from configparser import ConfigParser
from datetime import datetime

config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini')
config = ConfigParser(interpolation=None)
config.read(config_path)

log_level = config['logging']['level']
log_format = config['logging']['format']
log_handler = TimedRotatingFileHandler("network_monitor.log", when="midnight", interval=1)
log_handler.suffix = "%Y-%m-%d"

logging.basicConfig(
    handlers=[log_handler],
    level=getattr(logging, log_level.upper(), logging.INFO),
    format=log_format
)

gateway = config['network']['gateway']
interval = int(config['settings']['interval'])

csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'network_data.csv')
csv_columns = ['timestamp', 'download', 'upload', 'ping']

if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=csv_columns)
        writer.writeheader()

def measure_speed():
    st = speedtest.Speedtest()
    st.download()
    st.upload()
    results = st.results.dict()
    
    download_speed = results["download"] / 1_000_000  # to Mbps
    upload_speed = results["upload"] / 1_000_000
    logging.info(f"Download speed: {download_speed:.2f} Mbps, Upload speed: {upload_speed:.2f} Mbps")
    return download_speed, upload_speed

def ping_gateway(gateway=gateway):
    response = subprocess.run(["ping", "-n", "1", gateway], capture_output=True, text=True)
    # Change language, based on locale
    if "tiempo=" in response.stdout:
        time_ms = response.stdout.split("tiempo=")[1].split("ms")[0].strip()
        logging.info(f"Ping to {gateway}: {time_ms} ms")
        return float(time_ms)
    else:
        logging.warning(f"Ping to {gateway} failed")
        return None

def save_to_csv(download, upload, ping):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=csv_columns)
        writer.writerow({'timestamp': timestamp, 'download': download, 'upload': upload, 'ping': ping})

def send_logs_to_server():
    # to be continued...
    # https://docs.python.org/3/library/syslog.html
    pass

def main():
    while True:
        try:
            download_speed, upload_speed = measure_speed()
            ping_time = ping_gateway()

            save_to_csv(download_speed, upload_speed, ping_time)
            # send_logs_to_server("network_monitor.log")
        
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    main()
