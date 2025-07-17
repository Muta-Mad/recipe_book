from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Tag, Recipe, Ingredient
from users.models import CustomUser
from .serializers import (UsersSerializer, CustomAvatarSerializer, TagSerializer, RecipeCreateSerializer, IngredientsSerializer)
from .permission import CustomUsersPermission
from .mixins import ListRetrieveViewSet

class CustomUsersViewSet(UserViewSet):
    serializer_class = UsersSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (CustomUsersPermission,)

class AvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = CustomAvatarSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': user.avatar.url})

    def delete(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class TagsViewSet(ListRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
      
class RecipeCreateView(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAuthenticated,)


class IngredientsViewSet(ListRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None

 