from flask import Flask,render_template
import json
app = Flask(__name__)

@app.route('/')
def home():
	jsdata = json.load(open('static/test.json'))
	return render_template('index.html',**locals())

if __name__ == '__main__':
    app.run()