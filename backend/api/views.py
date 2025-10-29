from io import BytesIO

from django.db.models import Count, Exists, F, OuterRef, Prefetch, Sum
from django.http import FileResponse
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views as djoser_views
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .pagination import RecipeLimitPagination
from .permissions import AdminOrModeratorAuthorOrReadOnly
from .serializers import (
    FavoriteSerializer, IngredientSerializer, RecipeMinifiedSerializer,
    RecipesReadSerializer, RecipesWriteSerializer, SetAvatarSerializer,
    ShoppingCartSerializer, SubscriptionSerializer, TagSerializer,
    UserSerializer, UserSubscriptionsSerializer
)
from .services import generate_shopping_list_text
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Tag
)
from users.models import Subscriptions, User


class UserViewSet(djoser_views.UserViewSet):
    """Вьюсет данных пользователей."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = RecipeLimitPagination

    @action(
        ('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request, *args, **kwargs):
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        serializer_class=SubscriptionSerializer
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        data = {'user': user.id, 'author': author.id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        deleted_count, _ = Subscriptions.objects.filter(
            user=user,
            author=author
        ).delete()
        if not deleted_count:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscriptions_to_author__user=request.user
        ).prefetch_related(
            Prefetch(
                'recipes',
                queryset=Recipe.objects.order_by('-pub_date'),
            )
        ).annotate(recipes_count=Count('recipes'))
        page = self.paginate_queryset(authors)
        serializer = UserSubscriptionsSerializer(
            page,
            many=True,
            context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=('put',),
        permission_classes=(
            AdminOrModeratorAuthorOrReadOnly,
        ),
        serializer_class=SetAvatarSerializer,
        url_path='me/avatar',
    )
    def avatar(self, request):
        user = request.user
        data = request.data
        if not data:
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(
            user,
            data=data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminOrModeratorAuthorOrReadOnly,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminOrModeratorAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет рецептов."""

    permission_classes = (
        AdminOrModeratorAuthorOrReadOnly,
    )
    http_method_names = ('get', 'post', 'patch', 'delete')
    pagination_class = RecipeLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.prefetch_related(
            Prefetch('tags', queryset=Tag.objects.all()),
            Prefetch(
                'ingredient_in',
                queryset=IngredientInRecipe.objects.select_related(
                    'ingredients'
                )
            )
        ).select_related('author')
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe_id=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe_id=OuterRef('pk')
                    )
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return RecipesReadSerializer
        return RecipesWriteSerializer

    def _add_action(self, request, pk, serializer_class):
        recipe = self.get_object()
        user = request.user
        data = {'user': user.id, 'recipe': recipe.id}
        serializer = serializer_class(
            data=data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output_serializer = RecipeMinifiedSerializer(
            recipe,
            context=self.get_serializer_context()
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def _remove_action(self, request, pk, model):
        recipe = self.get_object()
        user = request.user
        deleted_count, _ = model.objects.filter(
            user=user,
            recipe=recipe
        ).delete()
        if not deleted_count:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        return self._add_action(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        return self._remove_action(request, pk, ShoppingCart)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        return self._add_action(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._remove_action(request, pk, Favorite)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            name=F('ingredients__name'),
            unit=F('ingredients__measurement_unit')
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('name')
        text = generate_shopping_list_text(ingredients)
        buffer = BytesIO(text.encode('utf-8'))
        return FileResponse(
            buffer,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain; charset=utf-8'
        )

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_short_link(self, request, pk=None):
        recipe = self.get_object()
        short_url = request.build_absolute_uri(
            reverse('short-link-redirect', args=[recipe.short_hash])
        )
        return Response({'short-link': short_url})
