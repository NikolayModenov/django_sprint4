from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView
)
from django.views.generic.list import MultipleObjectMixin

from blog.form import CommentForm, PostForm
from blog.models import Category, Comment, Post


def get_filtered_posts(unfiltered_posts):
    """
    Filter the received posts from the database with filter attributes:
    date of publication <= current time;
    post is allowed to publish;
    category of posts is allowed to publish.
    """
    return unfiltered_posts.select_related(
        'author', 'location', 'category'
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    )


class PostMixin:
    model = Post
    pk_url_kwarg = "post_id"
    template_name = 'blog/create.html'
    fields = 'title', 'text', 'pub_date', 'location', 'category', 'image'

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class DispathPostMixin(PostMixin):
    def dispatch(self, request, *args, **kwargs):
        current_post = get_object_or_404(
            Post.objects.values('author_id'),
            id=self.kwargs.get('post_id')
        )
        if self.request.user.id != current_post['author_id']:
            return redirect('blog:post_detail', self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentReverseMixin:
    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            kwargs={"post_id": self.kwargs['post_id']}
        )


class CommentChangeMixin(CommentReverseMixin):
    model = Comment
    pk_url_kwarg = "comment_id"
    template_name = 'blog/comment.html'

    def dispatch(self, request, *args, **kwargs):
        current_comment = get_object_or_404(
            Comment.objects.values('author_id'),
            id=self.kwargs.get('comment_id')
        )
        if self.request.user.id != current_comment['author_id']:
            return redirect('blog:post_detail', self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class IndexListView(ListView):
    """Open the main page."""

    model = Post
    queryset = (
        get_filtered_posts(Post.objects)
        .annotate(comment_count=Count('comment__id'))
        .order_by('-pub_date')
    )
    paginate_by = 10
    template_name = 'blog/index.html'


class PostDetailView(PostMixin, DetailView):
    """Open the page with the requested post."""

    template_name = 'blog/detail.html'

    def clean_post_id(self):
        post_id = self.cleaned_data['post_id']
        if post_id is None:
            raise Http404
        return post_id

    def get_context_data(self, **kwargs):
        current_post = get_object_or_404(
            Post.objects.values(
                'is_published',
                'pub_date',
                'author_id',
                'category__is_published'
            ),
            id=self.kwargs.get('post_id')
        )
        comments_current_post = Comment.objects.filter(
            post_id=self.kwargs.get('post_id')
        )
        if (
            not current_post['is_published']
            or current_post['pub_date'] >= timezone.now()
            or not current_post['category__is_published']
        ):
            if current_post['author_id'] != self.request.user.id:
                raise Http404
        context = super().get_context_data(**kwargs)
        context['comments'] = comments_current_post
        context['form'] = CommentForm()
        return context


class PostCreateView(LoginRequiredMixin, PostMixin, CreateView):
    """Open the post creation page."""

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, DispathPostMixin, UpdateView):
    """Open the edit page with the requested post."""

    def get_success_url(self) -> str:
        return reverse(
            'blog:post_detail',
            kwargs={"post_id": self.kwargs['post_id']}
        )


class PostDeleteView(LoginRequiredMixin, DispathPostMixin, DeleteView):
    """Open the page for deleting the requested post."""

    form_class = PostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PostForm(
            instance=Post.objects.get(pk=self.kwargs['post_id'])
        )
        return context


class CategoryDetailView(MultipleObjectMixin, DetailView):
    """Open the posts page of the specified category."""

    model = Category
    slug_url_kwarg = 'category_slug'
    template_name = 'blog/category.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        category_availability = get_object_or_404(
            Category.objects.values('is_published'),
            slug=self.kwargs.get('category_slug')
        )
        if not category_availability['is_published']:
            raise Http404
        object_list = (
            get_filtered_posts(Post.objects)
            .filter(category__slug=self.kwargs.get('category_slug'))
            .annotate(comment_count=Count('comment__id'))
            .order_by('-pub_date')
        )
        context = super(CategoryDetailView, self).get_context_data(
            object_list=object_list, **kwargs
        )
        context['category'] = get_object_or_404(
            Category.objects.all(),
            slug=self.kwargs.get('category_slug')
        )
        return context


class ProfileDetailView(MultipleObjectMixin, DetailView):
    """Open the user's profile page."""

    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        object_list = (
            Post.objects.filter(author__username=self.kwargs.get('username'))
            .annotate(comment_count=Count('comment__id'))
            .order_by('-pub_date')
        )
        if self.request.user.username != self.kwargs.get('username'):
            object_list = get_filtered_posts(object_list)
        context = (
            super(ProfileDetailView, self)
            .get_context_data(object_list=object_list, **kwargs)
        )
        context['profile'] = get_object_or_404(
            User.objects.all(),
            username=self.kwargs.get('username')
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Open the user profile editing page."""

    model = User
    fields = 'username', 'first_name', 'last_name', 'email'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'blog/user.html'

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.username != self.kwargs.get('username'):
            return redirect('blog:profile', self.kwargs.get('username'))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentCreateView(LoginRequiredMixin, CommentReverseMixin, CreateView):
    """Send a comment on the specified post."""

    model = Comment
    form_class = CommentForm
    pk_url_kwarg = "post_id"
    template_name = 'blog/detail.html'

    def form_valid(self, form):
        post_id_form = get_object_or_404(
            Post.objects.values('id'),
            id=self.kwargs.get('post_id')
        )
        form.instance.author = self.request.user
        form.instance.post_id = post_id_form['id']
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, CommentChangeMixin, UpdateView):
    """Open the comment editing page."""

    form_class = CommentForm


class CommentDeleteView(LoginRequiredMixin, CommentChangeMixin, DeleteView):
    """Open the comment deletion page."""

    pass
