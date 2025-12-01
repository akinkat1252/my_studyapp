
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View, generic
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import AddInterestCategoryForm


# Create your views here.
class IndexView(generic.TemplateView):
    template_name = 'task_management/index.html'
    

# View to list user's interest categories
class InterestCategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = 'task_management/interest_category/list.html'
    context_object_name = 'interest_categories'

    def get_queryset(self):
        return self.request.user.user_interest_categories.select_related('category')


# View to create a new interest category for the user
class InterestCategoryCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = 'task_management/interest_category/create.html'
    form_class = AddInterestCategoryForm
    success_url = reverse_lazy('task_management:interest_category_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class InterestCategoryDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'task_management/interest_category/confirm_delete.html'
    success_url = reverse_lazy('task_management:interest_category_list')

    def get_queryset(self):
        return self.request.user.user_interest_categories.select_related('category')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Interest category deleted successfully.')
        return super().delete(request, *args, **kwargs)
