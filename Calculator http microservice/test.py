from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

WINDOW_SIZE = 10
STORED_NUMBERS = []

API_ENDPOINTS = {
    'p': 'http://20.244.56.144/test/primes',
    'f': 'http://20.244.56.144/test/fibonacci',
    'e': 'http://20.244.56.144/test/even',
    'r': 'http://20.244.56.144/test/random'
}

def fetch_numbers(number_id):
    if number_id not in API_ENDPOINTS:
        return []
    try:
        start_time = time.time()
        response = requests.get(API_ENDPOINTS[number_id], timeout=0.5)
        if time.time() - start_time > 0.5:
            return []
        return response.json().get('numbers', [])
    except (requests.RequestException, ValueError):
        return []

def update_window(new_numbers):
    global STORED_NUMBERS
    new_numbers = list(filter(lambda x: x not in STORED_NUMBERS, new_numbers))
    STORED_NUMBERS.extend(new_numbers)
    if len(STORED_NUMBERS) > WINDOW_SIZE:
        STORED_NUMBERS = STORED_NUMBERS[-WINDOW_SIZE:]

def calculate_average():
    if not STORED_NUMBERS:
        return 0.0
    return round(sum(STORED_NUMBERS) / len(STORED_NUMBERS), 2)

@app.route('/numbers/<string:number_id>', methods=['GET'])
def get_numbers(number_id):
    prev_state = STORED_NUMBERS.copy()
    numbers = fetch_numbers(number_id)
    update_window(numbers)
    curr_state = STORED_NUMBERS.copy()
    avg = calculate_average()

    return jsonify({
        "windowPrevState": prev_state,
        "windowCurrState": curr_state,
        "numbers": numbers,
        "avg": avg
    })

if __name__ == '__main__':
    app.run(port=9876)
