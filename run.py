import json
import queue
import subprocess
from datetime import datetime

from flask import Flask, jsonify, request, Response, render_template, session
from threading import Thread
from pyngrok import ngrok
import os
from flask_socketio import SocketIO, emit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import time
import os
import queue

from localtunnel.app import start_localtunnel
import random

from flask import Flask, render_template, request, jsonify
import razorpay
import json
import os

from flask import Flask, render_template, jsonify, request
import razorpay
import os


# Set your Ngrok authtoken
ngrok.set_auth_token("2oI8ESkeGy20xKfVfxRjBWwQZKI_4DpKDP2Zh4UvzAWaU3Nq4")  # Replace with your actual token



RAZORPAY_KEY_ID = 'rzp_test_HehTNX7pWaWjWE'  # Replace with your Razorpay Key ID
RAZORPAY_KEY_SECRET = '6IFp2MbgGkstIffuQV52b0Dl'  # Replace with your Razorpay Key Secret
# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


# Define the Flask application
app = Flask(__name__)

app.secret_key = os.urandom(24)

socketio = SocketIO(app)

alert_queue = queue.Queue()  # Queue to hold alert messages for real-time updates

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self):

        self.previous_filename = None
        self.previous_timestamp = time.time()

    '''def on_modified(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path).replace('.json', '')

        # Get the current time
        current_time = time.time()

        # Check if this is the same file and if 5 seconds have passed since the last modification
        print(current_time - self.previous_timestamp)
        #if (current_time - self.previous_timestamp > 0.0):

        print("new file is  newly updated ")
        self.previous_filename = filename
        self.previous_timestamp = current_time
        with open(event.src_path, 'r') as file:
            file_content = file.read()
            socketio.emit('file_update', {'filename': filename, 'content': file_content})
            print('file modified', {'filename': filename, 'content': file_content})'''








def on_created(self, event):
    if event.is_directory:
        return



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


@app.route('/order_accept', methods=['POST'])
def order_accept():
    data = request.get_json()  # Get the JSON data from the POST request
    table_name = data.get("table_name", "default_table")  # Optional table name from JSON data

    socketio.emit('order_accept', {'filename': table_name})
    print("order rejecteed sending data to table")

    return jsonify({"status": "success", "message": f"order accepted for {table_name}"}), 200


@app.route('/order_reject', methods=['POST'])
def order_reject():
    data = request.get_json()  # Get the JSON data from the POST request
    table_name = data.get("table_name", "default_table")  # Optional table name from JSON data

    socketio.emit('order_reject', {'filename': table_name})
    print("order rejecteed sending data to table")

    return jsonify({"status": "success", "message": f"order rejecteed for {table_name}"}), 200


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

        with open(file_path, 'r') as file:
            file_content = file.read()
            socketio.emit('file_update', {'filename': table_name, 'content': file_content})
            print('file modified', {'filename': table_name, 'content': file_content})

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

@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/data')
def data():
    # Read the JSON file
    with open('templates/menu.json') as json_file:
        data = json.load(json_file)  # Load the JSON data from the file
        print(data)
    return jsonify(data)  # Return the data as a JSON response


@app.route('/check-order-status', methods=['POST'])
def handle_rejection_reason():
    data = request.get_json()
    reason = data.get('reason', None)

    if reason:
        session['rejection_reason'] = data  # Store the reason in the session
        return jsonify({'status': 'success', 'message': 'Rejection reason received'}), 200
        print("order rejected ",reason)

@app.route('/table_order_status')
def third_page():
    rejection_reason = session.get('rejection_reason', None)
    return jsonify(rejection_reason)


# Endpoint to receive the payment status from UPI gateway
@app.route('/payment-status', methods=['POST'])
def payment_status():
    # Extract data from the request
    payment_response = request.form.to_dict()  # This will be a dictionary of form data

    # Log the response (for debugging)
    print("Received payment response:", payment_response)

    # Assuming the response contains these fields:
    # - payment_status: success/failure
    # - transaction_id: ID of the transaction
    # - amount: amount paid
    # - merchant_reference: reference number for the transaction

    # Extracting data
    payment_status = payment_response.get('payment_status')  # Replace with actual field name from UPI response
    transaction_id = payment_response.get('transaction_id')
    amount = payment_response.get('amount')
    merchant_reference = payment_response.get('merchant_reference')

    # Validate or process the payment status
    if payment_status == 'success':
        # If payment was successful
        # Perform necessary actions, like updating the order status, etc.
        response_message = "Payment successful"
    else:
        # If payment failed
        response_message = "Payment failed"

    # You can return a success message or any other response as needed
    return jsonify({
        'status': 'OK',
        'message': response_message,
        'transaction_id': transaction_id,
        'amount': amount,
        'merchant_reference': merchant_reference
    })

@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.get_json()  # Parse the request body as JSON
    amount = int(data['amount'])  # The amount will be in paise (50000 for ₹500)

    #amount = 50000  # Amount in paise (INR 500.00)
    currency = 'INR'
    receipt = "receipt#" + str(random.randint(1000, 9999))

    order = razorpay_client.order.create(dict(
        amount=amount,
        currency=currency,
        receipt=receipt,
        payment_capture=1  # Automatically capture the payment
    ))

    return jsonify({
        'id': order['id'],
        'amount': order['amount']
    })

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    payment_id = request.form['razorpay_payment_id']
    order_id = request.form['razorpay_order_id']
    signature = request.form['razorpay_signature']

    payment_data = {
        'razorpay_order_id': order_id,
        'razorpay_payment_id': payment_id,
        'razorpay_signature': signature
    }

    # Verify the payment signature using Razorpay's utility method
    try:
        razorpay_client.utility.verify_payment_signature(payment_data)
        return jsonify({'status': 'Payment successful'})
    except razorpay.errors.SignatureVerificationError:
        return jsonify({'status': 'Payment verification failed'})

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
        app.run( host='0.0.0.0',port=port_number)
    finally:
        # Terminate LocalTunnel when the app stops
        lt_process.terminate()




def monitor_localtunnel():
    """
    Monitors the LocalTunnel process and restarts it if it disconnects.
    """
    while True:
        # Start the LocalTunnel process
        process = run_flask()

        # Continuously check the status
        try:
            while True:
                # Check if process has terminated
                if process.poll() is not None:
                    print("LocalTunnel disconnected. Attempting to reconnect...")
                    time.sleep(5)  # Wait a few seconds before restarting
                    break  # Exit inner loop to restart process

                # Read output for debugging (optional)
                output = process.stdout.readline()
                if output:
                    print(output.decode().strip())

                time.sleep(1)  # Avoid tight looping

        except KeyboardInterrupt:
            print("Process interrupted. Exiting...")
            process.terminate()
            break


if __name__ == '__main__':
    # Start Ngrok
    # Start the Flask app in a separate thread first
    thread = Thread(target=monitor_localtunnel)
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

    socketio.run(app, host='0.0.0.0', port=5000)