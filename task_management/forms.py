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

