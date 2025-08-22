from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.paginator import PageNumberPagination
from api.permission import IsAuthenticatedAuthorOrReadOnly
from api.serializers import (CustomAvatarSerializer, FavoriteSerializer,
                             GetSubscribeSerializer, IngredientsSerializer,
                             RecipeCreateUpdateSerializer, RecipeGet,
                             ShoppingCartSerializer, SubscribeSerializer,
                             TagSerializer, UsersSerializer)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscribe


class CustomUsersViewSet(UserViewSet):
    """ViewSet для работы с пользователями: регистрация, аватар, подписки."""
    serializer_class = UsersSerializer
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticatedAuthorOrReadOnly,)
    pagination_class = PageNumberPagination

    @action(
        methods=('PUT',),
        detail=False,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        serializer = CustomAvatarSerializer(
            instance=user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'avatar': user.avatar.url})

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('POST',),
        detail=True,
        url_path='subscribe',
    )
    def subscribe(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
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

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        author = get_object_or_404(CustomUser, id=id)
        deleted_count, _ = Subscribe.objects.filter(
            user=request.user,
            author=author
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Вы не были подписаны на этого пользователя!'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        detail=False,
        url_path='subscriptions',
        pagination_class=PageNumberPagination
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


class TagViewSet(viewsets.ReadOnlyModelViewSet):
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
    pagination_class = PageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete')

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipeGet
        return RecipeCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=('GET',),
        detail=True,
        url_path='get-link',
        permission_classes=(AllowAny,)
    )
    def get_short_link(self, request, pk):
        """Выдает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f'/recipes/{recipe.short_code}/')
        return Response({'short-link': link}, status=status.HTTP_200_OK)

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='shopping_cart'
    )
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = ShoppingCartSerializer(
            data={'user': request.user.id, 'recipe': recipe.id},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = ShoppingCart.objects.filter(
            user=request.user,
            recipe=recipe).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Рецепт не был в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('POST',),
        permission_classes=(IsAuthenticated,),
        detail=True,
        url_path='favorite'
    )
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        serializer = FavoriteSerializer(
            data={'user': request.user.id, 'recipe': recipe.id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count, _ = Favorite.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Рецепт не был в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=('GET',),
        permission_classes=(IsAuthenticated,),
        detail=False,
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredients_data = RecipeIngredient.objects.filter(
            recipe__shpg_recipe__user=request.user).values(
                'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        )
        shopping_list_lines = []
        for ingredient in ingredients_data:
            line = (f'- {ingredient["ingredient__name"]}: '
                    f'{ingredient["total_amount"]} '
                    f'{ingredient["ingredient__measurement_unit"]}')
            shopping_list_lines.append(line)
        shopping_list_text = '\n'.join(shopping_list_lines)
        response = HttpResponse(shopping_list_text, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для ингредиентов."""
    permission_classes = (AllowAny,)
    queryset = Ingredient.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
