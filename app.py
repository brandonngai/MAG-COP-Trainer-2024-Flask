from flask import Flask, render_template, request, jsonify
import os
import random
import base64
import pandas as pd
from itertools import compress
import json

# Initialization
app = Flask(__name__)

currentDir = os.getcwd()
imgDir = os.path.join(currentDir, "Static\\Images")
imageList = os.listdir(imgDir)
imageList.remove('welcome.png')

# Create Solution Dataframe
event_list = []
value_list = []
group_list = []
filename_list = []
skillnumber_list = []

global data, full_data
for filename in imageList:
    temp = filename[:-4]
    temp = temp.split('_')
    event_list.append(temp[0])
    value_list.append(temp[1])
    group_list.append(temp[2])
    skillnumber_list.append(temp[3])
    filename_list.append(filename)

data = pd.DataFrame({
    'Event': event_list,
    'Value': value_list,
    'EG': group_list,
    'Skill_Number': skillnumber_list,
    'Filename': filename_list
})
full_data = data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_image', methods=['POST'])
def get_image():
    app.logger.info("get_image route called")
    data = request.get_json()
    app.logger.info(f"Received data: {data}")

    if data['welcome_image_flag'] == 1:
        app.logger.info("First load, returning welcome image")
        with open(os.path.join(imgDir, 'welcome.png'), 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode()
        return jsonify({'image': f"data:image/png;base64,{encoded_image}", 'solution': ''})


    else:
        # Filter events based on the selected buttons
        event_filter_state = [x == "btn-success" for x in data['event_filter']]
        event_filter = list(compress(["FX", "PH", "SR", "PB", "HB"], event_filter_state))
        app.logger.info(f"Event filter: {event_filter}")

        # If event_filter is empty, select all events
        if not event_filter:
            app.logger.info("No events selected, using all events")
            filtered_data = full_data  # No filter applied
        else:
            # Otherwise filter based on the active events
            app.logger.info("Filtering data based on selected events")
            filtered_data = full_data[full_data["Event"].isin(event_filter)].reset_index(drop=True)

        app.logger.info(f"Filtered data shape: {filtered_data.shape}")

        if filtered_data.empty:
            app.logger.info("No skills found for the selected events")
            # If no data matches the filters, return a message
            return jsonify({'image': '', 'message': 'No skills found for the selected events', 'solution': None})

        # If there is data, select a random image
        i = random.randrange(0, filtered_data.shape[0])
        img_file = filtered_data["Filename"][i]
        solution = filtered_data['Value'][i]
        app.logger.info(f"Selected image: {img_file}, Solution: {solution}")

        with open(os.path.join(imgDir, img_file), 'rb') as f:
            encoded_image = base64.b64encode(f.read()).decode()

        # Map skill value to index (A-J -> 0-9)
        value_map_dict = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7, "I": 8, "J": 9}
        solution_index = value_map_dict[solution]

        app.logger.info("Returning image and solution")
        return jsonify({'image': f"data:image/png;base64,{encoded_image}", 'solution': solution_index})
    
@app.route('/check_solution', methods=['POST'])
def check_solution():
    data = request.get_json()
    user_guess = data['guess']
    solution = data['solution']

    if user_guess == solution:
        return jsonify({'correct': True})
    else:
        return jsonify({'correct': False})

if __name__ == '__main__':
    app.run(host="0.0.0.0")