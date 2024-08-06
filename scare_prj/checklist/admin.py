from django.contrib import admin
from .models import Day, Todo, Notification
# Register your models here.
admin.site.register(Day)
admin.site.register(Todo)
admin.site.register(Notification)
