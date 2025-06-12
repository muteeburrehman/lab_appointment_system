from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils import timezone
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'role', 'approval_status_display',
        'is_active', 'created_at', 'action_buttons'
    )
    list_filter = ('role', 'approval_status', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-created_at',)

    # Add approval fields to the form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Approval Information', {
            'fields': ('approval_status', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Additional Information', {
            'fields': ('role', 'phone', 'address', 'date_of_birth')
        }),
    )

    readonly_fields = ('approved_by', 'approved_at', 'created_at', 'updated_at')

    def approval_status_display(self, obj):
        """Display approval status with color coding"""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red'
        }
        color = colors.get(obj.approval_status, 'gray')

        # Add visual indicator for superusers
        status_text = obj.get_approval_status_display()
        if obj.is_superuser and obj.approval_status == 'approved':
            status_text += ' (Superuser)'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            status_text
        )

    approval_status_display.short_description = 'Approval Status'

    def action_buttons(self, obj):
        """Display action buttons for pending users"""
        # Superusers should not show action buttons as they're auto-approved
        if obj.is_superuser:
            return format_html('<span style="color: blue;">👑 Superuser</span>')

        if obj.approval_status == 'pending':
            approve_url = reverse('admin:approve_user', args=[obj.pk])
            reject_url = reverse('admin:reject_user', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background-color: green; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Approve</a>'
                '<a class="button" href="{}" style="background-color: red; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">Reject</a>',
                approve_url,
                reject_url
            )
        elif obj.approval_status == 'approved':
            return format_html('<span style="color: green;">✓ Approved</span>')
        elif obj.approval_status == 'rejected':
            return format_html('<span style="color: red;">✗ Rejected</span>')
        return '-'

    action_buttons.short_description = 'Actions'
    action_buttons.allow_tags = True

    def get_urls(self):
        """Add custom URLs for approve/reject actions"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:user_id>/approve/',
                self.admin_site.admin_view(self.approve_user),
                name='approve_user',
            ),
            path(
                '<int:user_id>/reject/',
                self.admin_site.admin_view(self.reject_user),
                name='reject_user',
            ),
        ]
        return custom_urls + urls

    def approve_user(self, request, user_id):
        """Approve a user"""
        try:
            user = User.objects.get(pk=user_id)

            # Prevent manual approval of superusers (they should be auto-approved)
            if user.is_superuser:
                messages.info(request, f'Superuser {user.username} is automatically approved.')
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))

            if user.approval_status != 'pending':
                messages.error(request, f'User {user.username} is not pending approval.')
            else:
                user.approval_status = 'approved'
                user.is_active = True
                user.approved_by = request.user
                user.approved_at = timezone.now()
                user.save()

                # Send approval email
                try:
                    user.send_approval_email()
                    messages.success(request, f'User {user.username} has been approved and notification email sent.')
                except Exception as e:
                    messages.warning(request, f'User {user.username} approved but email notification failed: {str(e)}')

        except User.DoesNotExist:
            messages.error(request, 'User not found.')

        return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))

    def reject_user(self, request, user_id):
        """Reject a user - this should redirect to a form for rejection reason"""
        try:
            user = User.objects.get(pk=user_id)

            # Prevent rejection of superusers
            if user.is_superuser:
                messages.error(request, f'Cannot reject superuser {user.username}.')
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))

            if user.approval_status != 'pending':
                messages.error(request, f'User {user.username} is not pending approval.')
                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))

            # For now, reject with a default reason
            # In a full implementation, you'd want a form for the rejection reason
            if request.method == 'POST':
                rejection_reason = request.POST.get('rejection_reason', 'Not specified')
                user.approval_status = 'rejected'
                user.rejection_reason = rejection_reason
                user.is_active = False
                user.save()

                # Send rejection email
                try:
                    user.send_rejection_email()
                    messages.success(request, f'User {user.username} has been rejected and notification email sent.')
                except Exception as e:
                    messages.warning(request, f'User {user.username} rejected but email notification failed: {str(e)}')

                return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))
            else:
                # Render a simple form for rejection reason
                from django.template.response import TemplateResponse
                context = {
                    'title': f'Reject User: {user.username}',
                    'user': user,
                    'opts': self.model._meta,
                    'has_change_permission': True,
                }
                return TemplateResponse(request, 'admin/reject_user.html', context)

        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return HttpResponseRedirect(reverse('admin:accounts_user_changelist'))

    def get_queryset(self, request):
        """Custom queryset to show additional information"""
        qs = super().get_queryset(request)
        return qs.select_related('approved_by')

    def save_model(self, request, obj, form, change):
        """Override save to handle approval status changes and auto-approve superusers"""

        # Auto-approve superusers
        if obj.is_superuser:
            if obj.approval_status != 'approved':
                obj.approval_status = 'approved'
                obj.is_active = True
                obj.approved_by = request.user if not obj.approved_by else obj.approved_by
                obj.approved_at = timezone.now() if not obj.approved_at else obj.approved_at
                messages.info(request, f'Superuser {obj.username} has been automatically approved.')

        if change:
            # Get the original object to compare changes
            original = User.objects.get(pk=obj.pk)

            # If user was made a superuser, auto-approve them
            if not original.is_superuser and obj.is_superuser:
                obj.approval_status = 'approved'
                obj.is_active = True
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
                messages.success(request, f'User {obj.username} promoted to superuser and automatically approved.')
                super().save_model(request, obj, form, change)
                return

            # If approval status changed to approved (and not a superuser)
            if (not obj.is_superuser and
                    original.approval_status != 'approved' and
                    obj.approval_status == 'approved' and
                    not obj.approved_by):
                obj.approved_by = request.user
                obj.approved_at = timezone.now()
                obj.is_active = True

                # Send approval email
                try:
                    obj.save()
                    obj.send_approval_email()
                    messages.success(request, f'User approved and notification email sent to {obj.email}')
                except Exception as e:
                    messages.warning(request, f'User approved but email notification failed: {str(e)}')
                return

            # If approval status changed to rejected (prevent for superusers)
            elif (original.approval_status != 'rejected' and
                  obj.approval_status == 'rejected'):
                if obj.is_superuser:
                    messages.error(request, 'Cannot reject a superuser.')
                    obj.approval_status = 'approved'  # Reset to approved
                    obj.is_active = True
                else:
                    obj.is_active = False
                    # Send rejection email
                    try:
                        obj.save()
                        obj.send_rejection_email()
                        messages.success(request, f'User rejected and notification email sent to {obj.email}')
                    except Exception as e:
                        messages.warning(request, f'User rejected but email notification failed: {str(e)}')
                    return

        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        """Make approval fields readonly for superusers"""
        readonly = list(self.readonly_fields)
        if obj and obj.is_superuser:
            readonly.extend(['approval_status'])
        return readonly


# Custom admin site configuration
admin.site.site_header = "User Management System"
admin.site.site_title = "User Admin"
admin.site.index_title = "Welcome to User Management"