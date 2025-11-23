# SISTEMA/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import LoginForm, UsuarioCreateForm, UsuarioEditForm, SetorForm, FluxoPadraoForm, InstanciaFluxoForm
from .models import Usuario, Setor, FluxoPadrao, EtapaFluxo, FluxoInstancia, EtapaInstancia, MovimentacaoFluxo, AcaoFluxo, Assinatura
from django.conf import settings
from abacatepay import AbacatePay, AbacatePayClient
from abacatepay.products import Product
import os, requests
from django.http import HttpResponse
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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
    """Lista fluxos em andamento e finalizados."""
    em_andamento = FluxoInstancia.objects.filter(finalizado=False).order_by('-criado_em')
    finalizados = FluxoInstancia.objects.filter(finalizado=True).order_by('-criado_em')

    return render(request, 'instancia_fluxo_listar.html', {
        'em_andamento': em_andamento,
        'finalizados': finalizados,
    })


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

@login_required
def detalhar_instancia_fluxo(request, id):
    """
    Mostra detalhes de uma instância de fluxo, timeline (etapas) e histórico.
    """
    instancia = get_object_or_404(FluxoInstancia, id=id)
    # carregar etapas da instância em ordem
    etapas = instancia.etapas.order_by('ordem_etapa')

    # garantir que se todas as etapas estiverem concluídas o fluxo seja marcado finalizado
    if etapas.exists() and all(e.concluida for e in etapas):
        if not instancia.finalizado:
            instancia.finalizado = True
            instancia.save()

    # encontrar etapa atual: primeira etapa não concluída
    etapa_atual = None
    for e in etapas:
        if not e.concluida:
            etapa_atual = e
            break

    # carregar histórico
    movimentacoes = instancia.movimentacoes.order_by('-data_acao')

    return render(request, 'instancia_fluxo_detalhar.html', {
        'instancia': instancia,
        'etapas': etapas,
        'etapa_atual': etapa_atual,
        'movimentacoes': movimentacoes,
    })


@login_required
def mover_etapa(request, instancia_id, etapa_id):
    """
    Recebe POST com acao in ('avancar','retornar') e comentario.
    Realiza a movimentação, atualiza EtapaInstancia e FluxoInstancia e registra MovimentacaoFluxo.
    """
    if request.method != 'POST':
        return redirect('detalhar_instancia_fluxo', id=instancia_id)

    instancia = get_object_or_404(FluxoInstancia, id=instancia_id)
    etapa = get_object_or_404(EtapaInstancia, id=etapa_id, fluxo_instancia=instancia)

    acao_nome = request.POST.get('acao')
    comentario = request.POST.get('comentario', '').strip()

    # garantir objetos de ação (nome em pt: Avançar / Retornar)
    acao_avancar, _ = AcaoFluxo.objects.get_or_create(nome='Avançar')
    acao_retornar, _ = AcaoFluxo.objects.get_or_create(nome='Retornar')

    if acao_nome == 'avancar':
        # se já foi concluída, não faz nada
        if etapa.concluida:
            messages.warning(request, 'Esta etapa já está concluída.')
            return redirect('detalhar_instancia_fluxo', id=instancia.id)

        # marcar etapa atual como concluída
        etapa.concluida = True
        etapa.save()

        # criar movimentação
        MovimentacaoFluxo.objects.create(
            fluxo_instancia=instancia,
            etapa=etapa,
            usuario=request.user,
            acao=acao_avancar,
            comentario=comentario,
            data_acao=timezone.now()
        )

        # ver se existe próxima etapa
        proximas = instancia.etapas.filter(ordem_etapa__gt=etapa.ordem_etapa).order_by('ordem_etapa')
        if not proximas.exists():
            # se não há próxima etapa, finalizar o fluxo
            instancia.finalizado = True
            instancia.save()
            messages.success(request, f'Instância "{instancia.nome}" finalizada.')
        else:
            # próxima etapa ficará como pendente (já está criada como pendente por padrão)
            prox = proximas.first()
            messages.success(request, f'Instância avançada para etapa "{prox.nome}".')

        return redirect('detalhar_instancia_fluxo', id=instancia.id)

    elif acao_nome == 'retornar':
        # não é possível retornar da primeira etapa
        if etapa.ordem_etapa == 1:
            messages.warning(request, 'Não é possível retornar: esta é a primeira etapa.')
            return redirect('detalhar_instancia_fluxo', id=instancia.id)

        # encontra etapa anterior
        anterior = instancia.etapas.filter(ordem_etapa=etapa.ordem_etapa - 1).first()
        if not anterior:
            messages.error(request, 'Etapa anterior não encontrada.')
            return redirect('detalhar_instancia_fluxo', id=instancia.id)

        # marcar etapa atual como não concluída (reabre) e também reabrir anterior
        etapa.concluida = False
        etapa.save()

        anterior.concluida = False
        anterior.save()

        # se estava finalizado, desfaz finalizado
        if instancia.finalizado:
            instancia.finalizado = False
            instancia.save()

        # registrar movimentação
        MovimentacaoFluxo.objects.create(
            fluxo_instancia=instancia,
            etapa=anterior,
            usuario=request.user,
            acao=acao_retornar,
            comentario=comentario,
            data_acao=timezone.now()
        )

        messages.success(request, f'Instância retornada para etapa "{anterior.nome}".')
        return redirect('detalhar_instancia_fluxo', id=instancia.id)

    else:
        messages.error(request, 'Ação inválida.')
        return redirect('detalhar_instancia_fluxo', id=instancia.id)

