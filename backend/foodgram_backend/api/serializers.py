from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import CustomUser, Subscribe


class UsersSerializer(UserSerializer):
    """Сериализатор для получения данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

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


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецепте."""
    id = serializers.IntegerField()
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


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта (POST/PATCH)."""
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
        required=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True
    )
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=1,
        error_messages={
            'min_value': 'Время приготовления должно быть больше 1'
        }
    )

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def validate(self, data):
        """Основная валидация данных."""
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                {'ingredients': 'Обязательное поле.'}
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                {'tags': 'Обязательное поле.'}
            )
        return data

    def validate_tags(self, value):
        """Валидация тегов."""
        if not value:
            raise serializers.ValidationError(
                'Поле не должно быть пустым.'
            )

        checked_tags = []
        for tag in value:
            if tag.id in checked_tags:
                raise serializers.ValidationError(
                    'Теги не должны повторяться!'
                )
            checked_tags.append(tag.id)
        return value

    def validate_ingredients(self, value):
        """Валидация ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Поле не должно быть пустым.'
            )

        checked_ids = []
        for ingredient in value:
            if ingredient['id'] in checked_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться!'
                )
            checked_ids.append(ingredient['id'])
        return value

    def create(self, validated_data):
        """Создание рецепта."""
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')

        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)

        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('recipe_ingredients', None)

        if tags is not None:
            instance.tags.set(tags)

        if ingredients_data is not None:

            RecipeIngredient.objects.filter(recipe=instance).delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )

        for field in ['name', 'text', 'cooking_time', 'image']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()
        return instance

    def to_representation(self, instance):
        """Возвращаем данные в формате для чтения."""
        return RecipeGet(instance, context=self.context).data


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
    image = Base64ImageField()

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
