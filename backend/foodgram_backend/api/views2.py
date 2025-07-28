from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from recipes.models import Tag, Recipe, Ingredient, Favorite, ShoppingCart
from users.models import CustomUser, Subscribe
from .serializers import (
    UsersSerializer, CustomAvatarSerializer,
    TagSerializer, RecipeCreateSerializer,
    IngredientsSerializer, GetSubscribeSerializer, ShoppingCartSerializer, FavoriteSerializer, SubscribeSerializer, RecipeGet
)
from .permission import CustomUsersPermission

PAGE_SIZE = 10

class CustomUsersViewSet(UserViewSet):
    serializer_class = UsersSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (CustomUsersPermission,)


class AvatarView(APIView):
    permission_classes = (IsAuthenticated,)
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


class TagsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, id=None):
        if id is not None:
            tag = get_object_or_404(Tag, id=id)
            serializer = TagSerializer(tag)
            return Response(serializer.data, status=status.HTTP_200_OK)
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeCreateView(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    permission_classes = (IsAuthenticated,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PageNumberPagination
    page_size = 10
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author',)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeGet

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {'detail': 'У вас нет прав для удаления этого рецепта'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, id=None):
        if id is not None:
            ingredient = get_object_or_404(Ingredient, id=id)
            serializer = IngredientsSerializer(ingredient)
            return Response(serializer.data, status=status.HTTP_200_OK)
        name = request.query_params.get('name')
        ingredients = Ingredient.objects.all()
        if name:
            ingredients = ingredients.filter(name__istartswith=name)
        serializer = IngredientsSerializer(ingredients, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubscribeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, user_id):
        """Подписаться на пользователя."""
        author = get_object_or_404(CustomUser, id=user_id)
        serializer = SubscribeSerializer(
            data={
                'user': request.user.id,
                'author': author.id
            },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        """Отписаться от пользователя."""
        author = get_object_or_404(CustomUser, id=user_id)
        subscription = Subscribe.objects.filter(
            user=request.user,
            author=author)
        if not subscription.exists():
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetSubscription(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        followers = CustomUser.objects.filter(
            subscribing__author=request.user
        )
        serializer = GetSubscribeSerializer(followers, many=True)
        return Response(serializer.data)


class FavoriteAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
        if not favorite.exists():
            return Response(
                {'detail': 'Рецепт не был в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        cart = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe)
        if not cart.exists():
            return Response(
                {'detail': 'Рецепт не был в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
