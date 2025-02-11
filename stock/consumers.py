import copy
import json
from asgiref.sync import sync_to_async, async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from stock.models import UserStock

class StockConsumer(AsyncWebsocketConsumer):
    
    @sync_to_async
    def addToCeleryBeat(self, stockpicker):
        task = PeriodicTask.objects.filter(name="every-10-seconds")
        if len(task) > 0:
            task = task.first()
            args = json.loads(task.args)
            args = args[0]
            for x in stockpicker:
                if x not in args:
                    args.append(x)
            task.args = json.dumps([args])
            task.save()
        else:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=10, period=IntervalSchedule.SECONDS
            )
            task = PeriodicTask.objects.create(
                interval=schedule, name="every-10-seconds",
                task="stock.tasks.update_stock",
                args=json.dumps([stockpicker])
            )
    
    @sync_to_async
    def addToUserStock(self, stockpicker):
        user = self.scope['user']
        for i in stockpicker:
            obj, created = UserStock.objects.get_or_create(ticker=i)
            obj.user.add(user)

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"stock_{self.room_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Parse query string
        query_params = parse_qs(self.scope['query_string'].decode())

        print('query params:', query_params)
        stockpicker = query_params['stockpicker']

        # add to celery beat
        await self.addToCeleryBeat(stockpicker)

        # add user to user stock
        await self.addToUserStock(stockpicker)

        await self.accept()

        print('User {0} Connected to {1}'.format(self.scope['user'], self.room_group_name))
    
    @sync_to_async
    def helper_func(self):
        user = self.scope['user']
        stocks = UserStock.objects.filter(user__id=user.id)
        task = PeriodicTask.objects.get(name='every-10-seconds')
        args = json.loads(task.args)
        args = args[0]
        for i in stocks:
            i.user.remove(user)
            if i.user.count() == 0:
                args.remove(i.ticker)
                i.delete()
        
        if args == None:
            args = []
        
        if len(args) == 0:
            task.delete()
        else:        
            task.args = json.dumps([args])
            task.save()

    async def disconnect(self, close_code):
        await self.helper_func()
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {
                "type": "send_update", 
                "message": message
            }
        )
    
    @sync_to_async
    def selectUserStocks(self):
        user = self.scope['user']
        user_stocks = user.userstock_set.values_list('ticker', flat=True)
        print('User: {0}, stocks: {1}'.format(user, user_stocks))
        return list(user_stocks)

    # Receive message from room group
    async def send_stock_update(self, event):
        print('=== send_stock_update ===')
        message = event["message"]
        message = copy.copy(message)

        user_stocks = await self.selectUserStocks()
        message = [x for x in message if x['ticker'] in user_stocks]
        print('message:', message)
        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))