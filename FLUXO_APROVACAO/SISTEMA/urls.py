from django.urls import path
from .views import login_view, home_view, logout_view, criar_usuario, listar_usuarios, editar_usuario, deletar_usuario, listar_setores, criar_setor, editar_setor, deletar_setor, listar_modelos_fluxo, criar_modelos_fluxo, excluir_modelos_fluxo, listar_instancias_fluxo, criar_instancia_fluxo, excluir_instancias_fluxo, mover_etapa, detalhar_instancia_fluxo

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
    path('logout/', logout_view, name='logout'),
    path('users/criar', criar_usuario, name='criar_usuario' ),
    path('users/', listar_usuarios, name='listar_usuarios'),
    path('usuarios/editar/<int:id>/', editar_usuario, name='editar_usuario'),
    path('usuarios/deletar/<int:id>/', deletar_usuario, name='deletar_usuario'),
    path('setores/', listar_setores, name='listar_setores'),
    path('setores/criar/', criar_setor, name='criar_setor'),
    path('setores/editar/<int:id>/', editar_setor, name='editar_setor'),
    path('setores/deletar/<int:id>/', deletar_setor, name='deletar_setor'),
    path('fluxos/modelos/', listar_modelos_fluxo, name='listar_modelos_fluxo'),
    path('fluxos/modelos/novo/', criar_modelos_fluxo, name='criar_modelos_fluxo'),
    path('fluxos/modelos/excluir/<int:id>/', excluir_modelos_fluxo, name='excluir_modelos_fluxo'),
    path('fluxos/instancias/', listar_instancias_fluxo, name='listar_instancias_fluxo'),
    path('fluxos/instancias/novo/', criar_instancia_fluxo, name='criar_instancia_fluxo'),
    path('fluxos/instancias/excluir/<int:id>/', excluir_instancias_fluxo, name='excluir_instancias_fluxo'),
    path('fluxos/instancias/<int:instancia_id>/mover/<int:etapa_id>/', mover_etapa, name='mover_etapa'),
    path('fluxos/instancias/<int:id>/', detalhar_instancia_fluxo, name='detalhar_instancia_fluxo'),
 
]