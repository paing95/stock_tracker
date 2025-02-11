import concurrent.futures

from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from yfinance import Ticker

import log_helper
from stock import models

logger = log_helper.getLogger('Stock API View')

def loginView(request):
    if request.user.is_authenticated:
        return redirect('stock-picker')

    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Please supply login credentials.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('stock-picker')
        else:
            messages.error(request, 'Wrong login credentials.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def signupView(request):
    if request.user.is_authenticated:
        return redirect('stock-picker')
    
    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        email = request.POST.get('email', '')

        if not username or not password or not email:
            messages.error(request, 'Please provide all user details.')
            return render(request, 'signup.html')
        
        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, 'User already exists.')
            return render(request, 'signup.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        login(request, user)
        return redirect('stock-picker')
    
    return render(request, 'signup.html')


def logoutView(request):
    logout(request)
    return redirect('stock-login')


def stockPickerView(request):
    if not request.user.is_authenticated:
        return redirect('stock-login')
    companies = models.Company.objects.all().order_by('name')
    return render(request,  'stock/picker.html', {
        "companies": companies
    })


def stockTrackerView(request):
    if not request.user.is_authenticated:
        return redirect('stock-login')
    tickers = request.GET.getlist('stockpicker')

    if not tickers:
        return render(request,  'stock/tracker.html', {
            "companies": []
        })
    
    # preload the dict to reduce db calls
    company_dict = {
        company.ticker : company.name for company in models.Company.objects.filter(ticker__in=tickers)
    }
    objects = []

    def get_stock_quote(t):
        try:
            ticker = Ticker(t)
            info = ticker.get_info()
            obj = {
                "ticker": t,
                "name": company_dict[t],
                "prev_close": round(info['previousClose'], 2),
                "open": round(info['open'], 2),
                "current_price": round(info['currentPrice'], 2),
                "change": round(info['currentPrice'] - info['previousClose'], 2),
                "change_percentage": round(((info['currentPrice'] - info['previousClose']) / info['previousClose']) * 100, 2),
                "volume": "{:,}".format(info['regularMarketVolume'])
            }
            return obj
        except Exception as e:
            logger.error(u'Error getting the stock info for {0}: {1}'.format(t, e))

    # Parllel Execution, I/O bound
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.API_VIEW_THREAD_COUNT) as executor:
        futures = [executor.submit(get_stock_quote, ticker) for ticker in tickers]
        for future in concurrent.futures.as_completed(futures):
            if not future.result: continue
            objects.append(future.result())
    
    if objects: objects = sorted(objects, key=lambda x: x['name'])

    return render(request,  'stock/tracker.html', {
        "companies": objects,
        "room_name": { 'name' : 'track'}
    })
