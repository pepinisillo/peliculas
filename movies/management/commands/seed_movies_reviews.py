import random
import string
from urllib.parse import quote_plus

import requests
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from movies.models import Movie, MovieReview, MovieReviewLike
from mymovies.load_movie import add_movie
from users.models import Profile


class Command(BaseCommand):
    help = "Load real TMDB movies and create reviews with likes/dislikes."
    OVERWATCH_USERNAMES = [
        "Tracer",
        "Genji",
        "Mercy",
        "Reaper",
        "DVa",
        "Hanzo",
        "Winston",
        "Widowmaker",
        "Lucio",
        "Zarya",
        "Soldier76",
        "Mei",
        "Ana",
        "Junkrat",
        "Roadhog",
        "Sombra",
        "Moira",
        "Brigitte",
        "Ashe",
        "Baptiste",
        "Sigma",
        "Echo",
        "Sojourn",
        "Kiriko",
        "Ramattra",
        "Illari",
        "Mauga",
        "Lifeweaver",
        "Cassidy",
        "Pharah",
    ]
    USERNAME_SUFFIXES = [
        "vanguard",
        "striker",
        "sentinel",
        "specter",
        "guardian",
        "phoenix",
        "ranger",
        "oracle",
        "warden",
        "nova",
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--movies",
            type=int,
            default=100,
            help="Number of real TMDB movies to load (default: 100).",
        )
        parser.add_argument(
            "--reviews-per-movie",
            type=int,
            default=5,
            help="Number of reviews per movie (default: 5).",
        )
        parser.add_argument(
            "--users",
            type=int,
            default=20,
            help="Minimum pool of users for reviews/votes (default: 20).",
        )
        parser.add_argument(
            "--tmdb-start-id",
            type=int,
            default=1,
            help="Initial TMDB movie id to start scanning (default: 1).",
        )
        parser.add_argument(
            "--max-scan",
            type=int,
            default=2000,
            help="Max TMDB ids to scan to reach movie target (default: 2000).",
        )

    def handle(self, *args, **options):
        movies_to_create = max(options["movies"], 1)
        reviews_per_movie = max(options["reviews_per_movie"], 1)
        min_users = max(options["users"], 2)
        tmdb_start_id = max(options["tmdb_start_id"], 1)
        max_scan = max(options["max_scan"], movies_to_create)

        users = self._ensure_users(min_users)

        created_movies = 0
        created_reviews = 0
        created_votes = 0
        scanned_ids = 0

        review_titles = [
            "Great watch",
            "Solid movie",
            "Worth your time",
            "Could be better",
            "Surprisingly good",
            "Mixed feelings",
            "Highly recommended",
            "Average but enjoyable",
        ]
        review_bodies = [
            "The story keeps a good pace and the cast does a strong job.",
            "Visual style is very good, but some scenes feel a bit long.",
            "Good direction and soundtrack. I would watch it again.",
            "Not perfect, but it has memorable moments and strong acting.",
            "A fun movie overall with a couple of weak points.",
            "Interesting concept and decent execution from start to finish.",
        ]

        current_tmdb_id = tmdb_start_id
        while created_movies < movies_to_create and scanned_ids < max_scan:
            scanned_ids += 1
            if Movie.objects.filter(tmdb_id=current_tmdb_id).exists():
                current_tmdb_id += 1
                continue

            try:
                add_movie(current_tmdb_id)
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(f"Skipping TMDB id {current_tmdb_id}: {exc}")
                )
                current_tmdb_id += 1
                continue

            movie = Movie.objects.filter(tmdb_id=current_tmdb_id).first()
            if not movie:
                current_tmdb_id += 1
                continue

            created_movies += 1
            for _ in range(reviews_per_movie):
                reviewer = random.choice(users)
                review = MovieReview.objects.create(
                    user=reviewer,
                    movie=movie,
                    rating=random.randint(1, 5),
                    title=random.choice(review_titles),
                    review=random.choice(review_bodies),
                )
                created_reviews += 1

                voters = [u for u in users if u.id != reviewer.id]
                voter = random.choice(voters) if voters else reviewer
                vote = random.choice([MovieReviewLike.LIKE, MovieReviewLike.DISLIKE])
                MovieReviewLike.objects.create(
                    user=voter,
                    review=review,
                    vote=vote,
                )
                created_votes += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Loaded movie {created_movies}/{movies_to_create} (tmdb_id={current_tmdb_id})"
                )
            )
            current_tmdb_id += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created_movies} real movies, {created_reviews} reviews, {created_votes} votes."
            )
        )
        if created_movies < movies_to_create:
            self.stdout.write(
                self.style.WARNING(
                    f"Target not reached. Scanned {scanned_ids} TMDB ids from {tmdb_start_id}."
                )
            )

    def _ensure_users(self, minimum):
        users = list(User.objects.order_by("id"))
        if len(users) < minimum:
            self._create_overwatch_users(minimum - len(users))
            users = list(User.objects.order_by("id"))
        self._ensure_profile_images(users[:minimum])
        return users

    def _create_overwatch_users(self, count):
        created = 0
        base_names = list(self.OVERWATCH_USERNAMES)
        random.shuffle(base_names)

        for base_name in base_names:
            if created >= count:
                return

            username = self._pick_unique_username(base_name.lower())
            user = User.objects.create(
                username=username,
                email=f"{username}@overwatch.gg",
            )
            user.set_password("SeedPass123!")
            user.save()
            created += 1

        while created < count:
            base_name = random.choice(self.OVERWATCH_USERNAMES).lower()
            username = self._pick_unique_username(base_name)
            user = User.objects.create(
                username=username,
                email=f"{username}@overwatch.gg",
            )
            user.set_password("SeedPass123!")
            user.save()
            created += 1

    def _pick_unique_username(self, base_name):
        # No "seed", no numbers: compose with lore-like suffixes or random letters only.
        candidates = [f"{base_name}_{suffix}" for suffix in self.USERNAME_SUFFIXES]
        random.shuffle(candidates)
        for candidate in candidates:
            if not User.objects.filter(username=candidate).exists():
                return candidate

        while True:
            letters = "".join(random.choice(string.ascii_lowercase) for _ in range(4))
            candidate = f"{base_name}_{letters}"
            if not User.objects.filter(username=candidate).exists():
                return candidate

    def _ensure_profile_images(self, users):
        for user in users:
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.image:
                continue

            avatar_url = (
                "https://ui-avatars.com/api/"
                f"?name={quote_plus(user.username)}&size=512&background=0f172a&color=ffffff"
            )
            try:
                response = requests.get(avatar_url, timeout=10)
                response.raise_for_status()
            except requests.RequestException:
                continue

            filename = f"{user.username}.png"
            profile.image.save(filename, ContentFile(response.content), save=True)
