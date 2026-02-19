import json

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View, generic

from accounts.models import CustomUser

from .forms import InterestCategoryAddForm, LearningGoalSetForm, NativeLanguageSetForm
from .models import (
    DraftLearningGoal,
    LearningGoal,
    LearningMainTopic,
    LearningSubTopic,
    UserInterestCategory,
)


# Create your views here.
class IndexView(generic.TemplateView):
    template_name = 'task_management/index.html'

 
class NativeLanguageSetView(LoginRequiredMixin, generic.UpdateView):
    model = CustomUser
    form_class = NativeLanguageSetForm
    template_name = "task_management/set_native_language.html"
    success_url = reverse_lazy("task_management:interest_category_list")

    def get_object(self):
        return self.request.user
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.user_language is not None:
            return redirect("task_management:interest_category_list")
        return super().dispatch(request, *args, **kwargs)


# === Interest Category Views ===

# View to list user's interest categories
class InterestCategoryListView(LoginRequiredMixin, generic.ListView):
    template_name = 'task_management/interest_category/list.html'
    context_object_name = 'interest_categories'

    def get_queryset(self):
        return self.request.user.user_interest_categories.select_related('category')


# View to create a new interest category for the user
class InterestCategoryCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = 'task_management/interest_category/create.html'
    form_class = InterestCategoryAddForm
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


# === Learning Goal Views ===

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
        context['user_interest'] = user_interest
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


# View to set a new learning goal
class LearningGoalSetView(LoginRequiredMixin, generic.CreateView):
    template_name = 'task_management/learning_goal/set.html'
    form_class = LearningGoalSetForm

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


# View to preview generated learning topic outline
class LearningTopicPreviewView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'task_management/learning_goal/preview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        draft_id = self.kwargs['draft_id']
        draft = get_object_or_404(
            DraftLearningGoal,
            user=self.request.user,
            id=draft_id,
        )
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            category=draft.category,
        )

        if isinstance(draft.raw_generated_data, str):
            try:
                generated_topics = json.loads(draft.raw_generated_data)
            except json.JSONDecodeError:
                generated_topics = {}
        elif isinstance(draft.raw_generated_data, dict):
            generated_topics = draft.raw_generated_data
        else:
            generated_topics = {}

        context.update({
            'draft': draft,
            'user_interest': user_interest,
            'generated_topics': generated_topics,
        })

        return context


# View to finalize and save the learning goal
class LearningGoalFinalizeView(LoginRequiredMixin, View):
    def post(self, request, draft_id):
        draft = get_object_or_404(
            DraftLearningGoal,
            user=request.user,
            id=draft_id,
        )

        generated = draft.raw_generated_data
        
        selected_main_topics = request.POST.getlist('main_topics')
        selected_sub_topics = {
            key: request.POST.getlist(key)
            for key in request.POST
            if key.endswith('_sub_topics')
        }

        learning_goal = LearningGoal.objects.create(
            user=request.user,
            category=draft.category,
            draft=draft,
            title=draft.title,
            current_level=draft.current_level,
            target_level=draft.target_level,
            description=draft.description,
        )

        for main in generated["main_topics"]:
            title = main["title"]
            if title not in selected_main_topics:
                continue

            main_topic = LearningMainTopic.objects.create(
                user=request.user,
                learning_goal=learning_goal,
                title=title,
            )

            sub_topic_key = f"{title}_sub_topics"
            chosen_sub_topics = selected_sub_topics.get(sub_topic_key, [])

            for sub in main["sub_topics"]:
                sub_title = sub["title"]
                if sub_title not in chosen_sub_topics:
                    continue

                LearningSubTopic.objects.create(
                    user=request.user,
                    learning_goal=learning_goal,
                    main_topic=main_topic,
                    title=sub_title,
                )

        draft.is_finalized = True
        draft.save()

        messages.success(request, 'Learning goal finalized successfully.')
        return redirect('task_management:learning_goal_detail', goal_id=learning_goal.id)
    

# View to display details of a learning goal
class LearningGoalDetailView(LoginRequiredMixin, generic.DetailView):
    model = LearningGoal
    template_name = 'task_management/learning_goal/detail.html'
    context_object_name = 'learning_goal'
    pk_url_kwarg = 'goal_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        learning_goal = context['learning_goal']
        context['main_topics'] = learning_goal.main_topics.prefetch_related('sub_topics')
        return context
    
    def get_queryset(self):
        return LearningGoal.objects.filter(user=self.request.user, id=self.kwargs['goal_id'])


# View to delete a learning goal
class LearningGoalDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = LearningGoal
    template_name = 'task_management/learning_goal/confirm_delete.html'
    pk_url_kwarg = 'goal_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            category=self.get_object().category,
        )
        context['user_interest'] = user_interest
        return context
    
    def get_queryset(self):
        return LearningGoal.objects.filter(user=self.request.user, id=self.kwargs['goal_id'])

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Learning goal deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        learning_goal = self.get_object()
        interest_category = learning_goal.category
        user_interest = get_object_or_404(
            UserInterestCategory,
            user=self.request.user,
            category=interest_category,
        )
        return reverse_lazy('task_management:learning_goal_list', kwargs={'interest_id': user_interest.id})
