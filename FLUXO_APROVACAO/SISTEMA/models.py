from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class Setor(models.Model):
    """
    Setores da empresa (ex: Financeiro, Engenharia).
    """
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Setor"
        verbose_name_plural = "Setores"
        db_table = "setores"

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    """
    Usuário customizado baseado em AbstractUser.
    - já herda: username, password (hash), email, first_name, last_name, is_active, is_staff, is_superuser
    - já suporta grupos e permissões do Django
    """
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True, blank=True)
    perfil = models.CharField(
        max_length=20,
        choices=[("administrador", "Administrador"), ("padrao", "Padrão")],
        default="padrao",
    )
    criado_em = models.DateTimeField(default=timezone.now)
    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='sistema_usuarios',  # Nome reverso único
        blank=True,
        help_text=('The groups this user belongs to. A user will get all permissions '
                   'granted to each of their groups.'),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='sistema_usuarios',  # Nome reverso único
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"
        db_table = "usuarios"

    def __str__(self):
        return self.username


class Assinatura(models.Model):
    """
    Histórico de assinaturas do usuário.
    """
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
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"
        db_table = "assinaturas"

    def __str__(self):
        return f"{self.usuario.username} - {self.plano} ({self.status})"


class FluxoPadrao(models.Model):
    """
    Fluxos padrão criados por usuários.
    """
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="fluxos_criados")
    criado_em = models.DateTimeField(default=timezone.now)
    atualizado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Fluxo Padrão"
        verbose_name_plural = "Fluxos Padrões"
        db_table = "fluxos"

    def __str__(self):
        return self.nome


class EtapaFluxo(models.Model):
    """
    Etapas do fluxo, vinculadas a setor e perfil aprovador.
    """
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
        verbose_name = "Etapa do Fluxo"
        verbose_name_plural = "Etapas do Fluxo"
        db_table = "etapas_fluxo"
        unique_together = ("fluxo", "ordem_etapa")
        ordering = ["fluxo", "ordem_etapa"]

    def __str__(self):
        return f"{self.fluxo.nome} - Etapa {self.ordem_etapa}: {self.nome}"


class AcaoFluxo(models.Model):
    """
    Ações possíveis em uma movimentação (ex.: aprovado, rejeitado).
    """
    nome = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Ação de Fluxo"
        verbose_name_plural = "Ações de Fluxo"
        db_table = "acoes_fluxo"

    def __str__(self):
        return self.nome


class MovimentacaoFluxo(models.Model):
    """
    Histórico das movimentações de um fluxo.
    """
    fluxo = models.ForeignKey(FluxoPadrao, on_delete=models.CASCADE, related_name="movimentacoes")
    etapa = models.ForeignKey(EtapaFluxo, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes")
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimentacoes")
    acao = models.ForeignKey(AcaoFluxo, on_delete=models.SET_NULL, null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)
    data_acao = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Movimentação do Fluxo"
        verbose_name_plural = "Movimentações do Fluxo"
        db_table = "movimentacoes_fluxo"
        ordering = ["-data_acao"]

    def __str__(self):
        usuario = self.usuario.username if self.usuario else "Sistema"
        return f"{self.fluxo.nome} | {self.etapa.nome if self.etapa else '—'} | {self.acao.nome if self.acao else '—'} por {usuario}"
