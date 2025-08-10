from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import CustomUser, Subscribe

from .filters import IngredientFilter, RecipeFilter
from .mixins import ListRetrieveViewSet
from .paginator import CustomPageNumberPagination
from .permission import IsAuthenticatedAuthorOrReadOnly
from .serializers import (CustomAvatarSerializer, FavoriteSerializer,
                          GetSubscribeSerializer, IngredientsSerializer,
                          RecipeCreateSerializer, RecipeGet,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer, UsersSerializer)


class CustomUsersViewSet(UserViewSet):
    """ViewSet для работы с пользователями: регистрация, аватар, подписки."""
    serializer_class = UsersSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = CustomPageNumberPagination

    @action(
        methods=('PUT', 'DELETE'),
        detail=False,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = CustomAvatarSerializer(
                instance=user,
                data=request.data,
                partial=True
            )
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
    """ViewSet для получения тегов."""
    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов + корзина избранное."""
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = PageNumberPagination
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
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk):
        """Выдает короткую ссылку на рецепт."""
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
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe
            )
            if not favorite.exists():
                return Response(
                    {'detail': 'Рецепт не был в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        cart_recipes = Recipe.objects.filter(shpg_recipe__user=request.user)
        ingredients = {}
        for recipe in cart_recipes:
            for recipe_ingredient in recipe.recipe_ingredients.all():
                name = recipe_ingredient.ingredient.name
                unit = recipe_ingredient.ingredient.measurement_unit
                amount = recipe_ingredient.amount
                ingredient_key = (name, unit)
                if ingredient_key in ingredients:
                    ingredients[ingredient_key] += amount
                else:
                    ingredients[ingredient_key] = amount
        shopping_list = '\n'.join(
            f'- {name}: {amount} {unit}'
            for (name, unit), amount in ingredients.items()
        )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class IngredientsViewSet(ListRetrieveViewSet):
    """ViewSet для ингредиентов."""
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
