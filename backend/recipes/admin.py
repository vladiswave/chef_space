from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (
    Ingredient, IngredientInRecipe, Favorite, Recipe, ShoppingCart, Tag
)


class IngredientInRecipeInline(admin.TabularInline):
    """Модель для вставки ингредиентов в рецепт."""

    model = IngredientInRecipe
    extra = 0
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тэгов."""

    list_display = (
        'name',
        'slug'
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранных."""

    list_display = ('user', 'recipe',)
    list_filter = ('user__username', 'recipe__name',)
    search_fields = ('user__username', 'recipe__name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = ('user', 'recipe',)
    list_filter = ('user__username', 'recipe__name',)
    search_fields = ('user__username', 'recipe__name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        'author',
        'name',
        'text',
        'cooking_time',
        'get_tags',
        'get_ingredients',
        'get_favorites',
        'get_image',
    )
    filter_horizontal = ('tags', )
    inlines = (IngredientInRecipeInline,)
    search_fields = ('name', 'author__username', 'tags__name',)
    list_filter = ('tags', 'author__username', 'cooking_time',)
    empty_value_display = 'Не задано'

    @admin.display(description='Тэг')
    def get_tags(self, obj):
        return ', '.join([tags.name for tags in obj.tags.all()])

    @admin.display(description='Избранное')
    def get_favorites(self, obj):
        return obj.favorites.count()

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join(
            [ingredients.name for ingredients in obj.ingredients.all()]
        )

    @admin.display(description='Изображение')
    def get_image(self, obj):
        return mark_safe(f'<img src="{obj.image.url}" width="80" height="60">')


admin.site.unregister(Group)
admin.site.empty_value_display = 'Не задано'
