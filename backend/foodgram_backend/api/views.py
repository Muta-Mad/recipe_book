from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly 
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action

from recipes.models import Tag, Recipe, Ingredient, Favorite, ShoppingCart
from users.models import CustomUser, Subscribe
from .serializers import (
    UsersSerializer, CustomAvatarSerializer,
    TagSerializer, RecipeCreateSerializer,
    IngredientsSerializer, GetSubscribeSerializer, ShoppingCartSerializer, FavoriteSerializer, SubscribeSerializer, RecipeGet
)
from .permission import CustomUsersPermission
from .mixins import ListRetrieveViewSet
from .paginator import CustomPageNumberPagination
from .filters import IngredientFilter, RecipeFilter

PAGE_SIZE = 10

class CustomUsersViewSet(UserViewSet):
    serializer_class = UsersSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (CustomUsersPermission,)
    pagination_class = CustomPageNumberPagination

    @action(
        methods=('PUT', 'DELETE'),
        detail=False,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = CustomAvatarSerializer(instance=user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': user.avatar.url})
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('POST', 'DELETE',),
        detail=True,
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
        if request.method == 'POST':
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
        if request.method == 'DELETE':
            subscription = Subscribe.objects.filter(
                user=request.user,
                author=author
            )
            if not subscription.exists():
                return Response(
                    {'detail': 'Вы не были подписаны на этого пользователя!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        url_path='subscriptions',
        pagination_class=CustomPageNumberPagination
    )
    def subscriptions(self, request):
        followers = CustomUser.objects.filter(
            subscribers__user=request.user
        )
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = GetSubscribeSerializer(
                page, many=True, context={'request': request}
            )
        return self.get_paginated_response(serializer.data)


class TagViewSet(ListRetrieveViewSet):
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PageNumberPagination
    page_size = 10
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGet
        return RecipeCreateSerializer

    @action(
        methods=('GET',),
        detail=True,
        url_path='get-link',
    )
    def get_short_link(self, request, pk):
        """Генерация короткой ссылки на рецепт."""
        get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f'/recipes/{pk}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    @action(
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'user': request.user.id, 'recipe': recipe.id},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
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

    @action(
        methods=('POST', 'DELETE'),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='favorite'
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'user': request.user.id, 'recipe': recipe.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe)
            if not favorite.exists():
                return Response(
                    {'detail': 'Рецепт не был в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientsViewSet(ListRetrieveViewSet):
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
