from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('all/', all_movies),
    path('search/', search, name='search'),
        path('random/', random_movie, name='random_movie'),
    path('<int:movie_id>/', movie, name='pelis'),
    path('movie_comment/add/<int:movie_id>/', add_comment, name='add_comment'),
    path('add_comment/<int:movie_id>/', add_comment),
    path('movie_review/add/<int:movie_id>/', add_review),
    path('movie_reviews/<int:movie_id>/', movie_reviews, name='movie_reviews'),
    path('favorite/<int:movie_id>/', toggle_favorite, name='toggle_favorite'),# favoritos
    path('actor/<int:person_id>/', views.actor_detail, name='actor_detail'),
    path('', index)
]
