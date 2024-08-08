from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.utils import timezone
from django.http import JsonResponse
import json
from accounts.models import *
from datetime import timedelta, datetime

@login_required
def checklist(request):
    user_role = request.user.role #자녀/부모 구분
    today = timezone.now()
    linked_users = request.user.followings.all() # 연동된 사용자들
    completed = request.GET.get('completed') or False
    date_str = request.GET.get('date')

    if date_str:
        try:
            today = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            today = timezone.now().date()
    else:
        today = timezone.now().date()

    # 현재 사용자와 연동된 사용자들의 ID를 리스트로 저장
    user_ids = [request.user.id] + list(linked_users.values_list('id', flat=True))
    
    # 현재 사용자의 체크리스트와 연동된 사용자들의 체크리스트 가져오기
    todos = Todo.objects.filter(due_date=today, author_id__in=user_ids).distinct()
    return render(request, 'checklist/home.html', {'todos' : todos, 'current_date':today, 'user_role': user_role, 'completed_filter': completed})

@login_required
def update_status(request, todo_id):
    if request.method == 'POST' and request.user.role == 'parent':
        todo = get_object_or_404(Todo, id=todo_id)
        try:
            data = json.loads(request.body.decode('utf-8'))
            completed = data.get('completed', False)
            todo.completed = completed
            todo.save()

            # 연동된 사용자에게 알림 생성
            linked_users = request.user.followings.all()
            child_users = linked_users.filter(role='child')

            if completed:
                message = f"'{todo.title}'이 완료되었어요."
                Notification.objects.create(user=todo.author, message=message)

            return JsonResponse({'success': True, 'completed': completed})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'success': False}, status=400)

@login_required
def create(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.author = request.user
            todo.save()
            form.save_m2m()  

            # 반복 요일 설정이 있을 경우 반복 생성
            repeat_days = form.cleaned_data['repeat_on']
            if repeat_days:
                start_date = todo.due_date
                if not start_date:
                    start_date = timezone.now().date()

                # 반복 주기를 2주로 설정
                end_date = start_date + timedelta(weeks=2)

                current_date = start_date
                while current_date <= end_date:
                    for day in repeat_days:
                        day_code = day.day_code
                        day_index = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'].index(day_code)
                        current_day_index = current_date.weekday()
                        
                        if current_day_index == day_index:
                            # 중복 검사: 동일 날짜와 제목의 Todo가 이미 존재하는지 확인
                            if not Todo.objects.filter(
                                due_date=current_date,
                                title=todo.title,
                                author=todo.author
                            ).exists():
                                new_todo = Todo.objects.create(
                                    title=todo.title,
                                    due_date=current_date,
                                    due_time=todo.due_time,
                                    completed=todo.completed,
                                    author=todo.author
                                )
                                # 처음 설정한 repeat_on 값을 복사
                                new_todo.repeat_on.set(repeat_days)  # 원래의 repeat_on 필드를 복사
                    
                    current_date += timedelta(days=1)


            return redirect('checklist:home')
    else:
        form = TodoForm()

    return render(request, 'checklist/create.html', {'form': form})


@login_required
def detail(request,id):
    todo = get_object_or_404(Todo, id =id)
    return render(request, 'checklist/detail.html', {'todo':todo})

@login_required
def update(request, todo_id):
    todo = get_object_or_404(Todo, id=todo_id)
    
    if request.method == 'POST':
        form = TodoForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            return redirect('checklist:home')
    else:
        form = TodoForm(instance=todo)
    
    return render(request, 'checklist/update.html', {'form': form, 'todo': todo})

@login_required
def delete(request, id):
    todo = get_object_or_404(Todo, id=id)

    # 연결된 반복 항목 모두 삭제
    repeat_todos = Todo.objects.filter(title=todo.title, author=todo.author, repeat_on__in=todo.repeat_on.all())

    for repeat_todo in repeat_todos:
        repeat_todo.delete()

    todo.delete()
    return redirect('checklist:home')

# 알림창
@login_required
def notification_list(request):
    user = request.user
    user_notifications = Notification.objects.filter(user=user)

    linked_users = user.followings.all()
    linked_users_notifications = Notification.objects.filter(user__in=linked_users)

    notifications = user_notifications.union(linked_users_notifications).order_by('-created_at')
    
    new_notifications = []
    past_notifications = []
    current_date = timezone.now().date()
    current_time = timezone.now().time()

    todos = Todo.objects.filter(author=user, completed=False)

    for todo in todos:
        if todo.due_time:
            for reminder_time in [5, 10, 15, 30]:  # 분 단위로 설정된 알림 시간
                reminder_duration = timedelta(minutes=reminder_time)
                reminder_time_threshold = (datetime.combine(current_date, todo.due_time) + reminder_duration).time()
                
                if current_time >= reminder_time_threshold:
                    # 알림 메시지 생성
                    message = f"'{todo.title}'의 예정 시간이 {reminder_time}분 지났어요."
                    notification, created = Notification.objects.get_or_create(
                        user=user,
                        message=message,
                    )

    for notification in notifications:
        days_since_created = (current_date - notification.created_at.date()).days

        # 알림 데이터에 형식화된 날짜 추가
        formatted_notification = {
            'message': notification.message,
            'created_at': notification.created_at,
            'formatted_date': (notification.created_at.strftime('%Y.%m.%d') if days_since_created >= 3 else None),
            'naturaltime_date': (None if days_since_created >= 3 else notification.created_at)
        }

        if notification.view_count == 0:
            notification.view_count += 1
            notification.is_read = True  
            notification.save()
            new_notifications.append(formatted_notification)
        else:
            past_notifications.append(formatted_notification)

    return render(request, 'checklist/notifications.html', {
        'new_notifications': new_notifications,
        'past_notifications': past_notifications,
    })

# 읽음 처리
@login_required
def mark_as_read(request, notification_id):
    notifications = get_object_or_404(Notification, id=notification_id, user=request.user)
    notifications.is_read = True
    notifications.save()
    return redirect('checklist:notification')
