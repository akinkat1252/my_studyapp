from django.db import models
from exam.exceptions import ExamTypeDomainError


class ExamTypeManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def get_by_code(self, code: str):
        try:
            return self.get(code=code)
        except self.model.DoesNotExist:
            raise ExamTypeDomainError("Exam type not found.")
