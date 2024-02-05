from django import forms

from blog.models import Comment, Post


class CommentForm(forms.ModelForm):
    """Create a comment form."""

    class Meta:
        model = Comment
        exclude = ('author', 'post')


class PostForm(forms.ModelForm):
    """Create a form for filling out posts."""

    class Meta:
        model = Post
        exclude = ('author',)
