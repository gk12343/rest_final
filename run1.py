import json
import queue

from flask import Flask, jsonify,request,Response, render_template
from threading import Thread
from pyngrok import ngrok
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import os
import queue

from localtunnel.app import start_localtunnel

# Set your Ngrok authtoken
ngrok.set_auth_token("2oI8ESkeGy20xKfVfxRjBWwQZKI_4DpKDP2Zh4UvzAWaU3Nq4")  # Replace with your actual token

# Define the Flask application
app = Flask(__name__)

alert_queue = queue.Queue()  # Queue to hold alert messages for real-time updates

class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            filename = os.path.splitext(os.path.basename(event.src_path))[0]
            alert = f"Alert: {filename} has added new item in previous order"
            print(alert)
            alert_queue.put(alert)

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.splitext(os.path.basename(event.src_path))[0]
            alert = f"Alert: {filename}   placed new order "
            print(alert)
            alert_queue.put(alert)


def start_observer(path_to_watch):
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

@app.route('/alerts')
def alerts():
    def generate():
        while True:
            try:
                alert = alert_queue.get(timeout=10)  # Wait for a new alert
                yield f"data: {alert}\n\n"
            except queue.Empty:
                continue  # Continue waiting for new alerts
    return Response(generate(), mimetype='text/event-stream')






@app.route('/save_json', methods=['POST'])
def save_json():
    data = request.get_json()  # Get the JSON data from the POST request
    table_name = data.get("table_name", "default_table")  # Optional table name from JSON data
    saved_order = data.get("order_data", {})  # Get the order data

    # Define the filename based on the table name
    filename = f"{table_name}.json"
    file_path = os.path.join(os.getcwd(), filename)  # Save in the current directory

    # Save data to a JSON file
    try:
        with open(file_path, 'w') as json_file:
            json.dump(saved_order, json_file, indent=2)  # Pretty print with 2 spaces
        return jsonify({"status": "success", "message": f"Data saved to {filename}"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/table_book')
def table():
    return render_template('local_global_server_table_booking.html')

@app.route('/')
def home():
    return render_template('frontpage.html')

@app.route('/backendpage.html')
def home1():
    return render_template('backendpage.html')



@app.route('/data')
def data():
    # Read the JSON file
    with open('templates/menu.json') as json_file:
        data = json.load(json_file)  # Load the JSON data from the file
        print(data)
    return jsonify(data)  # Return the data as a JSON response




# Function to run the Flask app
def run_flask():
    # Set up ngrok tunnel
    # Set your desired subdomain and port
    subdomain_name = "hotelgk"  # Replace with your chosen subdomain
    port_number = 5000  # Flask app will run on this port

    # Start LocalTunnel
    lt_process = start_localtunnel(port_number, subdomain_name)

    # Start the Flask app
    try:
        app.run(port=port_number)
    finally:
        # Terminate LocalTunnel when the app stops
        lt_process.terminate()

if __name__ == '__main__':
    # Start Ngrok
    # Start the Flask app in a separate thread first
    thread = Thread(target=run_flask)
    thread.start()

    # Give Flask a moment to start up
    time.sleep(1)






    # Specify the directory to watch
    path_to_watch = os.path.join(os.getcwd() )  # Replace with your directory path
    os.makedirs(path_to_watch, exist_ok=True)  # Create directory if it doesn't exist

    print("Monitoring directory:", path_to_watch)

    # Start the observer in a separate thread
    observer_thread = threading.Thread(target=start_observer, args=(path_to_watch,))
    observer_thread.daemon = True
    observer_thread.start()

    # Keep the main thread alive
    thread.join()
