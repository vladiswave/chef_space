from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import (
    MAX_AMOUNT_VALUE,
    MAX_PREVIEW_LENGTH,
    MAX_MEASUREMENT_LENGTH,
    MAX_NAME_AND_SLUG_LENGTH_TAGS,
    MAX_NAME_LENGTH_INGREDIENT,
    MAX_NAME_LENGTH_RECIPES,
    MIN_AMOUNT_VALUE,
    SHORT_HASH_LENGTH
)
from .services import generate_short_hash
from users.models import User


class Tag(models.Model):
    """Модель тегов."""

    name = models.CharField(
        max_length=MAX_NAME_AND_SLUG_LENGTH_TAGS,
        unique=True,
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_NAME_AND_SLUG_LENGTH_TAGS,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:MAX_PREVIEW_LENGTH]


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH_INGREDIENT,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_MEASUREMENT_LENGTH,
        verbose_name='Единицы измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            ),
        )

    def __str__(self):
        return self.name[:MAX_PREVIEW_LENGTH]


class Recipe(models.Model):
    """Модель рецептов."""

    tags = models.ManyToManyField(
        Tag,
        verbose_name='Список тегов',
        related_name='recipes',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Список ингредиентов',
        related_name='recipes',
    )
    name = models.CharField(
        max_length=MAX_NAME_LENGTH_RECIPES,
        verbose_name='Название',
    )
    image = models.ImageField(
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=(
            MinValueValidator(
                MIN_AMOUNT_VALUE,
                message=f'Значение должно быть не меньше {MIN_AMOUNT_VALUE}.',
            ),
            MaxValueValidator(
                MAX_AMOUNT_VALUE,
                message=f'Значение должно быть не больше {MAX_AMOUNT_VALUE}.',
            )
        )
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True,
        editable=False,
    )
    short_hash = models.CharField(
        max_length=SHORT_HASH_LENGTH,
        unique=True,
        editable=False,
        verbose_name='Короткий хеш для ссылки',
        db_index=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = (
            models.UniqueConstraint(
                fields=('name', 'author'),
                name='unique_name_author'
            ),
        )

    def __str__(self):
        return f'{self.name[:MAX_PREVIEW_LENGTH]} от {self.author}'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.short_hash = generate_short_hash(self.__class__)
        super().save(*args, **kwargs)


class IngredientInRecipe(models.Model):
    """Модель для связи рецепта и ингредиента с его количеством."""

    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='ingredient_in',
    )
    ingredients = models.ForeignKey(
        Ingredient,
        verbose_name='Список ингредиентов',
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=(
            MinValueValidator(
                MIN_AMOUNT_VALUE,
                message=f'Количество не может быть меньше {MIN_AMOUNT_VALUE}.',
            ),
            MaxValueValidator(
                MAX_AMOUNT_VALUE,
                message=f'Количество не может быть больше {MAX_AMOUNT_VALUE}.',
            )
        )
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Список ингредиентов'
        verbose_name_plural = 'Список ингредиентов'
        constraints = (
            models.UniqueConstraint(
                fields=('ingredients', 'recipe'),
                name='unique_recipe_ingredients'
            ),
        )

    def __str__(self):
        return f'{self.recipe} has {self.amount} of {self.ingredients}'


class UserRecipeBaseModel(models.Model):
    """Абстрактная модель для избранных и покупок пользователя."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )

    class Meta:
        abstract = True
        ordering = ('user',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_name_recipe_%(class)s'
            ),
        )

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в {self._meta.verbose_name}'


class Favorite(UserRecipeBaseModel):
    """Модель для связи пользователя и его избранных."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class ShoppingCart(UserRecipeBaseModel):
    """Модель для связи пользователя и его покупок."""

    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_carts'
