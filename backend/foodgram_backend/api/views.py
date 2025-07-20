from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from recipes.models import Tag, Recipe, Ingredient, Favorite
from users.models import CustomUser, Subscribe
from .serializers import (
    UsersSerializer, CustomAvatarSerializer,
    TagSerializer, RecipeCreateSerializer,
    IngredientsSerializer, GetSubscribeSerializer
)
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


class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Подписаться на пользователя."""
        author = get_object_or_404(CustomUser, id=user_id)
        user = request.user

        if user == author:
            return Response(
                {'detail': 'Нельзя подписаться на самого себя!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Subscribe.objects.filter(user=user, author=author).exists():
            return Response(
                {'detail': 'Вы уже подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Subscribe.objects.create(user=user, author=author)
        serializer = GetSubscribeSerializer(author, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        """Отписаться от пользователя."""
        author = get_object_or_404(CustomUser, id=user_id)
        user = request.user
        subscription = Subscribe.objects.filter(user=user, author=author)
        if not subscription.exists():
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class GetSubscription(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        followers = CustomUser.objects.filter(
            subscribing__author=user
        )
        serializer = GetSubscribeSerializer(followers, many=True)
        return Response(serializer.data)


class FavoriteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже есть в избранном!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        return Response(
            {'detail': 'Рецепт успешно добавлен в избранное'},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт не был в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(
            {'detail': 'Рецепт успешно удален из избранного'},
            status=status.HTTP_204_NO_CONTENT
        )
