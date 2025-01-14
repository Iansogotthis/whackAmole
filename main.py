
from flask import Flask
import os
import socket

app = Flask(__name__)

@app.route('/')
def index():
    return 'Flask server is running successfully'

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('0.0.0.0', port)) == 0

def find_available_port(start_port=5000, max_port=9000):
    port = start_port
    while port < max_port:
        if not is_port_in_use(port):
            return port
        port += 1
    return None

if __name__ == '__main__':
    port = find_available_port()
    if port:
        print(f"Starting server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        print("No available ports found between 5000-9000")
