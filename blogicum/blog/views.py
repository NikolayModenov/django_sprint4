from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .form import CommentForm, PostForm
from .models import Category, Comment, Post

DISPLAYING_POSTS_ON_PAGE = 10


def get_filtered_posts(unfiltered_posts, is_author_profile_detail_view=False):
    """Filter the received posts from the database."""
    if is_author_profile_detail_view:
        return (
            unfiltered_posts
            .annotate(comments_count=Count('comments'))
            .order_by('-pub_date')
        )
    return (
        unfiltered_posts
        .filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
        .annotate(comments_count=Count('comments'))
        .order_by('-pub_date')
    )


class PostMixin:
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    fields = 'title', 'text', 'pub_date', 'location', 'category', 'image'

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


class UserIsAuthorMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.request.user != self.get_object().author:
            return redirect(
                'blog:post_detail',
                self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class RedirectToPostMixin:
    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            args=[self.kwargs['post_id']]
        )


class CommentChangeMixin(UserIsAuthorMixin, RedirectToPostMixin):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'


class IndexListView(ListView):
    """Display the main page."""

    model = Post
    queryset = (
        get_filtered_posts(Post.objects)
    )
    template_name = 'blog/index.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE


class PostDetailView(PostMixin, DetailView):
    """Display the requested post."""

    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        if not get_filtered_posts(Post.objects).filter(
            id=self.kwargs.get(self.pk_url_kwarg)
        ):
            get_object_or_404(
                Post.objects,
                author=self.request.user,
                id=self.kwargs.get(self.pk_url_kwarg)
            )
        return super().get_object(queryset)

    def get_context_data(self, **kwargs):
        return dict(
            comments=self.get_object().comments.all(),
            form=CommentForm(),
            **super().get_context_data(**kwargs)
        )


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """Create a new post, the author of which is an authorized user."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(UserIsAuthorMixin, PostMixin, UpdateView):
    """Edit the requested post."""

    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class PostDeleteView(UserIsAuthorMixin, PostMixin, DeleteView):
    """Delete the requested post."""

    form_class = PostForm

    def get_context_data(self, **kwargs):
        return dict(
            form=PostForm(instance=self.get_object()),
            **super().get_context_data(**kwargs)
        )


class CategoryDetailView(ListView):
    """Render a category view with set of posts."""

    model = Category
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE

    def get_context_data(self, **kwargs):
        category = get_object_or_404(
            Category, is_published=True,
            slug=self.kwargs.get(self.slug_url_kwarg)
        )
        self.object_list = get_filtered_posts(category.posts.all())
        return dict(category=category, **super().get_context_data(**kwargs))


class ProfileDetailView(ListView):
    """Render author's profile view with an array of posts by that author."""

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'profilename'
    template_name = 'blog/profile.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE

    def get_context_data(self, **kwargs):
        is_author = False
        author = get_object_or_404(
            User,
            username=self.kwargs.get(self.slug_url_kwarg)
        )
        if self.request.user == author:
            is_author = True
        self.object_list = get_filtered_posts(
            author.posts.all(),
            is_author
        )
        return dict(profile=author, **super().get_context_data(**kwargs))


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit the author's profile."""

    model = User
    fields = 'username', 'first_name', 'last_name', 'email'
    slug_field = 'username'
    slug_url_kwarg = 'profilename'
    template_name = 'blog/user.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.username != self.kwargs.get(self.slug_url_kwarg):
            return redirect(
                'blog:profile',
                self.kwargs.get(self.slug_url_kwarg)
            )
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )


class CommentCreateView(LoginRequiredMixin, RedirectToPostMixin, CreateView):
    """Add a comment to the specified post."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            id=self.kwargs.get('post_id')
        )
        return super().form_valid(form)


class CommentUpdateView(CommentChangeMixin, UpdateView):
    """Make changes to the selected comment."""

    form_class = CommentForm


class CommentDeleteView(CommentChangeMixin, DeleteView):
    """Delete the selected comment."""
