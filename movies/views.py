from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieComment
from movies.forms import MovieReviewForm, MovieCommentForm
from django.db.models import Avg 
from .models import Favorite
from django.http import HttpResponseRedirect # Agregar quitar fav

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
    if request.user.is_authenticated:
        favorites = Favorite.objects.filter(user=request.user)

    # TODAS LAS PELÍCULAS
    movies = Movie.objects.all()

    context = { 'movies': movies,         
        'top_movies': top_movies, 
        'favorites': favorites,   
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
    context = { 'movie':movie, 'saludo':'welcome', 'review_form':review_form }
    return render(request,'movies/movie.html', context=context )

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
        return HttpResponseRedirect('/login/')

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
    return HttpResponseRedirect(f'/movies/{movie_id}/')
