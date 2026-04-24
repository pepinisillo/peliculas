from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from users.models import Profile
from movies.models import MovieReview
from django.contrib import messages
from django.contrib.messages import constants
from django.db.models import Count, Q

# Vista de login
def login_view(request):
    # Si el usuario está autenticado, se redirige a la página de inicio
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))
    # Validación de errores
    errors = {}
    # Si el método es POST, se procesa el formulario
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.POST.get("username")
        password = request.POST.get("password")
        # Validación de campos requeridos
        if not username:
            errors['username'] = "Please enter a valid username"
        if not password:
            errors['password'] = "Please enter a valid password"

        # Si hay errores, se muestran en la plantilla
        if errors:
            # Se retorna el formulario de login con el nombre de usuario ingresado
            return render(request, 'users/login.html', context={'errors':errors, 'username':username})

        # Autenticar el usuario
        user = authenticate(request, username=username, password=password)

        # Si el usuario es válido, se inicia sesión y se redirige a la página de inicio
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            # Si el usuario no es válido, se muestra un mensaje de error y se retorna el formulario de login con el nombre de usuario ingresado
            errors['login'] = "Your password is incorrect or this account does not exist. Please verify and try again."
            return render(request, 'users/login.html', context={'errors':errors, 'username':username})
    else:
        # Si el método es GET, se muestra el formulario de login
        return render(request, 'users/login.html')

# Vista de logout
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login'))

# Vista de registro
def register_view(request):
    # Si el usuario está autenticado, se redirige a la página de inicio
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))
    errors = {}
    # Si el método es POST, se procesa el formulario
    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validación de campos requeridos
        if not username:
            errors['username'] = "Please enter a username"
        if not email:
            errors['email'] = "Please enter your email"
        if not password:
            errors['password'] = "Please enter your password"
        if not confirm_password:
            errors['confirm_password'] = "Please confirm your password"
        if password and confirm_password and password != confirm_password:
            errors['password_confirmation'] = "Passwords do not match"

        # Si hay errores, se muestran en la plantilla
        if errors:
            return render(request, 'users/register.html', context={'errors':errors, 'username':username, 'email':email})
        else:
            # Validar que el correo electrónico no exista
            if User.objects.filter(email=email).exists():
                errors['email'] = "Please use a different email"
                return render(request, 'users/register.html', context={'errors':errors, 'username':username, 'email':email})
            # Validar que el nombre de usuario no exista
            if User.objects.filter(username=username).exists():
                errors['username'] = "This username is already in use"
                return render(request, 'users/register.html', context={'errors':errors, 'username':username, 'email':email})
            # Crear el usuario
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            # Si el usuario está autenticado, se redirige a la página de inicio
            if request.user.is_authenticated:
                return HttpResponseRedirect(reverse('index'))
            
    else:
        # Si el método es GET, se muestra el formulario de registro
        return render(request, 'users/register.html')

# Vista de perfil
def profile_view(request):
    # Si el usuario no está autenticado, se redirige a la página de login
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    # Si el usuario está autenticado, se muestra el perfil
    profile, _ = Profile.objects.get_or_create(user=request.user)
    sort = request.GET.get('sort', 'recent')
    reviews = (
        MovieReview.objects
        .filter(user=request.user)
        .select_related('movie')
        .annotate(
            like_count=Count('likes', filter=Q(likes__vote='like')),
            dislike_count=Count('likes', filter=Q(likes__vote='dislike')),
        )
    )
    if sort == 'popular':
        reviews = reviews.order_by('-like_count', '-created_at')
    else:
        sort = 'recent'
        reviews = reviews.order_by('-created_at')
    reviews_count = reviews.count()
    follower_profiles = profile.followers.select_related('user').order_by('user__username')
    following_profiles = profile.following.select_related('user').order_by('user__username')

    context = {
        'user': request.user,
        'profile': profile,
        'followers_count': profile.followers.count(),
        'following_count': profile.following.count(),
        'follower_profiles': follower_profiles,
        'following_profiles': following_profiles,
        'reviews_count': reviews_count,
        'reviews': reviews,
        'reviews_sort': sort,
    }
    return render(request, 'users/profile.html', context=context)

# Vista de edición de perfil
def edit_profile_view(request):
    # Si el usuario no está autenticado, se redirige a la página de login
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))

    profile, _ = Profile.objects.get_or_create(user=request.user)
    errors = {}
    success = False

    # Si el método es POST, se procesa el formulario
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        description = (request.POST.get('description') or '').strip()
        image = request.FILES.get('image')

        if not username:
            errors['username'] = 'Username is required.'
        elif User.objects.exclude(pk=request.user.pk).filter(username=username).exists():
            errors['username'] = 'That username is already in use.'

        if len(description) > 500:
            errors['description'] = 'Description cannot exceed 500 characters.'
        
        # Si no hay errores, se actualiza el perfil
        if not errors:
            request.user.username = username
            request.user.save()
            profile.description = description
            if image:
                profile.image = image
            profile.save()
            success = True
            messages.success(request, 'Profile updated successfully')
            return HttpResponseRedirect(reverse('profile'))

    context = {
        'user': request.user,
        'profile': profile,
        'errors': errors,
        'success': success,
    }
    return render(request, 'users/edit_profile.html', context=context)


def toggle_follow_view(request, user_id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    if request.method != 'POST':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))

    target_user = User.objects.filter(id=user_id).first()
    if not target_user:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))
    if target_user.id == request.user.id:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))

    my_profile, _ = Profile.objects.get_or_create(user=request.user)
    target_profile, _ = Profile.objects.get_or_create(user=target_user)

    if target_profile.followers.filter(id=my_profile.id).exists():
        target_profile.followers.remove(my_profile)
    else:
        target_profile.followers.add(my_profile)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('index')))
    