ABACATE_URL = "https://api.abacatepay.com/v1/billing/create"
API_KEY = os.getenv("ABACATEPAY_API_KEY") or getattr(settings, "ABACATEPAY_API_KEY", None)

@login_required
def assinatura_view(request):
    return render(request, 'assinaturas.html')  

@login_required
def checkout_prata(request):
    url = ABACATE_URL
    payload = {
        "frequency": "MULTIPLE_PAYMENTS",
        "methods": ["PIX"],
        "products": [
            {
                "externalId": "1",  # prata = 1
                "name": "Assinatura Prata",
                "description": "Plano Prata - 30 dias",
                "quantity": 1,
                "price": 8990  # centavos = R$89,90
            }
        ],
        "returnUrl": "http://127.0.0.1:8000/assinatura/",
        "completionUrl": "http://127.0.0.1:8000/assinatura/",
        "customer": {
            "name": request.user.get_full_name() or request.user.username,
            "cellphone": "11999999999",
            "email": "cliente@teste.com",
            "taxId": "39053344705"
        },
        "allowCoupons": False,
        "metadata": {"usuario_id": str(request.user.id)}
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        if data.get("data") and "url" in data["data"]:
            return redirect(data["data"]["url"])
        else:
            return HttpResponse(f"Erro ao criar checkout: {data}", status=response.status_code)
    except Exception as e:
        return HttpResponse(f"Erro inesperado: {e}", status=500)

@login_required
def checkout_ouro(request):
    url = ABACATE_URL
    payload = {
        "frequency": "MULTIPLE_PAYMENTS",
        "methods": ["PIX"],
        "products": [
            {
                "externalId": "2",  # ouro = 2
                "name": "Assinatura Ouro",
                "description": "Plano Ouro - 30 dias",
                "quantity": 1,
                "price": 11990  # centavos = R$119,90
            }
        ],
        "returnUrl": "http://127.0.0.1:8000/assinatura/",
        "completionUrl": "http://127.0.0.1:8000/assinatura/",
        "customer": {
            "name": request.user.get_full_name() or request.user.username,
            "cellphone": "11999999999",
            "email": "cliente@teste.com",
            "taxId": "39053344705"
        },
        "allowCoupons": False,
        "metadata": {"usuario_id": str(request.user.id)}
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        data = response.json()
        if data.get("data") and "url" in data["data"]:
            return redirect(data["data"]["url"])
        else:
            return HttpResponse(f"Erro ao criar checkout: {data}", status=response.status_code)
    except Exception as e:
        return HttpResponse(f"Erro inesperado: {e}", status=500)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or getattr

@csrf_exempt
def abacatepay_webhook(request):
    # Valida o secret
    secret = request.GET.get("secret") or request.GET.get("webhookSecret")
    if secret != WEBHOOK_SECRET:
        return JsonResponse({"error": "invalid secret"}, status=401)

    # Lê o JSON enviado pelo AbacatePay
    try:
        payload = json.loads(request.body)

        print("\n===== WEBHOOK RECEBIDO =====")
        print(json.dumps(payload, indent=4))
        print("============================\n")

    except Exception:
        return JsonResponse({"error": "invalid json"}, status=400)

    # Só processa pagamento confirmado
    if payload.get("event") != "billing.paid":
        return JsonResponse({"status": "ignored", "reason": "not billing.paid"}, status=200)

    billing = payload["data"]["billing"]
    products = billing.get("products", [])
    metadata = billing.get("metadata", {})

    # Pega usuário_id do metadata (o mais importante!)
    usuario_id = metadata.get("usuario_id")
    if not usuario_id:
        print("⚠️ metadata.usuario_id não veio no payload!")
        return JsonResponse({"status": "ignored", "reason": "no usuario_id"}, status=200)

    # Acha o usuário
    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return JsonResponse({"status": "ignored", "reason": "usuario_not_found"}, status=200)

    # Pega externalId para saber qual plano foi comprado
    external_id = None
    if products:
        external_id = products[0].get("externalId")

    # Mapea externalId → plano
    plano = None
    if str(external_id) == "1":
        plano = "prata"
    elif str(external_id) == "2":
        plano = "ouro"
    else:
        plano = "freemium"  # fallback

    # Cria ou atualiza assinatura
    assinatura, created = Assinatura.objects.update_or_create(
        usuario=usuario,
        defaults={
            "plano": plano,
            "status": "ativo",
            "data_inicio": timezone.localdate(),
            "data_fim": None  # ignorando expiração
        }
    )

    return JsonResponse({"status": "saved", "plano": plano}, status=200)