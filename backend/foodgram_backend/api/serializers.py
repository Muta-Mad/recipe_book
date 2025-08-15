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
    id = serializers.IntegerField(source='ingredient.id')
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


class RecipeIngredientInputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    def validate_id(self, value):
        try:
            Ingredient.objects.get(id=value)
        except Ingredient.DoesNotExist:
            raise serializers.ValidationError(
                f'Ингредиент с ID {value} не существует'
            )
        return value

    def validate_amount(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Количество ингредиента должно быть не меньше 1'
            )
        return value


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта (POST/PATCH)."""
    image = Base64ImageField(required=False)
    ingredients = RecipeIngredientInputSerializer(required=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True,
        required=True,)
    text = serializers.CharField(required=True,)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time',
                  )

    def _update_create_ingredients(self, recipe, ingredients_data):
        print("DEBUG ingredients_data:", ingredients_data)
        # Clear existing ingredients for the recipe
        recipe.recipe_ingredients.all().delete()
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            try:
                ingredient = Ingredient.objects.get(id=ingredient_id)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                )
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиент с ID {ingredient_id} не существует'
                )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self._update_create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        
        # Если изображение не передается, используем существующее
        if 'image' not in validated_data:
            validated_data['image'] = instance.image
            
        recipe = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        self._update_create_ingredients(recipe, ingredients_data)
        return instance

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Обязательное поле.'
            )
        checked_ingredients = []
        for item in ingredients:
            ingredient_id = item['id']
            if ingredient_id in checked_ingredients:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            # Проверяем существование ингредиента
            try:
                Ingredient.objects.get(id=ingredient_id)
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    f'Ингредиент с ID {ingredient_id} не существует'
                )
            checked_ingredients.append(ingredient_id)
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Обязательное поле.'
            )
        сhecked_tags = []
        for tag_id in tags:
            if tag_id in сhecked_tags:
                raise serializers.ValidationError(
                    'Теги не должны повторяться!'
                )
            сhecked_tags.append(tag_id)
        return tags

    def validate_image(self, value):
        if self.context['request'].method == 'POST' and not value:
            raise serializers.ValidationError(
                'Обязательное поле.'
            )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовление должно быть > 1'
            )
        return value

    def to_representation(self, instance):
        return RecipeGet(instance, context=self.context).data

    def validate(self, data):
        if self.context['request'].method == 'PATCH':
            if 'ingredients' not in data:
                raise serializers.ValidationError('Обязательное поле.')
            if 'tags' not in data:
                raise serializers.ValidationError('Обязательное поле.')
        return data


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
