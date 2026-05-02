from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import PostCategoryForm, PostForm
from .models import Post, PostAttachment, PostCategory

# #########################  PostCategory ###########################


class PostCategoryListView(LoginRequiredMixin, ListView):
    model = PostCategory
    template_name = 'board/postcategory_list.html'


class PostCategoryCreateView(LoginRequiredMixin, CreateView):
    model = PostCategory
    form_class = PostCategoryForm
    template_name = 'board/postcategory_form.html'
    success_url = reverse_lazy('board:category_list')


class PostCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = PostCategory
    form_class = PostCategoryForm
    template_name = 'board/postcategory_form.html'
    success_url = reverse_lazy('board:category_list')


class PostCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = PostCategory
    template_name = 'board/postcategory_confirm_delete.html'
    success_url = reverse_lazy('board:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        related_posts = Post.objects.filter(category=self.object)
        context['related_posts'] = related_posts
        context['has_dependencies'] = related_posts.exists()
        if 'delete_error' in self.request.session:
            context['error'] = self.request.session.pop('delete_error')
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if Post.objects.filter(category=self.object).exists():
            request.session['delete_error'] = _("Cannot delete category because it is in use. Remove all documents that use it first.")
            return redirect('board:category_delete', pk=self.object.pk)
        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            request.session['delete_error'] = str(e)
            return redirect('board:category_delete', pk=self.object.pk)


def board(request: HttpRequest) -> HttpResponse:
    sort = request.GET.get('sort', 'date')
    order = request.GET.get('order', 'desc')
    category_id = request.GET.get('category')
    reverse_order = (order == 'desc')

    if request.user.is_authenticated:
        posts_all = Post.objects.filter(is_archived=False).select_related('category', 'author')
    else:
        posts_all = Post.objects.filter(is_public=True, is_archived=False).select_related('category', 'author')

    # Filter by category if specified
    if category_id and category_id != 'all':
        try:
            category_id = int(category_id)
            posts_all = posts_all.filter(category_id=category_id)
            active_category = category_id
        except (ValueError, TypeError):
            active_category = None
    else:
        active_category = None

    # Group by category
    categories = list(PostCategory.objects.all())
    posts_by_cat = {}
    uncategorized = []
    for post in posts_all:
        if post.category_id:
            posts_by_cat.setdefault(post.category_id, []).append(post)
        else:
            uncategorized.append(post)

    category_groups = []
    for cat in categories:
        cat_posts = posts_by_cat.get(cat.pk, [])
        if cat_posts:
            # Sort posts within category
            sorted_posts = sorted(cat_posts, key=lambda p: p.updated, reverse=reverse_order)
            category_groups.append({
                'category': cat,
                'posts': sorted_posts
            })
    if uncategorized:
        # Sort uncategorized posts
        sorted_uncategorized = sorted(uncategorized, key=lambda p: p.updated, reverse=reverse_order)
        category_groups.append({
            'category': None,
            'posts': sorted_uncategorized
        })

    return render(
        request,
        'board/board.html',
        {
            'category_groups': category_groups,
            'categories': categories,
            'current_sort': sort,
            'current_order': order,
            'active_category': active_category,
        },
    )


def archive(request: HttpRequest) -> HttpResponse:
    posts_archived: QuerySet[Post] = Post.objects.filter(is_archived=True).order_by('-updated')
    return render(request, 'board/archive.html', {
        'posts': posts_archived
    })


@login_required
def create_post(request: HttpRequest):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            # Handle attachments
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                PostAttachment.objects.create(
                    post=post,
                    file=attachment,
                    filename=attachment.name
                )

            return redirect('board:view_post', post.pk)
    else:
        form = PostForm()
    return render(request, 'board/create_post.html', {
        'form': form
    })


@login_required
def edit_post(request: HttpRequest, pk: int):
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            # Handle attachments
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                PostAttachment.objects.create(
                    post=post,
                    file=attachment,
                    filename=attachment.name
                )

            return redirect('board:view_post', pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'board/edit_post.html', {
        'form': form,
        'post': post
    })


def view_post(request: HttpRequest, pk: int):
    post = get_object_or_404(Post, pk=pk)  # Only published documents can be viewed
    return render(request, 'board/post_detail.html', {
        'post': post
    })


@login_required
def delete_post(request: HttpRequest, pk: int):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        post.delete()
        return redirect('board:start')
    return render(request, 'board/post_confirm_delete.html', {
        'post': post
    })


@login_required
def delete_attachment(request: HttpRequest, pk: int, attachment_id: int):
    post = get_object_or_404(Post, pk=pk)
    attachment = get_object_or_404(PostAttachment, pk=attachment_id, post=post)
    if request.method == 'POST':
        attachment.delete()
        return redirect('board:edit_post', pk=pk)
    return render(request, 'board/attachment_confirm_delete.html', {
        'attachment': attachment,
        'post': post
    })
