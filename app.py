from flask import Flask, render_template, request, send_from_directory, url_for, redirect
import os
import pandas as pd
import plotly
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the path to the upload and static folders
UPLOAD_FOLDER = 'uploads'
STATIC_FOLDER = 'static'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['STATIC_FOLDER'] = STATIC_FOLDER

ALLOWED_EXTENSIONS = {'mp4', 'csv'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'video' not in request.files or 'csv' not in request.files:
            return redirect(request.url)

        video_file = request.files['video']
        csv_file = request.files['csv']

        # Check if files are empty
        if video_file.filename == '' or csv_file.filename == '':
            return redirect(request.url)

        # Check if the file types are allowed
        if video_file and allowed_file(video_file.filename) and csv_file and allowed_file(csv_file.filename):
            # Save uploaded CSV file
            csv_path = os.path.join(
                app.config['UPLOAD_FOLDER'], csv_file.filename)
            csv_file.save(csv_path)

            # Move video file to the static folder
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(
                app.config['STATIC_FOLDER'], video_filename)
            video_file.save(video_path)

            # Process CSV file and generate Plotly graph as JSON
            graphJSON = display_graph(csv_path)

            # Render the HTML template with the video and Plotly JSON
            return render_template('index.html', video_path=url_for('static', filename=video_filename), graphJSON=graphJSON)

    return render_template('index.html', video_path=None, plotly_json=None)


def display_graph(file_path):
    # Read the CSV data into a pandas
    df = pd.read_csv(file_path, parse_dates=['time'])

    # Create a figure with subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.02)

    # Add traces for each subplot
    fig.add_trace(go.Scatter(x=df['time'], y=df['x_accel'], showlegend=False,
                  hoverinfo='x+y', name='Accelerometer X'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['y_accel'], showlegend=False,
                  hoverinfo='x+y', name='Accelerometer Y'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['z_accel'], showlegend=False,
                  hoverinfo='x+y', name='Accelerometer Z'), row=3, col=1)

    fig.update_xaxes(tickformat='%H:%M:%S.%L',
                     showticklabels=True, row=1, col=1)
    fig.update_xaxes(tickformat='%H:%M:%S.%L',
                     showticklabels=True, row=2, col=1)
    fig.update_xaxes(tickformat='%H:%M:%S.%L',
                     showticklabels=True, row=3, col=1)

    fig.update_xaxes(title_text="Timestamp", row=3, col=1, range=[
                     df['time'].min(), df.loc[1000, 'time']])
    fig.update_yaxes(title_text="Accelerometer X", row=1, col=1)
    fig.update_yaxes(title_text="Accelerometer Y", row=2, col=1)
    fig.update_yaxes(title_text="Accelerometer Z", row=3, col=1)

    fig.update_layout(
        height=1000,
        yaxis=dict(fixedrange=True),
        yaxis2=dict(fixedrange=True),
        yaxis3=dict(fixedrange=True),
        hovermode='closest',
        dragmode='pan',
        margin=dict(
            l=50,
            r=50,
            t=50,
            b=50
        ),
    )

    line_shape = {
        'type': 'line',
        'xref': 'x',
        'yref': 'paper',
        'x0': df['time'].min(),
        'x1': df['time'].min(),
        'y0': 0,
        'y1': 1,
        'line': {
            'color': 'red',
            'width': 2
        }
    }

    fig.update_layout(shapes=[line_shape])

    # Convert the figure to JSON
    graphJSON = plotly.io.to_json(fig)

    # Render the template with the plot
    return graphJSON


# Serve static files from the 'static' folder
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)
