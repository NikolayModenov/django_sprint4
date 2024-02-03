from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import models

User = get_user_model()


class PublishedModel(models.Model):
    """
    An abstract model. Adds the is_published flag
    and automatically fills in the created_at field
    with the current line creation time.
    """

    is_published = models.BooleanField(
        default=True,
        verbose_name='Опубликовано',
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class Category(PublishedModel):
    """
    Create a category table with the title, description,
    and slug identifier fields.
    """

    title = models.CharField(max_length=256, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        unique=True,
        verbose_name='Идентификатор',
        max_length=50,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:50]


class Location(PublishedModel):
    """Create a location table with a place name field."""

    name = models.CharField(max_length=256, verbose_name='Название места')

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:50]


class Post(PublishedModel):
    """
    Create a table of posts with the fields title,
    date and time of publication, author of the publication.
    Link location and category to the tables.
    """

    title = models.CharField(max_length=256, verbose_name='Заголовок')
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Формат даты: День.Месяц.Год<br/>'
            'Пример: 20.10.2020<br/>'
            'Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
        ))
    image = models.ImageField(
        verbose_name='Фото',
        upload_to='post_images',
        blank=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        default_related_name = 'posts'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.title[:50]


class Comment(models.Model):
    """Create a comment table."""

    text = models.TextField(max_length=256, verbose_name='Текст комментария')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='add_comment'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Публикация',
        related_name='comments',
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return f'Комментарий №{self.pk} от {self.created_at}'
