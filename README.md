# Lost in Recommendations!

* It is one of the running joke on the internet that video recommendations on Youtube website sometimes tangential to your interests. And it is common for many users to surf through recommended videos and end up on a totally different video.  
* In this project, I have created a website that attempts to visualize a users's journey through the recommended videos on YouTube (and also the recommended articles on Wikipedia). 
* WebApp is live on https://lostinrecommendations.herokuapp.com/.

## Highlights:
* Complete end-to-end solution [running on Heroku as a webapp](https://lostinrecommendations.herokuapp.com/). 
* User is allowed to search a query on either Youtube or Wikipedia and user can also click on any node in the graph to further expand the graph with recommendations.
* Web sever is Flask-based and is written in Python.
* [Freelancer bootstrap theme](https://startbootstrap.com/template-overviews/freelancer/) was used for front-end component.
* Javascript/jQuery/AJAX used for managing interaction (GET/POST communication) with Flask server.
* D3 force directed graph is created to visualize the recommendations.
* Web scraping is done in order to generate data for D3 graph.

# Known issues:
* Due to certain fields optimized for desktop viewing, the mobile interface for the site is not rendered smoothly. This needs further work and improvements.

## Screenshots
Home Page
![Home Page](https://i.imgur.com/mUKKAYO.png)

Sample Wikipedia search result
![Wikipedia search result](https://i.imgur.com/PkuoUQd.png)

Click to further see recommendations for a node
![Click to further see recommendations for a node](https://i.imgur.com/UtE5wZG.png)

D3 force directed graphs support force/drag actions
![Force/drag support by D3 graphs](https://i.imgur.com/rBd7Nwn.png)

Sample Youtube search results
![Sample Youtube search results](https://i.imgur.com/nCAJxRE.png)

Mobile site preview  
![Mobile site preview](https://i.imgur.com/gBu1km9.png)
