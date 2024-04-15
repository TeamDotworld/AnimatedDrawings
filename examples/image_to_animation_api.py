from flask import Flask, request, jsonify
from flask_cors import CORS

from werkzeug.utils import secure_filename
from pathlib import Path
import logging
from pkg_resources import resource_filename

from image_to_annotations import image_to_annotations
from annotations_to_animation import annotations_to_animation
import sys
import random, string


app = Flask(__name__)
CORS(app)

# Configure the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def image_to_animation(img_fn: str, char_anno_dir: str, motion_cfg_fn: str, retarget_cfg_fn: str):
    try:
        """
        Given the image located at img_fn, create annotation files needed for animation.
        Then create animation from those animations and motion cfg and retarget cfg.
        """
        # create the annotations
        image_to_annotations(img_fn, char_anno_dir)
        print(f'Created annotations at {char_anno_dir}')
        print(f'Creating animation using {motion_cfg_fn} and {retarget_cfg_fn}')

        # create the animation
        controller =  annotations_to_animation(char_anno_dir, motion_cfg_fn, retarget_cfg_fn)
        controller._is_run_over()
        print(f'Created animation at {char_anno_dir}')
        print(f'Done!')
        return True
    except Exception as e:
        print(f'Error creating animation: {e}')
        return False

@app.route('/animate', methods=['POST'])
def animate():
    print(request.files)
    if 'image' not in request.files:
        return jsonify({'status': False, 'error': 'No image part in the request'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'status': False, 'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = Path(app.config['UPLOAD_FOLDER']) / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)
        file.save(str(save_path))

        # create a random directory to store the character annotations. use random string
        char_anno_dir = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(16))
        
        # char_anno_dir = request.form.get('char_anno_dir', 'dummy_out')
        motion_cfg_fn = resource_filename(__name__, 'config/motion/dab.yaml')
        retarget_cfg_fn = resource_filename(__name__, 'config/retarget/fair1_ppf.yaml')

        # Set up logging
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True, parents=True)
        logging.basicConfig(filename=f'{log_dir}/log.txt', level=logging.DEBUG)
        
        print(f'Sending image to animation: {save_path}, {char_anno_dir}, {motion_cfg_fn}, {retarget_cfg_fn}')
        # Assuming 'image_to_animation' function is defined elsewhere
        result = image_to_animation(str(save_path), char_anno_dir, "config/motion/dab.yaml", "config/retarget/fair1_ppf.yaml")
        

       # get only name of the file without extension. use path lib
        name = Path(filename).stem
       
       
        return jsonify({'status':result, 'data': {
            'id':char_anno_dir,
            'filename': name+".gif",
        }}), 200   
    
    return jsonify({'status': False, 'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5005)
