django-oauth-starter
====================
Everything you need to get going with OAuth 1.0a on Django


What this package is
--------------------
This package is a template you can use for implementing OAuth 1.0a authentication in your Django projects. It was developed during the creation of my service, http://bit-chest.com/ and is tested and works. Using this package and your knowledge of OAuth you can quickly set up OAuth 1.0a authentication in your Django project. Using the supplied client, you can test your implementation and offer the developers using your API a starting point for their implementations.


What this package is NOT
------------------------
This package is not a tutorial for OAuth 1.0a, although you could certainly turn it into one. There is no explanation of the terms used, and no guiding material that helps you learn what OAuth 1.0a is, why you should use it and what the other options are. Knowledge of Django and OAuth are necessary to use this package productively.

However, this package is also not a drop-in replacement for all your authentication needs. You cannot install this package into your project, adjust some settings and be done, simply because there are no settings. To use this package, you will need to take the code from it and put it into your own project, probably changing it quite a bit.

What this package contains
--------------------------
* A Django server project containing one app, `oauth_app` that:
  * handles OAuth 1.0a authentication (including all necessary libraries and models)
  * allows you to authorize, list and deauthorize your request and access tokens
  * uses the Django REST framework (http://django-rest-framework.org/) to serve one dummy resource with OAuth authentication
  * has one view that does OAuth authentication itself for demonstration purposes
  * enables Django admin on all interesting OAuth models
  * test data with one OAuth Consumer (== API key) and two users
  
  
Quickstart
==========

In one shell window, prepare the server:

    ./prepare-server.sh
    ./restart-server.sh

After the server is running, open another shell window and start the client:

    ./prepare-client.sh
    ./start-client.sh

Once you have seen a run of the OAuth workflow, look into `server/views.py` to see the workflow from a server side. Look into `client/client.py` to see the client-side implementation.


The server
==========
The Django server is located in the subdirectory `server`. It's a full Django project containing only one app, `oauth_app`. This app contains urls, models, views and libraries to make OAuth 1.0a work.

Before you can run the server, you have to install the prerequisites, as listed in `server/dependencies.txt`. We suggest putting them into a virtualenv. You can run the script `prepare-server.sh` to create the virtualenv and have the dependencies installed.

Once all prerequisites are installed, you can run the server by syncing the database and start the runserver, or you use the supplied `restart-server.sh` script. This script also loads the supplied test data (from `server/test_consumer.json`) which contains one consumer with key `key` and secret `secret`, as well as two users, `root` (which is a superuser) and `user` (which is not). This is all the data you need to complete an OAuth 1.0a workflow.

The server offers several URLs pertaining to the OAuth workflow, as well as views for authorizing and deauthorizing clients and test resources. You can find all URLs in the module `oauth_app/urls.py`

All views are collected in `oauth_app/views.py`. It is a good starting point for finding out how the workflow is put together.

All necessary models are collected in `oauth_app/models.py`. If you use these models as a starting point for your own implementation, you can add more fields to these models.


The client
==========

The client is a simple python script, `client.py` that completes the OAuth 1.0a workflow and accesses two resource functions. It is set up to access the URLs of the supplied test server.

Before you can run the client, you have to install the prerequites, as listed in `client/dependencies.txt`. We suggest putting them into a virtualenv. You can run the script `prepare-client.sh` to create the virtualenv and have the dependencies installed.

Once all prerequisites are installed, you can run the client by starting the script, or by using the supplied `start-client.sh` shell script. 