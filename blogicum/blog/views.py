from blog.form import CommentForm, PostForm
from blog.models import Category, Comment, Post
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from django.views.generic.list import MultipleObjectMixin


def get_filtered_posts(unfiltered_posts):
    """Filter the received messages from the database."""
    return unfiltered_posts.select_related(
        'author', 'location', 'category'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(comments_count=Count('comments__id')).order_by('-pub_date')


class PostMixin:
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    fields = 'title', 'text', 'pub_date', 'location', 'category', 'image'

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            kwargs={'profilename': self.request.user.username}
        )


class UserIsAuthorMixin:
    def dispatch(self, request, *args, **kwargs):
        current_post = get_object_or_404(
            self.model,
            id=self.kwargs[self.pk_url_kwarg]
        )
        if self.request.user != current_post.author:
            return redirect(
                'blog:post_detail',
                self.kwargs[self.pk_url_kwarg]
            )
        return super().dispatch(request, *args, **kwargs)


class CommentReverseMixin:
    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            args=[self.kwargs[self.pk_url_kwarg]]
        )


class PaginateMixin:
    paginate_by = 10


class CommentChangeMixin(UserIsAuthorMixin, CommentReverseMixin):
    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'


class IndexListView(PaginateMixin, ListView):
    """Open the main page."""

    model = Post
    queryset = (
        get_filtered_posts(Post.objects)
    )
    template_name = 'blog/index.html'


class PostDetailView(PostMixin, DetailView):
    """Open the page with the requested post."""

    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        current_post = get_object_or_404(
            Post,
            id=self.kwargs.get(self.pk_url_kwarg, id is not None)
        )
        if not get_filtered_posts(Post.objects).filter(
            id=self.kwargs.get(self.pk_url_kwarg)
        ):
            get_object_or_404(
                Post,
                author_id=self.request.user.id,
                id=self.kwargs.get(self.pk_url_kwarg, id is not None)
            )
        return {
            **super().get_context_data(**kwargs),
            'comments': current_post.comments.all(),
            'form': CommentForm()
        }


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
        return {
            **super().get_context_data(**kwargs),
            'form': PostForm(
                instance=Post.objects.get(pk=self.kwargs['post_id'])
            )
        }


class CategoryDetailView(PaginateMixin, MultipleObjectMixin, DetailView):
    """Open the posts page of the specified category."""

    model = Category
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'

    def get_context_data(self, **kwargs):
        category = get_object_or_404(
            Category,
            slug=self.kwargs.get(self.slug_url_kwarg),
            is_published=True
        )
        return {
            **super().get_context_data(
                object_list=get_filtered_posts(category.posts.all()),
                **kwargs
            ),
            'category': category
        }


class ProfileDetailView(PaginateMixin, MultipleObjectMixin, DetailView):
    """Open the user's profile page."""

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'profilename'
    template_name = 'blog/profile.html'

    def get_context_data(self, **kwargs):
        user_object = get_object_or_404(
            User.objects,
            username=self.kwargs.get(self.slug_url_kwarg)
        )
        post_object = user_object.posts.all()
        if self.request.user.username != self.kwargs.get('profilename'):
            post_object = get_filtered_posts(post_object)
        return {
            **super().get_context_data(
                object_list=post_object,
                **kwargs
            ),
            'profile': user_object
        }


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


class CommentCreateView(LoginRequiredMixin, CommentReverseMixin, CreateView):
    """Send a comment on the specified post."""

    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        post = get_object_or_404(
            Post,
            id=self.kwargs.get('post_id')
        )
        form.instance.author = self.request.user
        form.instance.post_id = post.id
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, CommentChangeMixin, UpdateView):
    """Open the comment editing page."""

    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentChangeMixin, DeleteView):
    """Open the comment deletion page."""
