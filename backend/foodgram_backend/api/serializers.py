# flake8: noqa: D106
"""Сериализаторы Пользователя."""
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers

from users.models import CustomUser
from recipes.models import Ingredient, Tag, Recipe, RecipeIngredient


class UsersSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.BooleanField(default=False, read_only=True)

    class Meta():
        model = CustomUser
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'is_subscribed', 'avatar',
        )


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


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = UserSerializer(read_only=True)

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