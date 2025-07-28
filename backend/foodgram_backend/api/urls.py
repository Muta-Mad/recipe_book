from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from .views import CustomUsersViewSet, RecipeViewSet, IngredientsViewSet, TagViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('users', CustomUsersViewSet, basename='users')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('ingredients', IngredientsViewSet, basename='ingredients')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
