from django.urls import path
from .views import login_view, home_view, logout_view, criar_usuario, listar_usuarios, editar_usuario, deletar_usuario

urlpatterns = [
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
    path('logout/', logout_view, name='logout'),
    path('users/editar', criar_usuario, name='criar_usuario' ),
    path('users/', listar_usuarios, name='listar_usuarios'),
    path('usuarios/editar/<int:id>/', editar_usuario, name='editar_usuario'),
    path('usuarios/deletar/<int:id>/', deletar_usuario, name='deletar_usuario'),
]