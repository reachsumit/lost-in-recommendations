from flask import Flask,render_template,request,jsonify
import json,requests
from bs4 import BeautifulSoup as bs
app = Flask(__name__)

current_engine = 'Wikipedia' # default search engine
nodes_dict = {"nodes":[]}
links_dict = {"links":[]}
current_group_number = 0

def appends_nodes_and_links(parent_title,parent_url,recommendations):
    # clear any prior nodes information
    global nodes_dict, links_dict, current_group_number
    
    # dummy node
    node = {}
   
    # add all the recommendations in nodes dictionary
    current_group_number += 1
    for recomm in recommendations:
        node = {}
        node['name'] = recomm[0]
        node['url'] = recomm[1]
        node['group'] = current_group_number
        nodes_dict["nodes"].append(node)

    # find parent's index
    parent_index = nodes_dict['nodes'].index(dict([item for item in nodes_dict['nodes'] if item['url']==parent_url][0]))
    # connect all children with this parent index
    for idx, item in enumerate(nodes_dict['nodes']):
        if idx == parent_index:
            continue
        else:
            links_dict['links'].append({"source":idx,"target":parent_index})

def crate_nodes_and_links(parent_title,parent_url,recommendations):
    # clear any prior nodes information
    global nodes_dict, links_dict, current_group_number
    nodes_dict = {"nodes":[]}
    current_group_number = 0
    
    # dummy node
    node = {}
    
    # add parent node to root
    node['name'] = parent_title
    node['url'] = parent_url
    node['group'] = current_group_number

    nodes_dict["nodes"].append(node)

    # add all the recommendations in nodes dictionary
    current_group_number += 1
    for recomm in recommendations:
        node = {}
        node['name'] = recomm[0]
        node['url'] = recomm[1]
        node['group'] = current_group_number
        nodes_dict["nodes"].append(node)
    
    # clear any prior links information
    links_dict = {"links":[]}
    # find parent's index
    parent_index = nodes_dict['nodes'].index(dict([item for item in nodes_dict['nodes'] if item['url']==parent_url][0]))
    # connect all children with this parent index
    for idx, item in enumerate(nodes_dict['nodes']):
        if idx == parent_index:
            continue
        else:
            links_dict['links'].append({"source":idx,"target":parent_index})

def get_recommendations(soup):
    recommendations = []
    # find all see also links
    seeAll = soup.find_all(text="See also")
    # check if we are at the bottom one
    foundSeeAll = False
    for item in seeAll:
        # this see all is one of the main headlines
        if item.parent.attrs['class'][0]=='mw-headline':
            foundSeeAll = True
            break
    # return error if See Also link was not found
    if not foundSeeAll:
        return -1
    # get all the hyperlinks from following unordered list of references
    #linkslist = item.parent.parent.next_sibling.next_sibling.find_all('a')
    # fix some wiki urls have a weird box at the bottom
    sibling = item.parent.parent.next_sibling.next_sibling
    # make 7 attempts to jump that box
    for i in range(7):
        # check if recommendations list is found
        if not sibling.name=='ul':
            sibling = sibling.next_sibling.next_sibling
            continue
        break
    # recommendation list couldn't be retrieved in 7 attempts
    if i==7:
        return -1
    # get links out of recommendations list
    linkslist = sibling.find_all('a')
    # separate out the hyperlinks and titles
    for link in linkslist:
        # save recommendations
        recommendations.append([link.getText(),"https://en.wikipedia.org"+link.get('href')])
    return recommendations

def search_on_wiki(search):
    parent_title = ""
    parent_url = ""
    
    # search text on wikipedia
    resp = requests.get("https://en.wikipedia.org/w/index.php?search="+search)
    # if failed for some reason
    if resp.status_code != 200:
        print("Couldn't search the query on Wikipedia")
        return (-1,-1,-1)
    
    # make soup of the result
    soup= bs(resp.text,'lxml')
        
    # This is the direct article page
    if len(soup.select("li[id='ca-nstab-main']")):
        # save first heading as parent's title
        parent_title = soup.select("h1[id='firstHeading']")[0].getText()
        # save the search url as the parent's url
        #parent_url = "https://en.wikipedia.org/w/index.php?search="+search.replace(" ","+")
        # fix: save the redirected url
        parent_url = resp.url
        # find recommendations for this url
        retval = get_recommendations(soup)
    
    # This is the search results page
    elif len(soup.select("li[id='ca-nstab-special']")):
        # if search didn't resul a valid result, return error
        if not len(soup.select("ul[class='mw-search-results'] a")):
            return (-1,-1,-1)
        # save title from first search result
        parent_title = soup.select("ul[class='mw-search-results'] a")[0].get("title")
        # save url from first search result
        parent_url = "https://en.wikipedia.org"+soup.select("ul[class='mw-search-results'] a")[0].get("href")
        # make soup from the parent url
        resp = requests.get(parent_url)
        # fix: save the redirected url, if applicable
        parent_url = resp.url
        if resp.status_code != 200:
            print("Couldn't search the query on Wikipedia")
            return (-1,-1,-1)
        soup= bs(resp.text,'lxml')
        # find children (recommendations)
        retval = get_recommendations(soup)
    
    # exception case
    else:
        print("Unknown content returned by wiki servers")
        return (-1,-1,-1)
    
    if retval == -1:
        print("Couldn't figure out the recommendation links")
        return (-1,-1,-1)
    else:
        #print("recommendations are:", "(Total: "+str(len(retval))+")")
        #print(retval)
        #print("for parent: "+parent_title)
        #print(parent_url)
        return (parent_title,parent_url,retval)

@app.route('/')
def home():
	jsdata = json.load(open('static/test.json'))
	return render_template('index.html',jsdata=jsdata)

@app.route('/search', methods = ['POST'])
def get_post_javascript_search_data():
	global current_engine
	jsdata = request.form['javascript_data']
	print("Got this: ",type(jsdata))
	if current_engine == 'Wikipedia':
		parent_title, parent_url, recommendations = search_on_wiki(jsdata)
		if parent_title==-1:
			print("Operation failed")
		else:
			crate_nodes_and_links(parent_title,parent_url,recommendations)
			jsdata = {**nodes_dict,**links_dict}
			print(jsonify(jsdata))
	return jsonify(jsdata)

@app.route('/expand', methods = ['POST'])
def get_post_javascript_expand_data():
	jsdata = request.form['javascript_data']
	print("Got this: ",jsdata,type(jsdata))
	if current_engine == 'Wikipedia':
		parent_title, parent_url, recommendations = search_on_wiki(jsdata)
		if parent_title==-1:
			print("Operation failed")
		else:
			appends_nodes_and_links(parent_title,parent_url,recommendations)
			jsdata = {**nodes_dict,**links_dict}
			print(jsonify(jsdata))
	return jsonify(jsdata)

@app.route('/switch', methods = ['POST'])
def get_post_javascript_switch_data():
	global current_engine
	jsdata = request.form['javascript_data']
	if jsdata != current_engine:
		current_engine = jsdata
	print("Current search engine is ", current_engine)
	return jsdata
	
if __name__ == '__main__':
	app.run(debug=True)