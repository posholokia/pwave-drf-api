from django.contrib.auth import get_user_model

from celery import shared_task

from notification.create_notify.creator import (CommentNotification,
                                                TaskNotification,
                                                WorkSpaceNotification,
                                                DeleteTaskNotification,
                                                DeadlineNotification)

from workspaces.models import Task, WorkSpace

User = get_user_model()


@shared_task
def end_deadline(pk: int):
    task = Task.objects.get(pk=pk)
    DeadlineNotification(obj=task).handler()


@shared_task
def run_task_notification(old, user, request):
    task = Task.objects.get(pk=old['id'])
    TaskNotification(
        request=request,
        obj=task,
        user=user,
        old=old
    ).handler()


@shared_task
def run_del_task_notification(old, user, request):
    obj = None
    DeleteTaskNotification(
        request=request,
        obj=obj,
        user=user,
        old=old
    ).handler()


@shared_task
def run_ws_notification(user, request, pk):
    ws = WorkSpace.objects.get(pk=pk)
    WorkSpaceNotification(
        request=request,
        obj=ws,
        user=user
    ).handler()


@shared_task
def run_comment_notification(user, request, pk):
    task = Task.objects.get(pk=pk)
    CommentNotification(
        request=request,
        obj=task,
        user=user
    ).handler()
