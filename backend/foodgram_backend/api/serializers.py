from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscribe
from .constants import (
    AMOUNT_MIN_VALUE,
    AMOUNT_MAX_VALUE,
    COOKING_TIME_MIN_VALUE,
    COOKING_TIME_MAX_VALUE,
)


class UsersSerializer(UserSerializer):
    """Сериализатор для получения данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta():
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class CustomUsersCreateSerializer(UserCreateSerializer):
    """Сериализатор для регистрации нового пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta():
        model = CustomUser
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password',
        )


class CustomAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""
    avatar = Base64ImageField(required=True)

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def validate(self, data):
        if 'avatar' not in data:
            raise serializers.ValidationError('Обязательное поле.')
        return data

    def update(self, instance, validated_data):
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте (чтение)."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True,)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть не меньше 1'
            )
        return value


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
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author',
                  'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time',
                  )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Recipe.objects.filter(
            favor_recipe__user=user, id=obj.id
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Recipe.objects.filter(
            shpg_recipe__user=user, id=obj.id
        ).exists()


class RecipeIngredientInputSerializer(serializers.Serializer):
    """Сериализатор только для ввода ингредиентов (create/update)."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        error_messages={
            'does_not_exist': 'Ингредиента с таким id не существует.',
        }
    )
    amount = serializers.IntegerField(
        min_value=AMOUNT_MIN_VALUE,
        max_value=AMOUNT_MAX_VALUE,
        error_messages={
            'min_value': f'Количество не может быть меньше {AMOUNT_MIN_VALUE}.',
            'max_value': f'Количество не может превышать {AMOUNT_MAX_VALUE}.',
            'invalid': 'Введите целое число.'
        },
    )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта (POST/PATCH)."""
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientInputSerializer(
        many=True,
        required=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    text = serializers.CharField(required=True,)
    cooking_time = serializers.IntegerField(
        min_value=COOKING_TIME_MIN_VALUE,
        max_value=COOKING_TIME_MAX_VALUE,
        error_messages={
            'min_value': (
                'Время готовки не может быть меньше '
                f'{COOKING_TIME_MIN_VALUE} минуты'
            ),
            'max_value': (
                'Время готовки не может превышать '
                f'{COOKING_TIME_MAX_VALUE} минут'
            ),
        }
    )

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time',
                  )

    def _update_create_ingredients(self, recipe, ingredients_data):
        """Метод для обновления и создания ингредиентов."""

        recipe.ingredients.clear()

        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    @transaction.atomic
    def create(self, validated_data):
        """Обработка ингредиентов и тегов при создании."""
        request = self.context.get('request')
        author = request.user if request else None
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags_data)
        self._update_create_ingredients(recipe, ingredients_data)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обработка ингредиентов и тегов при обновлении."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        recipe = super().update(instance, validated_data)
        recipe.tags.set(tags_data)
        self._update_create_ingredients(recipe, ingredients_data)

        return recipe

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError('Обязательное поле.')
        seen_ids = set()
        for ing in ingredients:
            ingredient_obj = ing['id']
            ingredient_pk = getattr(ingredient_obj, 'pk', ingredient_obj)
            if ingredient_pk in seen_ids:
                raise serializers.ValidationError('Ингредиенты не должны повторяться!')
            seen_ids.add(ingredient_pk)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError('Обязательное поле.')
        checked_tags = []
        for tag_id in tags:
            if tag_id in checked_tags:
                raise serializers.ValidationError('Теги не должны повторяться!')
            checked_tags.append(tag_id)
        return tags

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Обязательное поле.')
        return value

    def validate_cooking_time(self, value):
        if value < COOKING_TIME_MIN_VALUE:
            raise serializers.ValidationError(
                f'Время приготовление должно быть ">= {COOKING_TIME_MIN_VALUE}"'
            )
        if value > COOKING_TIME_MAX_VALUE:
            raise serializers.ValidationError(
                f'Время приготовление должно быть "<= {COOKING_TIME_MAX_VALUE}"'
            )
        return value

    def to_representation(self, instance):
        return RecipeGet(instance, context=self.context).data

    def validate(self, attrs):
        if self.context['request'].method == 'PATCH':
            if 'ingredients' not in attrs:
                raise serializers.ValidationError('Обязательное поле.')
            if 'tags' not in attrs:
                raise serializers.ValidationError('Обязательное поле.')
        return attrs


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


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

    def validate_author(self, value):
        user = self.context.get('request').user
        if value == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!'
            )
        return value

    def to_representation(self, instance):
        return GetSubscribeSerializer(
            instance.author, context=self.context).data


class GetSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода подписок."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed',
                  'avatar', 'recipes', 'recipes_count'
                  )

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'request').query_params.get(
                'recipes_limit'
        )
        queryset = obj.recipes.all()
        if recipes_limit:
            queryset = queryset[:int(recipes_limit)]
        return ShortRecipeSerializer(
            queryset,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(
                user=request.user,
                author=obj
            ).exists()
        return False


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого вывода рецепта."""
    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class FavoriteSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe, context=self.context).data
