from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from api.constants import (
    MAX_EMAIL_LENGTH,
    MAX_NAME_FIELD_LENGTH
)
from api.validators import validate_username_regex


class User(AbstractUser):
    """Модель пользователей."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
    )
    email = models.EmailField(
        unique=True,
        max_length=MAX_EMAIL_LENGTH,
        verbose_name='Адрес электронной почты',
        error_messages={
            'unique': 'Данный адрес уже используется',
        },
    )
    username = models.CharField(
        verbose_name='Имя пользователя',
        unique=True,
        max_length=MAX_NAME_FIELD_LENGTH,
        validators=(
            validate_username_regex,
        ),
        error_messages={
            'unique': 'Пользователь с таким именем уже существует',
        },
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=MAX_NAME_FIELD_LENGTH,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=MAX_NAME_FIELD_LENGTH,
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        blank=True,
        null=True,
        default=None
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscriptions(models.Model):
    """Модель для связи пользователя и его подписок на авторов рецептов."""

    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='subscriptions_to_author'
    )
    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='user_subscriptions'
    )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=('author', 'user'),
                name='unique_author_user'
            ),
        )

    def clean(self):
        if self.author == self.user:
            raise ValidationError('Нельзя подписаться на самого себя.')

    def __str__(self):
        return f'{self.user} subscribed to {self.author}'
