# flake8: noqa: D106
"""Сериализаторы Пользователя."""
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


from users.models import CustomUser, Subscribe
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient, Favorite, ShoppingCart

class UsersSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField()

    class Meta():
        model = CustomUser
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar',
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
    """Кастомный Сериализатор унаследованный от djoser."""

    password = serializers.CharField(write_only=True)

    class Meta():
        model = CustomUser
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password',)


class CustomAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def validate(self, attrs):
        if 'avatar' not in attrs:
            raise serializers.ValidationError({'avatar': 'Обязательное поле.'})
        return attrs


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)

class RecipeIngredientSerializer(serializers.ModelSerializer):
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
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Recipe.objects.filter(favor_recipe__user=user, id=obj.id).exists()
    
    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if not user.is_authenticated:
            return False
        return Recipe.objects.filter(shpg_recipe__user=user, id=obj.id).exists()
    

class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients',
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    text = serializers.CharField(required=True,)
    cooking_time = serializers.IntegerField()


    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text', 'cooking_time',)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        if tags:
            recipe.tags.set(tags)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'], 
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
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
        return instance
    
    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'обязательное поле.'
            )    
        checked_ids = []
        for ing in ingredients:
            ing_id = ing['id']
            if ing_id in checked_ids:
                raise serializers.ValidationError(
                    'ингредиенты не должны повторяться!')
            checked_ids.append(ing_id)

        for ingredient in ingredients:
            try:
                Ingredient.objects.get(id=ingredient['id'])
            except Ingredient.DoesNotExist:
                raise serializers.ValidationError(
                    'у нас такого ингридиента нет'
               )
        return ingredients
    
    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'обязательное поле.'
            ) 
        сhecked_tags = []
        for tag_id in tags:
            if tag_id in сhecked_tags:
                raise serializers.ValidationError(
                'теги не должны повторяться!')
            сhecked_tags.append(tag_id)
    
        return tags

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'обязательное поле.'
            )
        return value
    
    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError('значение должно быть больше единицы!')
        return value
    
    
    def to_representation(self, instance):
        return RecipeGet(instance, context=self.context).data


class IngredientsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)
     

class SubscribeSerializer(serializers.ModelSerializer):
    
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
        return GetSubscribeSerializer(instance.author, context=self.context).data


class GetSubscribeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 
                 'is_subscribed', 'avatar', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes_limit = self.context.get('request').query_params.get('recipes_limit')
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
        return ShortRecipeSerializer(instance.recipe, context=self.context).data

class ShoppingCartSerializer(serializers.ModelSerializer):
     
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
        return ShortRecipeSerializer(instance.recipe, context=self.context).data