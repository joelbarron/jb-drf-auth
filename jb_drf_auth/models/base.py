from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from safedelete.models import SafeDeleteModel, SOFT_DELETE

from jb_drf_auth.conf import get_setting
from jb_drf_auth.managers import UserManager


class AbstractTimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AbstractSafeDeleteModel(SafeDeleteModel):
    """
    Abstract base for soft delete using django-safedelete.
    """
    _safedelete_policy = SOFT_DELETE

    class Meta:
        abstract = True


class AbstractJbUser(AbstractSafeDeleteModel, AbstractTimeStampedModel, AbstractUser):
    """
    Abstract base for User.
    Projects can extend it in their accounts app.
    """
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    first_name = None
    last_name = None

    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={"unique": "Ya existe un usuario con este correo."},
    )
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_verified = models.BooleanField("verified", default=False)
    terms_and_conditions = models.DateTimeField(
        "terms_and_conditions",
        blank=True,
        null=True,
    )
    language = models.CharField(max_length=10, default=settings.LANGUAGE_CODE)
    timezone = models.CharField(max_length=50, default=settings.TIME_ZONE)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.email}-{self.username}"

    def get_default_profile(self):
        """
        Returns the default profile for this user.
        """
        return self.profiles.filter(is_default=True).first()


class AbstractJbProfile(AbstractSafeDeleteModel, AbstractTimeStampedModel):
    """
    Abstract base for Profile.
    NOTE: A User has MANY profiles.
    """
    ROLE_CHOICES = get_setting("PROFILE_ROLE_CHOICES")
    GENDER_CHOICES = get_setting("PROFILE_GENDER_CHOICES")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profiles",
        db_index=True,
    )

    is_default = models.BooleanField(default=False)

    role = models.CharField(
        max_length=30,
        default=get_setting("DEFAULT_PROFILE_ROLE"),
        choices=ROLE_CHOICES,
    )

    first_name = models.CharField(max_length=100, blank=True, null=True)
    middle_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=50,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )
    picture = models.ImageField(
        upload_to=get_setting("PROFILE_PICTURE_UPLOAD_TO"),
        max_length=500,
        blank=True,
        null=True,
    )

    label = models.CharField(max_length=80, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        if self.is_default:
            self.__class__.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class AbstractJbDevice(AbstractSafeDeleteModel, AbstractTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
    )
    platform = models.CharField(max_length=250, null=True, blank=True)
    name = models.CharField(max_length=250, null=True, blank=True)
    token = models.CharField(max_length=250, null=True, blank=True)
    linked_at = models.DateTimeField(
        "linked at",
        help_text="Date time on which the device was linked to profile.",
        auto_now_add=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.platform} {self.name}".strip()


class AbstractJbOtpCode(AbstractSafeDeleteModel, AbstractTimeStampedModel):
    """
    Model for one-time password (OTP) codes for email/phone authentication.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="otp_codes",
    )
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    code = models.CharField(max_length=6, blank=False)
    channel = models.CharField(
        max_length=10,
        choices=[("email", "Email"), ("sms", "SMS")],
    )
    valid_until = models.DateTimeField(blank=False, null=False)
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.channel} OTP for {self.email or self.phone}: {self.code}"
