from w1thermsensor import W1ThermSensor, SensorNotReadyError
from flask import Flask, render_template, send_file, jsonify
import datetime
import thread
import time

LOGGING_INTERVAL_SEC = 5
LOG_FILE_NAME = "temperature_data.csv"

app = Flask(__name__)
logging_is_enabled = True


def write_data_csv_header():
    #Write CSV data header
    with open(LOG_FILE_NAME, 'w+') as f:
        f.write("timestamp,sensor_id,temperature\n")


def get_logged_sensor_data():
    sensor_data = {}
    with open(LOG_FILE_NAME, 'r') as f:
        for line_no, line in enumerate(f.readlines()):
            if line_no == 0:
                continue
            ts,sensor_id,temp = line.strip().split(',')
            if not sensor_id in sensor_data:
                sensor_data[sensor_id] = []
            sensor_data[sensor_id].append((ts, temp))

    return sensor_data

write_data_csv_header()
recent_temp_data = {}
def data_logger_thread():
    while True:
        if logging_is_enabled:
            sensors = W1ThermSensor.get_available_sensors()
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            sensor_data = []
            for sensor in sensors:
                try:
                    temperature = sensor.get_temperature()
                    sensor_data.append((sensor.id, temperature))
                    recent_temp_data[sensor.id] = {
                            "timestamp": timestamp,
                            "temperature": temperature
                        }
                except SensorNotReadyError:
                    print "Sensor " + str(sensor.id) + " is not ready\n"

            with open(LOG_FILE_NAME, 'a') as f:
                for data in sensor_data:
                    f.write('{ts},{id},{temp}\n'.format(ts=timestamp, id=data[0], temp=data[1]))

        time.sleep(LOGGING_INTERVAL_SEC)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    return jsonify(recent_temp_data)

@app.route('/data_csv')
def get_data_csv():
    return send_file(LOG_FILE_NAME,
                     mimetype='text/csv',
                     attachment_filename='temp_data.csv',
                     as_attachment=True)

@app.route('/data_json')
def get_data_json():
    data = get_logged_sensor_data()
    return jsonify(data)

try:
   thread.start_new_thread( data_logger_thread, ())
except:
   print "Error: unable to start data logger thread"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
