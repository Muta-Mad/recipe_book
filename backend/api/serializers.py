from __future__ import annotations

from typing import Any, Optional

from drf_extra_fields.fields import Base64ImageField
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.validators import UniqueTogetherValidator
from users.models import Subscribe, User


class UsersSerializer(serializers.ModelSerializer):
    """Сериализатор для получения данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj: User) -> bool:
        # Если в контексте есть prefetch-набор — используем его (O(1), без SQL)
        subscribed_ids: Optional[set[int]] = self.context.get('subscribed_ids')
        if subscribed_ids is not None:
            return obj.pk in subscribed_ids
        request: Optional[Request] = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Subscribe.objects.filter(user=request.user, author=obj).exists()
        )


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте (чтение)."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGet(serializers.ModelSerializer):
    """Сериализатор для безопасного чтения рецепта (GET-запросы)."""

    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj: Recipe) -> bool:
        favorited_ids: Optional[set[int]] = self.context.get('favorited_ids')
        if favorited_ids is not None:
            return obj.pk in favorited_ids
        request: Optional[Request] = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and Favorite.objects.filter(user=request.user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        cart_ids: Optional[set[int]] = self.context.get('cart_ids')
        if cart_ids is not None:
            return obj.pk in cart_ids
        request: Optional[Request] = self.context.get('request')
        return (
            request is not None
            and request.user.is_authenticated
            and ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()
        )


class RecipeIngredientInputSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте (запись)."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта (POST/PATCH)."""

    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientInputSerializer(required=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    text = serializers.CharField(required=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text', 'cooking_time')

    def _set_ingredients(self, recipe: Recipe, ingredients_data: list[dict]) -> None:
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def create(self, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe: Recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._set_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance: Recipe, validated_data: dict) -> Recipe:
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        super().update(instance, validated_data)
        instance.tags.set(tags_data)
        self._set_ingredients(instance, ingredients_data)
        return instance

    def validate_name(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError('Название не может быть пустым.')
        return value

    def validate_text(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError('Описание не может быть пустым.')
        return value

    def validate(self, data: dict) -> dict:
        # На PATCH (partial=True) — ingredients и tags всё равно обязательны
        if self.instance is not None:
            if 'ingredients' not in data:
                raise serializers.ValidationError(
                    {'ingredients': 'Обязательное поле.'}
                )
            if 'tags' not in data:
                raise serializers.ValidationError({'tags': 'Обязательное поле.'})

        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': 'Список ингредиентов не может быть пустым.'}
            )
        ids = [item['ingredient'].id for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                {'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Список тегов не может быть пустым.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        return data

    def to_representation(self, instance: Recipe) -> dict:
        return RecipeGet(instance, context=self.context).data


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого вывода рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки на пользователя."""

    class Meta:
        model = Subscribe
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя!'
            )
        ]

    def validate_author(self, value: User) -> User:
        if value == self.context['request'].user:
            raise serializers.ValidationError('Нельзя подписаться на самого себя!')
        return value

    def to_representation(self, instance: Subscribe) -> dict:
        return GetSubscribeSerializer(instance.author, context=self.context).data


class GetSubscribeSerializer(UsersSerializer):
    """Сериализатор для вывода подписок с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UsersSerializer.Meta):
        fields = UsersSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes_count(self, obj: User) -> int:
        if hasattr(obj, 'recipes_count'):
            return obj.recipes_count  # type: ignore[attr-defined]
        return obj.recipes.count()

    def get_recipes(self, obj: User) -> list[Any]:
        limit_str: Optional[str] = self.context.get('request').query_params.get(
            'recipes_limit'
        )
        recipes: list = list(obj.recipes.all())
        if limit_str:
            try:
                limit = int(limit_str)
                if limit > 0:
                    recipes = recipes[:limit]
            except ValueError:
                pass
        return ShortRecipeSerializer(recipes, many=True, context=self.context).data


class _UserRecipeRelationSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для Favorite/ShoppingCart."""

    def to_representation(self, instance: Any) -> dict:
        return ShortRecipeSerializer(instance.recipe, context=self.context).data


class FavoriteSerializer(_UserRecipeRelationSerializer):
    """Сериализатор для добавления рецепта в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в списке избранных!'
            )
        ]


class ShoppingCartSerializer(_UserRecipeRelationSerializer):
    """Сериализатор для добавления рецепта в корзину покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже есть в списке покупок!'
            )
        ]
