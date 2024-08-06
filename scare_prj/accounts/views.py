from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from .models import *
from django.contrib.auth.forms import AuthenticationForm # 로그인
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.urls import reverse

# 임시페이지
def comming_soon(request):
    return render(request, 'accounts/comming_soon.html')

def index(request):
    return render(request, 'accounts/index.html')

# 회원가입
def signup_view(request):
    if request.method == "GET":
        form = SignUpForm()
        return render(request, 'accounts/signup.html', {'form' : form})
    form = SignUpForm(request.POST)

    if form.is_valid():
        user = form.save(commit=False) # role 추가 변경 가능하도록
        user.role = form.cleaned_data.get('role')
        user.save()
        return redirect('accounts:login')
    else:
        return render(request, 'accounts/signup.html', {'form' : form})

# 로그인
def login_view(request):
    if request.method == "GET":
        return render(request, 'accounts/login.html', {'form' : AuthenticationForm})

    form = AuthenticationForm(request, data = request.POST)
    if form.is_valid():
        login(request, form.user_cache)
        return redirect('cal:home')
    return render(request, 'accounts/login.html', {'form' : form, 'login_failed': True})

# 로그아웃
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('accounts:index')

@login_required
# 마이페이지
def mypage(request):
    return render(request, 'accounts/mypage.html')

@login_required
# 나의 정보 수정
def myinfo_update(request):
    info = request.user
    default_image_path = 'default_mypage_image.jpg'

    if request.method == "POST":
        image = request.FILES.get('image')
        info.nickname = request.POST.get('nickname')

        # 기존 이미지가 기본값이 아닌 경우만 삭제
        if info.image.name != default_image_path:
            info.image.delete()

        if image:
            info.image = image

        info.save()
        return redirect('accounts:mypage')
    return render(request, 'accounts/myinfo_update.html', {'info':info})


@login_required
def gearing(request, id):
    user = get_object_or_404(User, id=id)
    followers = user.followings.all()
    follow_requests = user.received_follow_requests.filter(status='pending')

    searched = False
    searched_user = None
    already_linked = False

    if 'gear_id' in request.GET:
        searched = True
        gear_id = request.GET.get('gear_id')
        try:
            searched_user = User.objects.get(username=gear_id)
            if user.followings.filter(id=searched_user.id).exists():
                already_linked = True
        except User.DoesNotExist:
            searched_user = None

    return render(request, 'accounts/gearing.html', {
        'follow_requests': follow_requests,
        'followers': followers,
        'searched': searched,
        'searched_user': searched_user,
        'already_linked': already_linked
    })


# 계정 연동 신청
@login_required
def link_account(request, user_id):
    if request.method == 'POST':
        from_user = request.user
        to_user = get_object_or_404(User, id=user_id)
        
        if from_user == to_user:
            return JsonResponse(
                {"message": "자신에게 친구 신청을 할 수 없습니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        if from_user.followings.filter(id=to_user.id).exists():
            return JsonResponse(
                {"message": "이미 연동된 계정입니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        follow_request, created = Follow.objects.get_or_create(
            from_user=from_user,
            to_user=to_user,
            status='pending'
        )
        
        if created:
            return JsonResponse(
                {"message": "친구 신청을 보냈습니다.", "redirect_url": reverse('accounts:gearing', args=[from_user.id])},
                status=201,
                json_dumps_params={'ensure_ascii': False}
            )
        else:
            return JsonResponse(
                {"message": "이미 친구 신청을 보냈습니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

    return HttpResponseForbidden()



# 연동 신청 수락
@login_required
def follow_accept(request):
    if request.method == 'POST':
        follow_request_id = request.POST.get('follow_request_id')
        if not follow_request_id:
            return JsonResponse(
                {"message": "follow_request_id가 필요합니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        follow_request = get_object_or_404(Follow, id=follow_request_id)
        
        if follow_request.to_user != request.user:
            return JsonResponse(
                {"message": "권한이 없습니다."},
                status=403,
                json_dumps_params={'ensure_ascii': False}
            )
        if follow_request.status != 'pending':
            return JsonResponse(
                {"message": "이미 처리된 요청입니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        follow_request.status = 'accepted'
        follow_request.save()

        from_user = follow_request.from_user
        to_user = follow_request.to_user

        from_user.followings.add(to_user)
        to_user.followings.add(from_user)

        return JsonResponse(
            {"message": "친구 신청을 수락했습니다.",
            "redirect": reverse('accounts:gearing', kwargs={'id': request.user.id})},
            status=200,
            json_dumps_params={'ensure_ascii': False}
        )

    return HttpResponseForbidden()

# 연동 신청 거절
@login_required
def follow_reject(request):
    if request.method == 'POST':
        follow_request_id = request.POST.get('follow_request_id')
        if not follow_request_id:
            return JsonResponse(
                {"message": "follow_request_id가 필요합니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        follow_request = get_object_or_404(Follow, id=follow_request_id)

        if follow_request.to_user != request.user:
            return JsonResponse(
                {"message": "권한이 없습니다."},
                status=403,
                json_dumps_params={'ensure_ascii': False}
            )
        
        if follow_request.status != 'pending':
            return JsonResponse(
                {"message": "이미 처리된 요청입니다."},
                status=400,
                json_dumps_params={'ensure_ascii': False}
            )

        follow_request.status = 'rejected'
        follow_request.save()

        return JsonResponse(
            {"message": "친구 신청을 거절했습니다.",
            "redirect": reverse('accounts:gearing', kwargs={'id': request.user.id})},
            status=200,
            json_dumps_params={'ensure_ascii': False}
        )

    return HttpResponseForbidden()

# 연동 삭제
def unfollow(request, user_id):
    current_user = request.user
    user_to_unfollow = get_object_or_404(User, id=user_id)

    Follow.objects.filter(from_user=current_user, to_user=user_to_unfollow).delete()
    Follow.objects.filter(from_user=user_to_unfollow, to_user=current_user).delete()

    if user_to_unfollow in current_user.followings.all():
        current_user.followings.remove(user_to_unfollow)
    if current_user in user_to_unfollow.followings.all():
        user_to_unfollow.followings.remove(current_user)

    return redirect('accounts:gearing', id=current_user.id) if user_to_unfollow in current_user.followings.all() else JsonResponse(
        {"message": "연동 계정을 삭제했습니다."},
        status=400,
        json_dumps_params={'ensure_ascii': False}
    )

#알람
@login_required
def alarm(request):
    return render(request, 'accounts/alarm.html')