from flask import Flask,render_template,request
import json,requests
from bs4 import BeautifulSoup as bs
app = Flask(__name__)

current_engine = 'Wikipedia' # default search engine


@app.route('/')
def home():
	jsdata = json.load(open('static/test.json'))
	return render_template('index.html',**locals())

@app.route('/search', methods = ['POST'])
def get_post_javascript_search_data():
	jsdata = request.form['javascript_data']
	print("Got this: ",type(jsdata))
	return jsdata

@app.route('/switch', methods = ['POST'])
def get_post_javascript_switch_data():
	global current_engine
	jsdata = request.form['javascript_data']
	if jsdata != current_engine:
		current_engine = jsdata
	print("Current search engine is ", current_engine)
	return jsdata
	
if __name__ == '__main__':
    app.run()