
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views import View, generic
from django.urls import reverse_lazy, redirect
from django.contrib import messages

from .forms import AddInterestCategoryForm, LearningGoalCreateForm
from .models import UserInterestCategory, LearningGoal


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


# View to delete an interest category for the user
class InterestCategoryDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'task_management/interest_category/confirm_delete.html'
    success_url = reverse_lazy('task_management:interest_category_list')

    def get_queryset(self):
        return self.request.user.user_interest_categories.select_related('category')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Interest category deleted successfully.')
        return super().delete(request, *args, **kwargs)


# View to list user's learning goals
class LearningGoalListView(LoginRequiredMixin, generic.ListView):
    model = LearningGoal
    template_name = 'task_management/learning_goal/list.html'
    context_object_name = 'learning_goals'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interest_id = self.kwargs['interest_id']
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            id=interest_id,
        )
        context['interest_category'] = user_interest.category
        return context

    def get_queryset(self):
        interest_id = self.kwargs['interest_id']
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            id=interest_id,
        )
        return LearningGoal.objects.filter(
            user=self.request.user,
            category=user_interest.category
        ).select_related('category')


# View to create a new learning goal
class LearningGoalCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = 'task_management/learning_goal/create.html'
    form_class = LearningGoalCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        interest_id = self.kwargs['interest_id']
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            id=interest_id,
        )
        context['interest_category'] = user_interest.category
        return context
    
    def form_valid(self, form):
        draft = form.save(commit=False)
        draft.user = self.request.user
        interest_id = self.kwargs['interest_id']
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            id=interest_id,
        )
        draft.category = user_interest.category
        draft.save()
        return redirect('ai_support:learning_topic_generate', draft_id=draft.id)
