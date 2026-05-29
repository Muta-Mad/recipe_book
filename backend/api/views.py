from __future__ import annotations

from typing import Any

from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from users.models import Subscribe, User

from api.filters import IngredientFilter, RecipeFilter
from api.paginator import RecipeBookPagination
from api.permission import IsAuthenticatedAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    FavoriteSerializer,
    GetSubscribeSerializer,
    IngredientsSerializer,
    RecipeCreateUpdateSerializer,
    RecipeGet,
    ShoppingCartSerializer,
    SubscribeSerializer,
    TagSerializer,
    UsersSerializer,
)


class UsersProfileViewSet(UserViewSet):
    """ViewSet для работы с пользователями: регистрация, аватар, подписки."""

    serializer_class = UsersSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = RecipeBookPagination

    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_context(self) -> dict:
        ctx = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            ctx['subscribed_ids'] = set(
                Subscribe.objects.filter(user=user).values_list('author_id', flat=True)
            )
        return ctx

    @action(methods=('PUT',), detail=False, url_path='me/avatar')
    def avatar(self, request: Request) -> Response:
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': serializer.instance.avatar.url})

    @avatar.mapping.delete
    def delete_avatar(self, request: Request) -> Response:
        if request.user.avatar:
            request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('POST',), detail=True, url_path='subscribe')
    def subscribe(self, request: Request, id: int) -> Response:
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={'user': request.user.id, 'author': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request: Request, id: int) -> Response:
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Subscribe.objects.filter(
            user=request.user, author=author
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=False, url_path='subscriptions')
    def subscriptions(self, request: Request) -> Response:
        followers: QuerySet[User] = (
            User.objects.filter(subscribers__user=request.user)
            .annotate(recipes_count=Count('recipes'))
            .prefetch_related(
                Prefetch(
                    'recipes',
                    queryset=Recipe.objects.only(
                        'id', 'name', 'image', 'cooking_time', 'author_id'
                    ),
                )
            )
        )
        subscribed_ids = set(
            Subscribe.objects.filter(user=request.user)
            .values_list('author_id', flat=True)
        )
        page = self.paginate_queryset(followers)
        serializer = GetSubscribeSerializer(
            page,
            many=True,
            context={'request': request, 'subscribed_ids': subscribed_ids},
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для получения тегов."""

    permission_classes = (AllowAny,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для рецептов: CRUD + корзина + избранное."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = RecipeBookPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_queryset(self) -> QuerySet[Recipe]:
        return (
            Recipe.objects.select_related('author')
            .prefetch_related(
                'tags',
                Prefetch(
                    'recipe_ingredients',
                    queryset=RecipeIngredient.objects.select_related('ingredient'),
                ),
            )
        )

    def get_serializer_class(self) -> type:
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGet
        return RecipeCreateUpdateSerializer

    def get_serializer_context(self) -> dict:
        ctx = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            ctx['favorited_ids'] = set(
                Favorite.objects.filter(user=user).values_list('recipe_id', flat=True)
            )
            ctx['cart_ids'] = set(
                ShoppingCart.objects.filter(user=user)
                .values_list('recipe_id', flat=True)
            )
            ctx['subscribed_ids'] = set(
                Subscribe.objects.filter(user=user)
                .values_list('author_id', flat=True)
            )
        return ctx

    def perform_create(self, serializer: Any) -> None:
        serializer.save(author=self.request.user)

    # --- Short link ----------------------------------------------------------

    @action(
        methods=('GET',),
        detail=True,
        url_path='get-link',
        url_name='get-link',
        permission_classes=(AllowAny,),
    )
    def get_short_link(self, request: Request, pk: int) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f'/s/{recipe.short_code}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    # --- Shopping cart -------------------------------------------------------

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='shopping_cart',
    )
    def shopping_cart(self, request: Request, pk: int) -> Response:
        return self._add_to_list(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request: Request, pk: int) -> Response:
        return self._remove_from_list(request, pk, ShoppingCart, 'списке покупок')

    # --- Favorites -----------------------------------------------------------

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='favorite',
    )
    def favorite(self, request: Request, pk: int) -> Response:
        return self._add_to_list(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def delete_favorite(self, request: Request, pk: int) -> Response:
        return self._remove_from_list(request, pk, Favorite, 'избранном')

    # --- Download cart -------------------------------------------------------

    @action(
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request: Request) -> HttpResponse:
        from django.db.models import Sum

        rows = (
            RecipeIngredient.objects.filter(
                recipe__shpg_recipe__user=request.user
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = [
            f'- {r["ingredient__name"]}: {r["total_amount"]} '
            f'{r["ingredient__measurement_unit"]}'
            for r in rows
        ]
        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    # --- Helpers -------------------------------------------------------------

    def _add_to_list(
        self, request: Request, pk: int, serializer_class: type
    ) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = serializer_class(
            data={'user': request.user.id, 'recipe': recipe.id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_list(
        self,
        request: Request,
        pk: int,
        model_class: type,
        list_name: str,
    ) -> Response:
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = model_class.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': f'Рецепт не был в {list_name}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


def redirect_short_link(request: Request, short_code: str) -> HttpResponseRedirect:
    recipe = get_object_or_404(Recipe, short_code=short_code)
    return HttpResponseRedirect(f'/recipes/{recipe.id}/')


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""

    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
