# flake8: noqa: D106
"""Сериализаторы Пользователя."""
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.core.exceptions import ValidationError

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
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)

class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

class RecipeGet(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = UsersSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
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
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = UsersSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time', 'author')

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('recipe_ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
    
        for ingredient_data in ingredients_data:
            ingredient = get_object_or_404(Ingredient, pk=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount'])
        return recipe
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients_data = validated_data.pop('recipe_ingredients', None)

        if tags is not None:
            instance.tags.set(tags)
        
        if ingredients_data is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()

            for ingredient_data in ingredients_data:
                ingredient = get_object_or_404(Ingredient, pk=ingredient_data['id'])
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient,
                    amount=ingredient_data['amount']
                ) 
        return instance
    
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
        recipes = obj.recipes.all()
        return ShortRecipeSerializer(recipes, context=self.context, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscribe.objects.filter(user=request.user, author=obj).exists()
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