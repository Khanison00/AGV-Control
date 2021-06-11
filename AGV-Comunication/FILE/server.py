from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage

app = Flask(__name__)

@app.route('/upload')
def _upload_file():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      f.save(f"upload/{secure_filename(f.filename)}")
      print(f)
      return 'file uploaded successfully'

@app.route('/')
def index():
   return render_template('index.html')


# http://43.72.228.147/ekanban/pages/supply_monitor.php
		
if __name__ == '__main__':
   app.run(debug = True)