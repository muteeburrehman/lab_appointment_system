from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'approval_status')


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile management"""

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'address', 'date_of_birth',
            'approval_status', 'created_at'
        )
        read_only_fields = ('id', 'username', 'role', 'approval_status', 'created_at')

    def validate_email(self, value):
        """Validate email uniqueness (excluding current user)"""
        if self.instance and self.instance.email == value:
            return value

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'role')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                'password': "Passwords don't match"
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password', None)
        # Set approval status to pending
        validated_data['approval_status'] = 'pending'
        # Make user inactive until approved
        validated_data['is_active'] = False

        user = User.objects.create_user(**validated_data)

        # Send notification to admins
        try:
            user.send_admin_notification_email()
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send admin notification: {e}")

        return user


class PendingUserSerializer(serializers.ModelSerializer):
    """Serializer for admin to view pending users"""

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'approval_status',
            'created_at', 'phone', 'address'
        )
        read_only_fields = ('id', 'created_at')


class UserApprovalSerializer(serializers.ModelSerializer):
    """Serializer for approving/rejecting users"""
    action = serializers.ChoiceField(choices=['approve', 'reject'], write_only=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('action', 'rejection_reason')

    def update(self, instance, validated_data):
        action = validated_data.get('action')
        rejection_reason = validated_data.get('rejection_reason', '')

        if action == 'approve':
            instance.approval_status = 'approved'
            instance.is_active = True
            instance.approved_by = self.context['request'].user
            instance.approved_at = timezone.now()
            instance.save()

            # Send approval email
            try:
                instance.send_approval_email()
            except Exception as e:
                print(f"Failed to send approval email: {e}")

        elif action == 'reject':
            instance.approval_status = 'rejected'
            instance.rejection_reason = rejection_reason
            instance.is_active = False
            instance.save()

            # Send rejection email
            try:
                instance.send_rejection_email()
            except Exception as e:
                print(f"Failed to send rejection email: {e}")

        return instance