from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieComment
from movies.forms import MovieReviewForm, MovieCommentForm
from django.db.models import Avg, Count
from .models import Favorite, Movie, Genre
from django.contrib.auth.models import User
import random
from django.shortcuts import redirect

def all_movies(request):
    movies = Movie.objects.all()
    context = {'movies': movies, 'message': 'welcome'}
    return render(request, 'movies/allmovies.html', context=context)

# Create your views here.
def index(request):
    # TOP 10 POR PROMEDIO DE CALIFICACIONES
    # usa las reseñas (rating), NO likes
    top_movies = Movie.objects.annotate(
        avg_rating=Avg('moviereview__rating')
    ).filter(
        avg_rating__isnull=False
    ).order_by('-avg_rating')[:10]

    # FAVORITAS DEL USUARIO
    favorites = []
    favorite_ids = []
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user)
        favorite_ids = [f.movie.id for f in favorites]

    # TODAS LAS PELÍCULAS
    movies = Movie.objects.all()[:8] 

    context = { 'movies': movies,
        'top_movies': top_movies,
        'favorites': favorites,
        'favorite_ids': favorite_ids,
        'message': 'welcome'
    }
    return render(request,'movies/index.html', context=context )

def add_comment(request, movie_id):
    form = None
    movie = Movie.objects.get(id=movie_id)

    if request.method == 'POST':
        form = MovieCommentForm(request.POST)
        if form.is_valid():
            comment = form.cleaned_data['comment']
            movie_comment = MovieComment(movie=movie, user=request.user, comment=comment)
            movie_comment.save()
            return HttpResponseRedirect('/movies/')
    else:
        form = MovieCommentForm()
        return render(request,
                  'movies/movie_comment_form.html',
                  {'movie_comment_form': form, 'movie':movie})

def movie(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    review_form = MovieReviewForm()
    
    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = [f.movie.id for f in Favorite.objects.filter(user=request.user)]
    
    context = { 
        'movie': movie, 
        'saludo': 'welcome', 
        'review_form': review_form,
        'favorite_ids': favorite_ids
    }
    return render(request,'movies/movie.html', context=context)

def movie_reviews(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    return render(request,'movies/reviews.html', context={'movie':movie } )

def add_review(request, movie_id):
    form = None
    movie = Movie.objects.get(id=movie_id)
    if request.method == 'POST':
        form = MovieReviewForm(request.POST)
        if form.is_valid():
            rating = form.cleaned_data['rating']
            title  = form.cleaned_data['title']
            review = form.cleaned_data['review']
            movie_review = MovieReview(
                    movie=movie,
                    rating=rating,
                    title=title,
                    review=review,
                    user=request.user)
            movie_review.save()
            return HttpResponse(status=204,
                                headers={'HX-Trigger': 'listChanged'})
    else:
        form = MovieReviewForm()
        return render(request,
                  'movies/movie_review_form.html',
                  {'movie_review_form': form, 'movie':movie})

def toggle_favorite(request, movie_id):
    # verificar usuario logueado
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/users/login')

    movie = Movie.objects.get(id=movie_id)

    # crear o buscar favorito
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        movie=movie
    )

    # si ya existía → eliminar (toggle)
    if not created:
        favorite.delete()

    # regresar a la película
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/movies/'))
    #return HttpResponseRedirect(f'/movies/{movie_id}/')

def search(request):
    query = request.GET.get('q')
    search_type = request.GET.get('type', 'movies')  # default movies
    selected_genres = request.GET.getlist('genres')

    movies = []
    users = []
    genres = Genre.objects.all()
    favorite_ids = []

    if request.user.is_authenticated:
        favorite_ids = [f.movie.id for f in Favorite.objects.filter(user=request.user)]


    # USERS
    if search_type == 'users':
        if query:
            users = User.objects.filter(username__icontains=query)[:5]
        return render(request, 'movies/search.html', {
            'users': users,
            'movies': [],
            'genres': [],
            'query': query,
            'search_type': search_type
        })

    # MOVIES
    movies = Movie.objects.all()

    if query:
        movies = movies.filter(title__icontains=query)

    if selected_genres:
        movies = movies.filter(genres__id__in=selected_genres) \
                       .annotate(num_genres=Count('genres')) \
                       .filter(num_genres__gte=len(selected_genres))
    # la primera = mejor calificada
    movies = movies.annotate(avg_rating=Avg('moviereview__rating')) \
               .order_by('-avg_rating')

    return render(request, 'movies/search.html', {
        'movies': movies,
        'users': [],
        'genres': genres,
        'favorite_ids': favorite_ids,
        'selected_genres': selected_genres,
        'query': query,
        'search_type': search_type
    })

def random_movie(request):
    ids = list(Movie.objects.values_list('id', flat=True))
    
    if not ids:
        return redirect('/movies/')  # por si no hay pelis

    random_id = random.choice(ids)
    return redirect(f'/movies/{random_id}/')