from pyngrok import ngrok, conf
import time, json, sys

# Start tunnel
tunnel = ngrok.connect(8000, "http")
print(f"NGROK_URL:{tunnel.public_url}")
sys.stdout.flush()

# Keep alive
try:
    ngrok_process = ngrok.get_ngrok_process()
    ngrok_process.proc.wait()
except KeyboardInterrupt:
    ngrok.kill()
