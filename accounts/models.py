from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.mail import send_mail
from django.conf import settings


class User(AbstractUser):
    ROLE_CHOICES = [
        ('superuser', 'Superuser'),
        ('admin', 'Admin'),
        ('lab_owner', 'Lab Owner'),
        ('user', 'User'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Approval fields
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - {self.get_approval_status_display()}"

    @property
    def is_approved(self):
        return self.approval_status == 'approved'

    def send_approval_email(self):
        """Send email when user is approved"""
        subject = 'Account Approved - Welcome!'
        message = f"""
        Hi {self.username},

        Great news! Your account has been approved and you can now access the platform.

        You can login at: {settings.FRONTEND_URL}/login

        Welcome aboard!
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )

    def send_rejection_email(self):
        """Send email when user is rejected"""
        subject = 'Account Registration Update'
        message = f"""
        Hi {self.username},

        We regret to inform you that your account registration has not been approved at this time.

        Reason: {self.rejection_reason or 'Not specified'}

        If you have questions, please contact support.
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )

    def send_admin_notification_email(self):
        """Send notification to superusers when new user registers"""
        superusers = User.objects.filter(is_superuser=True)
        admin_emails = [user.email for user in superusers if user.email]

        if admin_emails:
            subject = 'New User Registration Pending Approval'
            message = f"""
            A new user has registered and is pending approval:

            Username: {self.username}
            Email: {self.email}
            Role: {self.get_role_display()}
            Registration Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}

            Login to the admin panel to approve or reject this user:
            {settings.FRONTEND_URL}/admin/pending-users
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                admin_emails,
                fail_silently=False,
            )