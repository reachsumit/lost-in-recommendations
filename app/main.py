from flask import Flask,render_template,request,jsonify,request,make_response
import json,requests
from bs4 import BeautifulSoup as bs
app = Flask(__name__)

current_engine = 'Wikipedia' # default search engine
nodes_dict = {"nodes":[]}
links_dict = {"links":[]}
current_group_number = 0

def get_recommendations_yt(soup):
    recommendations = []
    try:
        # temporary list to save side bar
        myl = soup.select('li[class="video-list-item related-list-item show-video-time related-list-item-compact-video"] a')
        # skip by one item to avoid duplicate entry
        for item in myl[::2]:
		    # keep title length to 45 characters to maintain readability
            recommendations.append([item.get("title")[:45],"https://www.youtube.com"+item.get("href")])
    except Exception as e:
        print(e)
        return -1
    return recommendations[:4]

def search_on_yt(search):
    parent_title = ""
    parent_url = ""
    try:
        # search text on youtube
        resp = requests.get("https://www.youtube.com/results?search_query="+search)
        # if failed for some reason
        if resp.status_code != 200:
            print("Couldn't search the query on Youtube")
            return (-1,-1,-1)
	
        # make soup of the result
        soup= bs(resp.text,'lxml')
        
        # Take first search result as the parent node
        for item in soup.select("div[class='yt-lockup-content'] a"):
            if item.get("href").startswith("/watch?v="):
                parent_title = item.get("title")
                parent_url = "https://www.youtube.com"+item.get("href")
                break
        
        # open parent link and look for recommenations in the side bar
        resp = requests.get(parent_url)
        if resp.status_code != 200:
            print("Couldn't search the query on Youtube")
            return (-1,-1,-1)
        soup = bs(resp.text,'lxml')
        # pass this soup to another function to read recommendations
        retval = get_recommendations_yt(soup)
        
        if retval == -1:
            print("Couldn't figure out the Youtube recommendation links")
            return (-1,-1,-1)
        else:
            print("recommendations are:", "(Total: "+str(len(retval))+")")
            print(retval)
            print("for parent: "+parent_title)
            print(parent_url)
            return (parent_title,parent_url,retval)
    except Exception as e:
        print(e)
        return (-1,-1,-1)

def appends_nodes_and_links(parent_url,recommendations):
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
        # check if this node already exists
        if [item for item in nodes_dict['nodes'] if item['url']==node['url']]:
            continue
        nodes_dict["nodes"].append(node)

    try:
        # find parent's index
        parent_index = nodes_dict['nodes'].index(dict([item for item in nodes_dict['nodes'] if item['url']==parent_url][0]))
        # connect all children with this parent index
        for idx, item in enumerate(nodes_dict['nodes']):
            if idx == parent_index:
                continue
            else:
                links_dict['links'].append({"source":idx,"target":parent_index})
    except Exception as e:
        print(e)
        return -1

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
    try:
        # find parent's index
        parent_index = nodes_dict['nodes'].index(dict([item for item in nodes_dict['nodes'] if item['url']==parent_url][0]))
        # connect all children with this parent index
        for idx, item in enumerate(nodes_dict['nodes']):
            if idx == parent_index:
                continue
            else:
                links_dict['links'].append({"source":idx,"target":parent_index})
    except Exception as e:
        print(e)
        return -1
	
def get_recommendations(soup):
    recommendations = []
    # find all see also links
    seeAll = soup.find_all(text="See also")
    # check if we are at the bottom one
    foundSeeAll = False
    try:
        for item in seeAll:
            # this seeAll variable is one of the main headlines
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
    except Exception as e:
        print(e)
        return -1
    return recommendations

def search_on_wiki(search):
    parent_title = ""
    parent_url = ""
    try:
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
    except Exception as e:
        print(e)
        return (-1,-1,-1)

@app.route('/')
def home():
	jsdata = json.load(open('static/test.json'))
	resp = make_response(render_template('index.html',jsdata=jsdata))
	resp.set_cookie('engine', 'Wikipedia') 
	return resp

@app.route('/knowType', methods = ['GET'])
def get_post_javascript_knowType_data():
    global current_engine
    jsdata = {"engine":current_engine}
    eng = request.cookies.get('engine')
    if eng:
        print("engine stored in cookies is: ",eng)
        current_engine = eng
        jsdata = {"engine":eng}
        return jsonify(jsdata)
    else:
        return jsonify(jsdata)

@app.route('/search', methods = ['POST'])
def get_post_javascript_search_data():
	global current_engine
	eng = request.cookies.get('engine')
	if eng:
		current_engine = eng
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
	elif current_engine == 'Youtube':
		parent_title, parent_url, recommendations = search_on_yt(jsdata)
		if parent_title==-1:
			print("Operation failed")
		else:
			crate_nodes_and_links(parent_title,parent_url,recommendations)
		jsdata = {**nodes_dict,**links_dict}
		print(jsonify(jsdata))
	return jsonify(jsdata)

@app.route('/expand', methods = ['POST'])
def get_post_javascript_expand_data():
	global current_engine
	eng = request.cookies.get('engine')
	if eng:
		current_engine = eng
	jsdata = request.form['javascript_data']
	print("Got this: ",jsdata,type(jsdata))
	parent_url = jsdata
	if current_engine == 'Wikipedia':
		resp = requests.get(jsdata)
		soup= bs(resp.text,'lxml')
		recommendations = get_recommendations(soup)
		if recommendations==-1:
			print("Operation failed")
		else:
			appends_nodes_and_links(parent_url,recommendations)
		jsdata = {**nodes_dict,**links_dict}
		print(jsonify(jsdata))
	elif current_engine == 'Youtube':
		resp = requests.get(jsdata)
		soup= bs(resp.text,'lxml')
		recommendations = get_recommendations_yt(soup)
		if recommendations==-1:
			print("Operation failed")
		else:
			appends_nodes_and_links(parent_url,recommendations)
		jsdata = {**nodes_dict,**links_dict}
		print(jsonify(jsdata))
	return jsonify(jsdata)

@app.route('/switch', methods = ['POST'])
def get_post_javascript_switch_data():
    # clear any prior nodes information
    global current_engine, nodes_dict, links_dict, current_group_number
    nodes_dict = {"nodes":[]}
    current_group_number = 0
    links_dict = {"links":[]}
    
    jsdata = request.form['javascript_data']
    if jsdata != current_engine:
        current_engine = jsdata
    print("Current search engine is ", jsdata)
    #return jsdata
    #resp = make_response(render_template('index.html',jsdata=jsdata))
	#resp.set_cookie('engine', 'Wikipedia') 
	#return resp
    resp = make_response(render_template('index.html',jsdata=jsdata))
    resp.set_cookie('engine', jsdata) 
    return resp
	
if __name__ == '__main__':
	app.run(debug=False)