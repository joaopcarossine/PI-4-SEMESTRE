from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# ==========================================================
# ESTRUTURA ORGANIZACIONAL
# ==========================================================
class Setor(models.Model):
    """Setores da empresa (ex: Financeiro, Engenharia)."""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "setores"
        verbose_name = "Setor"
        verbose_name_plural = "Setores"

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    """Usuário customizado com vínculo a setor e perfil."""
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    perfil = models.CharField(
        max_length=20,
        choices=[("administrador", "Administrador"), ("padrao", "Padrão")],
        default="padrao",
    )
    criado_em = models.DateTimeField(default=timezone.now)

    # Corrige conflitos de nomes reversos do Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuarios_sistema',
        blank=True,
        help_text='Grupos do Django.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuarios_sistema',
        blank=True,
        help_text='Permissões específicas.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = "usuarios"
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.username


# ==========================================================
# ASSINATURA / LICENCIAMENTO
# ==========================================================
class Assinatura(models.Model):
    """Histórico de assinaturas do usuário."""
    PLANO_CHOICES = [
        ("freemium", "Freemium"),
        ("premium", "Premium"),
    ]
    STATUS_CHOICES = [
        ("ativo", "Ativo"),
        ("inativo", "Inativo"),
        ("cancelado", "Cancelado"),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="assinaturas")
    plano = models.CharField(max_length=20, choices=PLANO_CHOICES)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ativo")
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "assinaturas"
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"

    def __str__(self):
        return f"{self.usuario.username} - {self.plano} ({self.status})"


# ==========================================================
# FLUXO PADRÃO (MODELO / TEMPLATE)
# ==========================================================
class FluxoPadrao(models.Model):
    """Modelos de fluxo criados pelos administradores."""
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "fluxos_padrao"
        verbose_name = "Fluxo Padrão"
        verbose_name_plural = "Fluxos Padrões"

    def __str__(self):
        return self.nome


class EtapaFluxo(models.Model):
    """Etapas definidas dentro do fluxo padrão."""
    fluxo = models.ForeignKey(FluxoPadrao, on_delete=models.CASCADE, related_name="etapas")
    ordem_etapa = models.PositiveIntegerField()
    nome = models.CharField(max_length=200)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    perfil_aprovador = models.CharField(
        max_length=20,
        choices=[("administrador", "Administrador"), ("padrao", "Padrão")],
        default="padrao",
    )
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "etapas_fluxo"
        verbose_name = "Etapa do Fluxo"
        verbose_name_plural = "Etapas do Fluxo"
        unique_together = ("fluxo", "ordem_etapa")
        ordering = ["fluxo", "ordem_etapa"]

    def __str__(self):
        return f"{self.fluxo.nome} - Etapa {self.ordem_etapa}: {self.nome}"


# ==========================================================
# INSTÂNCIAS (FLUXOS REAIS EM EXECUÇÃO)
# ==========================================================
class FluxoInstancia(models.Model):
    """Execução real de um fluxo baseado em um modelo padrão."""
    modelo = models.ForeignKey(FluxoPadrao, on_delete=models.CASCADE, related_name="instancias")
    nome = models.CharField(max_length=200)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(auto_now=True)
    finalizado = models.BooleanField(default=False)

    class Meta:
        db_table = "fluxos_instancia"
        verbose_name = "Fluxo em Execução"
        verbose_name_plural = "Fluxos em Execução"

    def __str__(self):
        return f"{self.nome} (baseado em {self.modelo.nome})"


class EtapaInstancia(models.Model):
    """Etapas reais, clonadas do modelo, para controle de status."""
    fluxo_instancia = models.ForeignKey(FluxoInstancia, on_delete=models.CASCADE, related_name="etapas")
    ordem_etapa = models.PositiveIntegerField()
    nome = models.CharField(max_length=200)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    perfil_aprovador = models.CharField(
        max_length=20,
        choices=[("administrador", "Administrador"), ("padrao", "Padrão")],
        default="padrao",
    )
    concluida = models.BooleanField(default=False)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "etapas_instancia"
        verbose_name = "Etapa da Instância"
        verbose_name_plural = "Etapas da Instância"
        unique_together = ("fluxo_instancia", "ordem_etapa")
        ordering = ["fluxo_instancia", "ordem_etapa"]

    def __str__(self):
        return f"{self.fluxo_instancia.nome} - Etapa {self.ordem_etapa}: {self.nome}"


# ==========================================================
# AÇÕES E MOVIMENTAÇÕES
# ==========================================================
class AcaoFluxo(models.Model):
    """Ações possíveis em uma movimentação (ex.: aprovado, rejeitado)."""
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "acoes_fluxo"
        verbose_name = "Ação de Fluxo"
        verbose_name_plural = "Ações de Fluxo"

    def __str__(self):
        return self.nome


class MovimentacaoFluxo(models.Model):
    """Histórico das ações realizadas dentro de uma instância de fluxo."""
    fluxo_instancia = models.ForeignKey(
        FluxoInstancia,
        on_delete=models.CASCADE,
        related_name="movimentacoes",
        null=True,  # Permite migração limpa
        blank=True
    )
    etapa = models.ForeignKey(EtapaInstancia, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.ForeignKey(AcaoFluxo, on_delete=models.SET_NULL, null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)
    data_acao = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "movimentacoes_fluxo"
        verbose_name = "Movimentação do Fluxo"
        verbose_name_plural = "Movimentações do Fluxo"
        ordering = ["-data_acao"]

    def __str__(self):
        usuario = self.usuario.username if self.usuario else "Sistema"
        return f"{self.fluxo_instancia.nome if self.fluxo_instancia else 'Sem Fluxo'} | {self.etapa.nome if self.etapa else '—'} | {self.acao.nome if self.acao else '—'} por {usuario}"