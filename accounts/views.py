from django.shortcuts import render, redirect
from .forms import RegistrationForm

from .models import Account

from django.contrib import messages, auth

from django.contrib.auth import login as auth_login

from django.contrib.auth.decorators import login_required

# verification email
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator

def register(request):

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            username = email.split('@')[0]

            # Create User Account
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, username = username, email=email, password=password)
            user.phone_number = phone_number



            user.save()

            # User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please activate your account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            #messages.success(request, 'Thank you for registering with us. We have sent you a verification email to your email address. Please verify it !')

            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()    


    context = {
        'form': form,
    }

    return render(request, 'accounts/register.html', context)

def login(request):

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Logged in Successfully')
            return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)

    messages.success(request, 'Logged out Successfully')
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            messages.info(request, 'User already activated')
            return redirect('login')

        if user.is_active:
            messages.info(request, 'User already activated')
            return redirect('login')

        user.is_active = True
        user.save()

        messages.success(request, 'Account activated successfully')
        return redirect('login')

    except Exception as e:
        pass

    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = Account.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Account activated successfully')
    else:
        messages.error(request, 'Activation link is invalid')
        return redirect('register')

    return redirect('login')

@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']

        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # Reset Password Email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })

            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('login')

        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = Account.objects.get(pk=uid)

    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired')
        return redirect('login')


def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()

            messages.success(request, 'Password reset successful')
            return redirect('login')

        else:
            messages.error(request, 'Passwords do not match')
            return redirect('resetPassword')

    else:
        return render(request, 'accounts/resetPassword.html')