from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User



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
            errors['username'] = "Por favor, ingresa un usuario válido"
        if not password:
            errors['password'] = "Por favor, ingresa una contraseña válida"

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
            errors['login'] = "Tu contraseña es incorrecta o esta cuenta no existe. Por favor, verifica y vuelve a intentarlo"
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
            errors['username'] = "Por favor, ingresa un nombre de usuario"
        if not email:
            errors['email'] = "Por favor, ingresa tu correo electrónico"
        if not password:
            errors['password'] = "Por favor, ingresa tu contraseña"
        if not confirm_password:
            errors['confirm_password'] = "Por favor, confirma tu contraseña"
        if password and confirm_password and password != confirm_password:
            errors['password_confirmation'] = "Las contraseñas no coinciden"

        # Si hay errores, se muestran en la plantilla
        if errors:
            return render(request, 'users/register.html', context={'errors':errors, 'username':username, 'email':email})
        else:
            # Validar que el correo electrónico no exista
            if User.objects.filter(email=email).exists():
                errors['email'] = "Ingresa otro correo electrónico"
                return render(request, 'users/register.html', context={'errors':errors, 'username':username, 'email':email})
            # Validar que el nombre de usuario no exista
            if User.objects.filter(username=username).exists():
                errors['username'] = "El nombre de usuario ya está en uso"
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
