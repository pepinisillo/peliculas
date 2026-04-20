from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request,'users/profile.html')

# Vista de login
def login_view(request):
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
            return render(request, 'users/login.html', context={'errors':errors})

        # Autenticar el usuario
        user = authenticate(request, username=username, password=password)

        # Si el usuario es válido, se inicia sesión y se redirige a la página de inicio
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            # Si el usuario no es válido, se muestra un mensaje de error
            errors['login'] = "Tu contraseña es incorrecta o esta cuenta no existe. Por favor, verifica y vuelve a intentarlo"
            return render(request, 'users/login.html', {'errors':errors})
    else:
        # Si el método es GET, se muestra el formulario de login
        return render(request, 'users/login.html')

# Vista de logout
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))
