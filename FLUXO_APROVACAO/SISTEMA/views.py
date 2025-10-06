# SISTEMA/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm
from .models import Usuario

def login_view(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("home")  # página inicial
            else:
                messages.error(request, "Usuário ou senha incorretos.")

    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def home_view(request):
    return render(request, "home.html")

@login_required
def criar_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('listar_usuarios')  # ajuste para sua rota de listagem
        else:
            messages.error(request, 'Erro ao criar usuário. Verifique os campos.')
    else:
        form = UsuarioCreateForm()

    return render(request, 'usuario_criar.html', {'form': form})

@login_required
def listar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    return render(request, 'usuario_listar.html', {'usuarios': usuarios})

@login_required
def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('listar_usuarios')
    else:
        form = UsuarioEditForm(instance=usuario)
    return render(request, 'usuario_editar.html', {'form': form, 'usuario': usuario})


@login_required
def deletar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)
    if request.method == 'POST':
        usuario.delete()
        return redirect('listar_usuarios')
    return render(request, 'usuario_excluir.html', {'usuario': usuario})
    