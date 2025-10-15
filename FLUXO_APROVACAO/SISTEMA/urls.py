from django.urls import path
from .views import login_view, home_view, logout_view, criar_usuario, listar_usuarios, editar_usuario, deletar_usuario, listar_setores, criar_setor, editar_setor, deletar_setor

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
]