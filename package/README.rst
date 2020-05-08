===============
django-sharding
===============
Simple horizontal scaling utilities for django framework

- Short def:
    * Scalability is the property of a system to handle a growing amount of work by adding resources to the system
    * Scaling horizontally (out/in) means adding more nodes to (or removing nodes from) a system, such as adding a new computer to a distributed software application. An example might involve scaling out from one web server to three.
    * With horizontal-scaling it is often easier to scale dynamically by adding more machines into the existing pool

This simple package allows the developer to add more than one table to one Model, each table limited by the maximum rows specified in settings.py

How django-sharding work
========================
- Every Model has its own database and you can use 1 database for more than one model
- Every table has new id as premairy key (nid)
- nid is uuid but the first 8 charter are fixed and it used as prefix
- every prefix is specific to database key
- every database can spilt by row count max
- sharding django create a table for databases and register number of rows.

Installation
============
run pip install django-horizontal-sharding

to read configuration and use guide visit: https://github.com/Fethienv/django-sharding