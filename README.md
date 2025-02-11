# Stock Tracker Django Application

It is a simple django application that allows you to select and track S&P 500 company stocks. Powered by python version ***3.11.7***, django, redis, celery and channels to get real time data.

As prerequisites, 

1. Must install the libraries from requirements.txt on a python virtual environment.
2. Must do the database migrations.
3. Must populate the stock tickers into the database with sync_companies.py script.
4. Must have redis server installed.

Command to run redis-server:

```
redis-server
```

Command to run celery worker & beat:

```
celery -A stock_tracker worker --beat --loglevel=info
```