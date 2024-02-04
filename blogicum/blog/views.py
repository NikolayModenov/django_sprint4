from blog.form import CommentForm, PostForm
from blog.models import Category, Comment, Post
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView,
    UpdateView
)
from django.views.generic.list import MultipleObjectMixin

DISPLAYING_POSTS_ON_PAGE = 10


def get_filtered_posts(unfiltered_posts):
    """Filter the received messages from the database."""
    return unfiltered_posts.select_related(
        'author', 'location', 'category'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(comments_count=Count('comments')).order_by('-pub_date')


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
    """Open the main page."""

    model = Post
    queryset = (
        get_filtered_posts(Post.objects)
    )
    template_name = 'blog/index.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE


class PostDetailView(PostMixin, DetailView):
    """Open the page with the requested post."""

    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        if not get_filtered_posts(Post.objects).filter(
            id=self.kwargs.get(self.pk_url_kwarg)
        ):
            self.get_object(
                Post.objects.filter(author_id=self.request.user.id)
            )
        return dict(
            **super().get_context_data(**kwargs),
            comments=self.get_object().comments.all(),
            form=CommentForm()
        )


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """Open the post creation page."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserIsAuthorMixin, PostMixin,
                     UpdateView):
    """Open the edit page with the requested post."""

    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class PostDeleteView(LoginRequiredMixin, UserIsAuthorMixin, PostMixin,
                     DeleteView):
    """Open the page for deleting the requested post."""

    form_class = PostForm

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=PostForm(instance=self.get_object())
        )


class CategoryDetailView(MultipleObjectMixin, DetailView):
    """Open the posts page of the specified category."""

    model = Category
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE

    def get_context_data(self, **kwargs):
        category = self.get_object(Category.objects.filter(is_published=True))
        return dict(
            **super().get_context_data(
                object_list=get_filtered_posts(category.posts.all()),
                **kwargs
            ),
            category=category
        )


class ProfileDetailView(MultipleObjectMixin, DetailView):
    """Open the user's profile page."""

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'profilename'
    template_name = 'blog/profile.html'
    paginate_by = DISPLAYING_POSTS_ON_PAGE

    def get_context_data(self, **kwargs):
        author = self.get_object()
        if self.request.user.username != self.kwargs.get('profilename'):
            post = get_filtered_posts(author.posts)
        else:
            post = author.posts.all()
        return dict(
            **super().get_context_data(
                object_list=post,
                **kwargs
            ),
            profile=author
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Open the user profile editing page."""

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
            kwargs={'profilename': self.request.user.username}
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


class CommentUpdateView(LoginRequiredMixin, CommentChangeMixin, UpdateView):
    """Make changes to the selected comment."""

    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentChangeMixin, DeleteView):
    """Delete the selected comment."""
