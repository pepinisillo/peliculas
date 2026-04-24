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
    path('review/like/<int:review_id>/', toggle_like, name='toggle_like'),
    path('delete_review/<int:review_id>/', delete_review, name='delete_review'),
    path('edit_review/<int:review_id>/', edit_review, name='edit_review'),
    path('review/create/<int:movie_id>/', create_review, name='create_review'),
    path('favorite/<int:movie_id>/', toggle_favorite, name='toggle_favorite'),# favoritos
    path('actor/<int:person_id>/', views.actor_detail, name='actor_detail'),
    path('', index)
]
