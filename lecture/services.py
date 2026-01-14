from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone
from .models import LectureSession, LectureProgress, LectureLog
from ai_support.modules.lecture.generate_lecture import (
    generate_lecture,
    generate_lecture_summary,
    generate_lecture_answer,
    generate_lecture_report,
)


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


def get_current_lecture_progress(session):
    return (
        session.progress_records
        .filter(is_completed=False)
        .order_by("order")
        .first()
    )

# Advance the lecture to the next topic
@transaction.atomic
def advance_lecture(session) -> dict:
    current = get_current_lecture_progress(session)

    # mark current as completed
    if current and session.logs.filter(role='ai').exists():
        current.is_completed = True
        current.save()

    # get the next topic
    next_progress = get_current_lecture_progress(session)
    if not next_progress:
        return {"is_ended": True}
    
    # generate lecture content
    ai_response = generate_lecture(session=session, topic=next_progress.topic)

    # Log AI response
    usage = ai_response.usage_metadata or {}
    total_tokens = usage.get("total_tokens", 0)
    LectureLog.objects.create(
        session=session,
        role='ai',
        message=ai_response.content,
        token_count=total_tokens,
    )

    # generate summary and save to session
    summary_response = generate_lecture_summary(session=session)
    session.summary = summary_response.content
    session.save()

    return {
        "is_ended": False,
        "lecture_content": ai_response.content,
    }


@transaction.atomic
def handle_lecture_chat(session, user_input) -> str:
    # Generate AI response to user input
    ai_response = generate_lecture_answer(session=session, user_input=user_input)

    # Log user message
    LectureLog.objects.create(
        session=session,
        role='user',
        message=user_input,
    )

    # Log AI response
    usage = ai_response.usage_metadata or {}
    total_tokens = usage.get("total_tokens", 0)
    LectureLog.objects.create(
        session=session,
        role='ai',
        message=ai_response.content,
        token_count=total_tokens,
    )

    summary = generate_lecture_summary(session=session)
    session.summary = summary.content
    session.save()

    return ai_response.content


def finalize_lecture(session):
    # Mark current topic as completed
    current = get_current_lecture_progress(session)
    if current:
        current.is_completed = True
        current.save()
    
    # Save end time
    now = timezone.now()
    session.ended_at = now
    session.save()

    # Calculate total tokens used in the session
    total_tokens = (
        session.logs
        .filter(role='ai')
        .aggregate(total=Sum('token_count'))['total']
        or 0
    )
    session.total_tokens = total_tokens
    session.save()

    return total_tokens


def lecture_report(session):
    completed_topics = session.progress_records.filter(is_completed=True)

    incomplete_topics = session.progress_records.filter(is_completed=False)
    study_time = (session.ended_at - session.started_at) if session.ended_at and session.started_at else None
    ai_response = generate_lecture_report(session=session)

    report = {
        "generated_report": ai_response.content,
        "total_topics": session.progress_records.count(),
        "completed_topics": completed_topics.count(),
        "total_tokens": session.total_tokens,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
    }
    return report