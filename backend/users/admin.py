from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import Subscriptions, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для пользователей."""

    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'avatar',
        'get_image_avatar',
        'get_recipe_count',
        'get_subscriber_count',
    )
    search_fields = (
        'email',
        'username',
        'last_name',
    )
    list_filter = (
        'email',
        'username',
    )
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'avatar'
            )
        }),
        ('Права доступа', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields':
            (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'avatar'
            ),
        }),
    )
    empty_value_display = 'Не задано'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            recipe_count=Count('recipes', distinct=True),
            subscriber_count=Count('subscriptions_to_author', distinct=True)
        )

    @admin.display(description='Рецепты')
    def get_recipe_count(self, obj):
        return obj.recipe_count

    @admin.display(description='Подписчики')
    def get_subscriber_count(self, obj):
        return obj.subscriber_count

    @admin.display(description='Изображение аватара')
    def get_image_avatar(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.avatar.url}" width="80" height="60">'
            )
        return self.empty_value_display


@admin.register(Subscriptions)
class SubscriptionsAdmin(admin.ModelAdmin):
    """Админка для подписок пользователей."""
    list_display = (
        'user',
        'author',
        'get_user_email',
        'get_author_email'
    )
    list_filter = (
        'user__username',
        'author__username',
    )
    search_fields = (
        'user__username',
        'user__email',
        'author__username',
        'author__email',
    )

    @admin.display(description='Email пользователя')
    def get_user_email(self, obj):
        return obj.user.email

    @admin.display(description='Email автора')
    def get_author_email(self, obj):
        return obj.author.email
