from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, Field
from .models import UserInterestCategory, DraftLearningGoal, LearningGoal


# Form for adding interest categories to a user.
class AddInterestCategoryForm(forms.ModelForm):
    class Meta:
        model = UserInterestCategory
        fields = ['category']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'category': 'Select Category',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Add Interest Category',
                Field('category', css_class='form-control')
            ),
            ButtonHolder(
                Submit('submit', 'Add Category', css_class='btn btn-primary mt-4 mb-5')
            )
        )


# Form for creating a new learning goal draft.
class LearningGoalCreateForm(forms.ModelForm):
    class Meta:
        model = DraftLearningGoal
        fields = ['title', 'current_level', 'target_level', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'current_level': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'target_level': forms.TextInput(attrs={'class': 'form-control', 'rows': 4}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'title': 'Learning Goal Title *',
            'current_level': 'Current Level (optional)',
            'target_level': 'Target Level (optional)',
            'description': 'Description (optional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                'Create Learning Goal',
                Field(
                    'title',
                    css_class='form-control',
                    placeholder='E.g., Learn Django Basics'
                ),
                Field(
                    'current_level',
                    css_class='form-control',
                    placeholder='E.g., Familiar with Python, but new to Django',
                ),
                Field(
                    'target_level',
                    css_class='form-control',
                    placeholder='E.g., Able to build and deploy Django applications',
                ),
                Field(
                    'description',
                    css_class='form-control',
                    placeholder='E.g., I want to learn Django to build web applications efficiently.',
                ),
            ),
            ButtonHolder(
                Submit('submit', 'Create Goal', css_class='btn btn-primary mt-4 mb-5')
            )
        )
