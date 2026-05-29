from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'get_favorite_count')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInline,)
    list_select_related = ('author',)

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(
            favorite_count=Count('favor_recipe', distinct=True)
        )

    @admin.display(description='В избранном')
    def get_favorite_count(self, obj: Recipe) -> int:
        return obj.favorite_count  # type: ignore[attr-defined]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')
    list_select_related = ('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_select_related = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_select_related = ('user', 'recipe')
