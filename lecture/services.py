from datetime import timedelta

from django.db import transaction
from django.db.models import Max, Sum
from django.utils import timezone

from ai_support.modules.lecture.generate_lecture import (
    generate_lecture,
    generate_lecture_answer,
    generate_lecture_report,
    generate_lecture_summary,
    generate_update_report,
)

from .models import LectureLog, LectureProgress, LectureSession


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
        "current_topic": next_progress.topic,
        "lecture_content": ai_response,
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

    return ai_response


def finalize_lecture(session):
    # Mark current topic as completed
    current = get_current_lecture_progress(session)
    if current:
        current.is_completed = True
        current.save()
    
    # Save end time
    slice = session.time_slices.filter(ended_at__isnull=True).last()
    if slice:
        slice.ended_at = timezone.now()
        slice.save()
    
    # Calculate total study time
    total_time = timedelta()
    for time_slice in session.time_slices.exclude(ended_at__isnull=True):
        total_time += (time_slice.ended_at - time_slice.started_at)

    session.duration_seconds = int(total_time.total_seconds())


    # Calculate total tokens used in the session
    total_tokens = (
        session.logs
        .aggregate(total=Sum('token_count'))['total']
        or 0
    )
    session.used_tokens = total_tokens

    # Mark session as finished
    session.is_finished = True
    session.save()


def create_lecture_report(session):
    ai_response = generate_lecture_report(session=session)

    if not ai_response:
        raise ValueError("Failed to generate lecture report.")

    # Update session with report and last log id
    last_log = session.logs.order_by("id").last()
    session.last_report_log_id = last_log.id if last_log else None
    session.report = ai_response.content
    session.save()
    
    next_progress = get_current_lecture_progress(session)

    report = {
        "generated_report": ai_response.content,
        "used_tokens": session.used_tokens,
        "total_study_time_seconds": session.duration_seconds,
        "completed": True if not next_progress else False,
    }
    return report


def update_lecture_report(session):
    ai_response = generate_update_report(session=session)

    if not ai_response:
        raise ValueError("Failed to generate lecture report.")

    # Update session with report and last log id
    last_log = session.logs.order_by("id").last()
    session.last_report_log_id = last_log.id if last_log else None
    session.report = ai_response.content
    session.save()

    next_progress = get_current_lecture_progress(session)   

    report = {
        "generated_report": ai_response.content,
        "used_tokens": session.used_tokens,
        "total_study_time_seconds": session.duration_seconds,
        "completed": True if not next_progress else False,
    }
    return report
