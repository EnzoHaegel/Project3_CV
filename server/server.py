from flask import Flask, request
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
import os
import logging

app = Flask(__name__)
api = Api(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}

# Set up logging
logging.basicConfig(filename='server.log', level=logging.DEBUG)

def allowed_file(filename):
    """
    Check if the file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class UploadVideo(Resource):
    def post(self):
        """
        Upload a video to the server
        """
        print(request.files)
        if 'video' in request.files:
            file = request.files['video']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logging.info(f"Received file: {filename}")
                return {'message': f'video {filename} uploaded successfully'}
        logging.warning("No video in request or wrong format")
        return {'error': 'no video in request or wrong format'}, 400

api.add_resource(UploadVideo, '/upload_video')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
