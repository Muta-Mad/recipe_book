from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from .views import CustomUsersViewSet, AvatarView, TagsViewSet, RecipeCreateView, IngredientsViewSet, SubscribeView, GetSubscription, FavoriteAPIView, ShoppingCartAPIView

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'users', CustomUsersViewSet, basename='users')
router_v1.register('tags', TagsViewSet, basename='tags')
router_v1.register('recipes', RecipeCreateView, basename='recipes')
router_v1.register('ingredients', IngredientsViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/<int:id>/favorite/', FavoriteAPIView.as_view(), name='favorite'),
    path('recipes/<int:id>/shopping_cart/', ShoppingCartAPIView.as_view(), name='shopping_cart'),
    path("users/subscriptions/", GetSubscription.as_view(), name="subscriptions"),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_v1.urls)),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
    path("users/<int:user_id>/subscribe/", SubscribeView.as_view(), name="subscribe")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
