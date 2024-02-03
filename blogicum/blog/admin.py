from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Create a post editing tab."""

    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published'
    )
    list_editable = ('is_published', 'category')
    search_fields = ('title',)
    list_filter = ('author', 'category')
    empty_value_display = 'Не задано'


class Postline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Create a category editing tab."""

    inlines = (Postline,)
    list_display = ('title', 'is_published')
    list_editable = ('is_published',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Create a location editing tab."""

    list_display = ('name', 'is_published')
    list_editable = ('is_published',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Create a comment editing tab."""

    list_display = ('__str__', 'text', 'author', 'post')
