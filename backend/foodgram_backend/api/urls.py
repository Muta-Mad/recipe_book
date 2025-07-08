from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from .views import CustomUsersViewSet, AvatarView, TagsViewset, RecepeCreateView

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register(r'users', CustomUsersViewSet, basename='users')
router_v1.register('tags', TagsViewset, basename='tags')
router_v1.register('recipes', RecepeCreateView, basename='recipes')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
