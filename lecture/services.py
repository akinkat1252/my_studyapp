from django.db import transaction
from django.db.models import Max
from .models import LectureSession, LectureProgress


def create_new_lecture_session(user, sub_topic):
    with transaction.atomic():
        last_number = (
            LectureSession.objects
            .filter(user=user, sub_topic=sub_topic)
            .aggregate(max=Max("lecture_number"))["max"]
            or 0
        )
        session = LectureSession.objects.create(
            user=user,
            sub_topic=sub_topic,
            lecture_number=last_number + 1,
        )

        progress_objs = [
            LectureProgress(
                session=session,
                topic=topic,
                order=topic.default_order,
            ) for topic in sub_topic.lecture_topics.all().order_by("default_order")
        ]
        LectureProgress.objects.bulk_create(progress_objs)

    return session
