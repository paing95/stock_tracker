import concurrent.futures
import traceback

import asyncio
from celery import shared_task
from channels.layers import get_channel_layer
from django.conf import settings
from yfinance import Ticker

import log_helper
from stock import models

logger = log_helper.getLogger('Celery Tasks')

@shared_task(bind = True)
def update_stock(_, tickers):
    logger.debug("Tickers: {}".format(tickers))
    
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
                "name": company_dict[t.upper()],
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
            logger.error(u'Traceback: {}'.format(traceback.format_exc()))

    # Parllel Execution, I/O bound
    with concurrent.futures.ThreadPoolExecutor(max_workers=settings.API_VIEW_THREAD_COUNT) as executor:
        futures = [executor.submit(get_stock_quote, ticker) for ticker in tickers]
        for future in concurrent.futures.as_completed(futures):
            if not future.result(): continue
            objects.append(future.result())
    
    if objects:
        objects = sorted(objects, key=lambda x: x['name'])
        
        # send data to channel
        channel_layer = get_channel_layer()
        loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)

        loop.run_until_complete(channel_layer.group_send("stock_track", {
            'type': 'send_stock_update',
            'message': objects
        }))
        logger.debug("Data sent to room {1}: {0}".format(objects, 'stock_track'))

    return 'Done'
