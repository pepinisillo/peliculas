from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class Genre(models.Model):
    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name

class Person(models.Model):
    name = models.CharField(max_length=128)
    profile_path = models.URLField(blank=True, null=True)
    known_for_department = models.CharField(max_length=40, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    place_of_birth = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class ProductionCompany(models.Model):
    name = models.CharField(max_length=128)

class Movie(models.Model):
    title = models.CharField(max_length=80)
    overview = models.TextField()
    release_date = models.DateField()
    running_time = models.IntegerField()
    budget = models.IntegerField(blank=True, null=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    revenue = models.IntegerField(blank=True, null=True)
    poster_path = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre)
    credits = models.ManyToManyField(Person, through='MovieCredit')
    production_companies = models.ManyToManyField(ProductionCompany, blank=True)
    backdrops = models.URLField(blank=True, null=True)

    def __str__(self):
        return f'{self.title} {self.release_date}'


class MovieCredit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)


class MovieReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    title = models.TextField(blank=False, null=False, default="Reseña")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        # Un usuario solo puede dejar una reseña por película
        unique_together = ('user', 'movie')

class MovieReviewLike(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    VOTE_CHOICES = [(LIKE, 'Like'), (DISLIKE, 'Dislike')]

    # Relaciones con el usuario y la reseña que recibe el voto
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE, related_name='likes')
    
    # Almacena si el voto es like o dislike
    vote = models.CharField(max_length=7, choices=VOTE_CHOICES)

    class Meta:
        # Evita que un usuario vote más de una vez en la misma reseña
        unique_together = ('user', 'review')

    def __str__(self):
        return f"{self.user} - {self.vote} - {self.review.id}"

class MovieComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    # like = models.BooleanField(default=False)
    comment = models.TextField(blank=True)

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # usuario que da favorito
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE) # película marcada como favorita

    def __str__(self):
        return f"{self.user} - {self.movie}"
