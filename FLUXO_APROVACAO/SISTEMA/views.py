# SISTEMA/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm, SetorForm, FluxoPadraoForm, InstanciaFluxoForm
from .models import Usuario, Setor, FluxoPadrao, EtapaFluxo, FluxoInstancia, EtapaInstancia

## Login
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

## CRUD do Usuário
@login_required
def criar_usuario(request):
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('listar_usuarios')  
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

## CRUD do Setor
login_required
def listar_setores(request):
    setores = Setor.objects.all().order_by('nome')
    return render(request, 'setor_listar.html', {'setores': setores})

@login_required
def criar_setor(request):
    if request.method == 'POST':
        form = SetorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_setores')
    else:
        form = SetorForm()
    return render(request, 'setor_criar.html', {'form': form, 'titulo': 'Criar Setor'})

@login_required
def editar_setor(request, id):
    setor = get_object_or_404(Setor, id=id)
    if request.method == 'POST':
        form = SetorForm(request.POST, instance=setor)
        if form.is_valid():
            form.save()
            return redirect('listar_setores')
    else:
        form = SetorForm(instance=setor)
    return render(request, 'setor_criar.html', {'form': form, 'titulo': 'Editar Setor'})

@login_required
def deletar_setor(request, id):
    setor = get_object_or_404(Setor, id=id)
    if request.method == 'POST':
        setor.delete()
        return redirect('listar_setores')
    return render(request, 'setor_excluir.html', {'setor': setor})
    
@login_required
def listar_modelos_fluxo(request):
    fluxos = FluxoPadrao.objects.all().order_by('-criado_em')
    return render(request, 'modelos_fluxo_listar.html', {'fluxos': fluxos})

@login_required
def criar_modelos_fluxo(request):
    if request.method == 'POST':
        form = FluxoPadraoForm(request.POST)
        if form.is_valid():
            fluxo = form.save(commit=False)
            fluxo.criado_por = request.user
            fluxo.save()

            # Cria as etapas dinamicamente conforme os campos enviados
            etapas_total = int(request.POST.get('num_etapas', 0))
            for i in range(1, etapas_total + 1):
                nome = request.POST.get(f'etapa_nome_{i}')
                setor_id = request.POST.get(f'etapa_setor_{i}')
                if nome:
                    EtapaFluxo.objects.create(
                        fluxo=fluxo,
                        ordem_etapa=i,
                        nome=nome,
                        setor_id=setor_id if setor_id else None,
                        criado_em=timezone.now()
                    )
            messages.success(request, 'Fluxo modelo criado com sucesso!')
            return redirect('listar_modelos_fluxo')
    else:
        form = FluxoPadraoForm()
    return render(request, 'modelos_fluxo_criar.html', {'form': form, 'setores': Setor.objects.all()})

@login_required
def excluir_modelos_fluxo(request, id):
    fluxo = get_object_or_404(FluxoPadrao, id=id)
    if request.method == 'POST':
        fluxo.delete()
        messages.success(request, 'Modelo de fluxo excluído com sucesso.')
        return redirect('listar_modelos_fluxo')
    return render(request, 'modelos_fluxo_excluir.html', {'fluxo': fluxo})

@login_required
def criar_instancia_fluxo(request):
    if request.method == 'POST':
        form = InstanciaFluxoForm(request.POST)
        if form.is_valid():
            fluxo_padrao = form.cleaned_data['fluxo_padrao']
            nome_instancia = form.cleaned_data['nome_instancia']

            # Cria a nova instância
            fluxo_instancia = FluxoInstancia.objects.create(
                modelo=fluxo_padrao,
                nome=nome_instancia,
                criado_por=request.user
            )

            # Clona as etapas do modelo
            for i, etapa in enumerate(fluxo_padrao.etapas.all(), start=1):
                EtapaInstancia.objects.create(
                    fluxo_instancia=fluxo_instancia,
                    ordem_etapa=i,
                    nome=etapa.nome,
                    setor=etapa.setor,
                    perfil_aprovador=etapa.perfil_aprovador,
                    criado_em=timezone.now()
                )

            messages.success(request, f'Instância "{nome_instancia}" criada com sucesso!')
            return redirect('listar_instancias_fluxo')
    else:
        form = InstanciaFluxoForm()

    return render(request, 'instancia_fluxo_criar.html', {'form': form})

@login_required
def listar_instancias_fluxo(request):
    """
    Lista todas as instâncias de fluxo (fluxos em execução).
    """
    instancias = FluxoInstancia.objects.all().order_by('-criado_em')
    return render(request, 'instancia_fluxo_listar.html', {'instancias': instancias})

@login_required
def excluir_instancias_fluxo(request, id):
    """
    Exclui uma instância de fluxo e suas etapas associadas.
    """
    instancia = get_object_or_404(FluxoInstancia, id=id)

    if request.method == 'POST':
        nome = instancia.nome
        instancia.delete()
        messages.success(request, f'Fluxo "{nome}" excluído com sucesso!')
        return redirect('listar_instancias_fluxo')

    return render(request, 'instancia_fluxo_excluir.html', {'instancia': instancia})
