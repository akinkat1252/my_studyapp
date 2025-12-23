from django.db.models import Max
from .models import LectureSession


def create_new_lecture_session(user, sub_topic):
    last_number = (
        LectureSession.objects
        .filter(user=user, sub_topic=sub_topic)
        .aggregate(max=Max("lecture_number"))["max"]
        or 0
    )

    return LectureSession.objects.create(
        user=user,
        sub_topic=sub_topic,
        lecture_number=last_number + 1,
    )
