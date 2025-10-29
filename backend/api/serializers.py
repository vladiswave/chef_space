from django.db import transaction
from djoser.serializers import UserSerializer as BaseUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .constants import DEFAULT_COUNTER_NUMBER
from recipes.constants import MAX_AMOUNT_VALUE, MIN_AMOUNT_VALUE
from recipes.models import (
    Ingredient, IngredientInRecipe, Recipe, Tag,
    ShoppingCart, Favorite
)
from users.models import Subscriptions, User


class SetAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления аватара пользователя."""

    avatar = Base64ImageField(
        max_length=None,
        use_url=True,
        required=True,
        allow_null=False,
    )

    class Meta:
        model = User
        fields = (
            'avatar',
        )


class UserSerializer(BaseUserSerializer, SetAvatarSerializer):
    """Сериализатор для запросов к данным пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = BaseUserSerializer.Meta.fields + ('is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated and (
                request.user.user_subscriptions.filter(
                    author=obj.id
                ).exists()
            )
        )


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Укороченный сериализатор для рецептов"""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )


class UserSubscriptionsSerializer(UserSerializer):
    """Расширенный cериализатор пользователя с рецептами"""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        read_only=True,
        default=DEFAULT_COUNTER_NUMBER
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes_count', 'recipes')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        queryset = obj.recipes.all()
        if limit:
            try:
                limit_int = int(limit)
                if limit_int > 0:
                    queryset = queryset[:limit_int]
            except (ValueError, TypeError):
                pass
        return RecipeMinifiedSerializer(
            queryset,
            many=True,
            context=self.context
        ).data


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Subscriptions
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise ValidationError('Нельзя подписаться на самого себя.')
        if Subscriptions.objects.filter(user=user, author=author).exists():
            raise ValidationError('Подписка уже существует.')
        return data

    def to_representation(self, instance):
        return UserSubscriptionsSerializer(
            instance.author,
            context=self.context
        ).data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')
        read_only_fields = ('__all__',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингрединтов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для связи рецепта и ингредиента."""

    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientAddToRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления ингридиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT_VALUE,
        max_value=MAX_AMOUNT_VALUE,
        error_messages={
            'min_value': f'Значение не должно быть больше {MIN_AMOUNT_VALUE}.',
            'max_value': f'Значение не должно быть больше {MAX_AMOUNT_VALUE}.'
        }
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount',
        )


class RecipesReadSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов для GET."""

    tags = TagSerializer(many=True, read_only=True,)
    author = UserSerializer(many=False, read_only=True,)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='ingredient_in',
        read_only=True
    )
    is_favorited = serializers.BooleanField(
        read_only=True,
        default=False
    )
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True,
        default=False
    )
    image = Base64ImageField(max_length=None, use_url=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )


class RecipesWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для произведений для POST и PATCH."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True,
        allow_null=False,
    )
    ingredients = IngredientAddToRecipeSerializer(
        many=True,
        required=True,
        allow_empty=False
    )
    author = UserSerializer(read_only=True,)
    image = Base64ImageField(max_length=None, use_url=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_AMOUNT_VALUE,
        max_value=MAX_AMOUNT_VALUE,
        error_messages={
            'min_value': f'Время не должно быть меньше {MIN_AMOUNT_VALUE}.',
            'max_value': f'Время не должно быть больше {MAX_AMOUNT_VALUE}.'
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'image',
            'text',
            'cooking_time',
            'tags',
            'ingredients',
        )

    def validate_tags(self, tags):
        if not tags:
            raise ValidationError('Необходимо указать хотя бы один тег.')
        if len(tags) != len(set(tags)):
            raise ValidationError('Указаны несуществующие тэги.')
        return tags

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise ValidationError(
                'Необходимо указать хотя бы один ингредиент.'
            )
        ingredient_ids = [item['id'] for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError('Ингредиенты не должны повторяться.')
        return ingredients

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                'Поле изображения не может быть пустым.'
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=author,
            **validated_data,
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags:
            instance.tags.clear()
            instance.tags.set(tags)
        if ingredients:
            instance.ingredient_in.all().delete()
            self.create_ingredients(instance, ingredients)
        instance = super().update(instance, validated_data)
        return instance

    @staticmethod
    def create_ingredients(recipe, ingredients):
        IngredientInRecipe.objects.bulk_create(
            [IngredientInRecipe(
                recipe=recipe,
                ingredients=ingredient_data['id'],
                amount=ingredient_data['amount']
            ) for ingredient_data in ingredients]
        )

    def to_representation(self, instance):
        return RecipesReadSerializer(instance, context=self.context).data


class BaseFavoriteShoppingSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для действий с рецептами."""

    class Meta:
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data['user']
        recipe = data['recipe']
        model = self.Meta.model
        if model.objects.filter(user=user, recipe=recipe).exists():
            model_name = model._meta.verbose_name.lower()
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {model_name}.'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context=self.context
        ).data


class FavoriteSerializer(BaseFavoriteShoppingSerializer):
    """Сериализатор для добавления в избранное."""

    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = Favorite


class ShoppingCartSerializer(BaseFavoriteShoppingSerializer):
    """Сериализатор для добавления в корзину."""

    class Meta(BaseFavoriteShoppingSerializer.Meta):
        model = ShoppingCart
