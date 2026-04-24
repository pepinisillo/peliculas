from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from movies.models import Movie, MovieReview, Person, MovieComment, MovieCredit, MovieReviewLike
from movies.models import Movie, MovieReview, Person, MovieComment, MovieReviewLike
from movies.forms import MovieReviewForm, MovieCommentForm
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from .models import Favorite, Movie, Genre
from django.contrib.auth.models import User
import random
from django.shortcuts import redirect

def all_movies(request):
    # Obtiene el número de página actual, por defecto 1
    page = int(request.GET.get('page', 1))
    per_page = 8

    # Calcula el rango de películas a mostrar
    start = (page - 1) * per_page
    end = start + per_page

    all_movies_qs = Movie.objects.all()
    movies = all_movies_qs[start:end]

    # Verifica si existen más películas después de la página actual
    has_more = all_movies_qs.count() > end

    context = {
        'movies': movies,
        'page': page,
        'has_more': has_more
    }

    # Si la petición viene de HTMX, retorna solo el parcial de tarjetas
    if request.headers.get('HX-Request'):
        return render(request, 'movies/partials/movie_cards.html', context)

    return render(request, 'movies/allmovies.html', context)

# Create your views here.
def index(request):
    # TOP 10 POR PROMEDIO DE CALIFICACIONES
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

    # PAGINACIÓN: muestra las primeras 8 películas
    page = int(request.GET.get('page', 1))
    per_page = 8
    start = (page - 1) * per_page
    end = start + per_page
    all_movies_qs = Movie.objects.all()
    movies = all_movies_qs[start:end]
    # Verifica si hay más películas por cargar
    has_more = all_movies_qs.count() > end

    context = {
        'movies': movies,
        'top_movies': top_movies,
        'favorites': favorites,
        'favorite_ids': favorite_ids,
        'message': 'welcome',
        'page': page,
        'has_more': has_more
    }

    # Si la petición viene de HTMX, retorna solo las tarjetas nuevas
    if request.headers.get('HX-Request'):
        return render(request, 'movies/partials/movie_card.html', context)

    return render(request, 'movies/index.html', context)

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

    actors = MovieCredit.objects.filter(movie=movie, job__name='Acting')[:7]
    director = MovieCredit.objects.filter(movie=movie, job__name='Director').first()
    writer = MovieCredit.objects.filter(movie=movie, job__name='Writer').first()
    avg_rating = MovieReview.objects.filter(movie=movie).aggregate(Avg('rating'))['rating__avg']

    favorite_ids = []
    if request.user.is_authenticated:
        favorite_ids = [f.movie.id for f in Favorite.objects.filter(user=request.user)]

    reviews_preview = MovieReview.objects.filter(
        movie=movie
    ).order_by('-id')[:3]

    context = { 'movie':movie, 
               'actors':actors, 
               'avg_rating':avg_rating, 
               'favorite_ids':favorite_ids, 
               'director':director,
               'writer':writer,
               'review_form':review_form, 
               'reviews_preview':reviews_preview 
    }
    return render(request,'movies/movie.html', context=context)

def movie_reviews(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    reviews = movie.moviereview_set.all()


    # conteos de likes y dislikes a cada reseña
    for review in reviews:
        review.like_count = review.likes.filter(vote='like').count()
        review.dislike_count = review.likes.filter(vote='dislike').count()
    return render(request, 'movies/reviews.html', {
        'movie': movie,
        'reviews': reviews
    })


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
    
def delete_review(request, review_id):
    review = MovieReview.objects.get(id=review_id)
    movie_id = review.movie.id
    if review.user == request.user:
        review.delete()
    # Regresa a la página de reseñas de esa película
    return redirect(f'/movies/movie_reviews/{movie_id}/')

def edit_review(request, review_id):
    review = MovieReview.objects.get(id=review_id)
    if request.method == 'POST':
        form = MovieReviewForm(request.POST)
        if form.is_valid():
            review.rating = form.cleaned_data['rating']
            review.title = form.cleaned_data['title']
            review.review = form.cleaned_data['review']
            review.save()
            return HttpResponse(status=204, headers={'HX-Trigger': 'listChanged'})
    else:
        form = MovieReviewForm(initial={
            'rating': review.rating,
            'title': review.title,
            'review': review.review
        })
        return render(request, 'movies/movie_review_form.html', {
            'movie_review_form': form,
            'movie': review.movie,
            'review': review
        })
    
# Vista propia para crear reseña desde la página de reseñas (distinta al modal de movie.html)
def create_review(request, movie_id):
    movie = Movie.objects.get(id=movie_id)
    
    if request.method == 'POST':
        form = MovieReviewForm(request.POST)
        if form.is_valid():
            # Guarda la reseña y redirige a la página de reseñas
            MovieReview.objects.create(
                movie=movie,
                user=request.user,
                rating=form.cleaned_data['rating'],
                title=form.cleaned_data['title'],
                review=form.cleaned_data['review']
            )
            return redirect(f'/movies/movie_reviews/{movie_id}/')
    else:
        form = MovieReviewForm()

    return render(request, 'movies/review_form.html', {
        'movie': movie,
        'form': form
    })
    
def toggle_like(request, review_id):
    # Solo usuarios logueados pueden votar
    if not request.user.is_authenticated:
        return HttpResponseRedirect('/users/login')

    review = MovieReview.objects.get(id=review_id)
    vote_type = request.POST.get('vote')  # 'like' o 'dislike'

    existing_vote = MovieReviewLike.objects.filter(
        user=request.user,
        review=review
    ).first()

    if existing_vote:
        if existing_vote.vote == vote_type:
            # Si vota igual, cancela el voto
            existing_vote.delete()
        else:
            # Si vota diferente, actualiza
            existing_vote.vote = vote_type
            existing_vote.save()
    else:
        # Voto nuevo
        MovieReviewLike.objects.create(
            user=request.user,
            review=review,
            vote=vote_type
        )

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/movies/'))
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


    # CASCARÓN DE USERS
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

def actor_detail(request, person_id):
    person = get_object_or_404(Person, id=person_id)
    credits = MovieCredit.objects.filter(person=person).select_related('movie')
    
    # Agrega avg_rating a cada película en los créditos
    credits = credits.annotate(avg_rating=Avg('movie__moviereview__rating'))
    
    return render(request, 'movies/actor.html', {'person': person, 'credits': credits})
