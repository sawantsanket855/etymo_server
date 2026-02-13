from django.urls import path
from .views import sample_api,update_mistakes_recording_api

app_name = 'new_app'

urlpatterns = [
    path('sample/', sample_api),
    path('update_mistake_recording/',update_mistakes_recording_api)
]
