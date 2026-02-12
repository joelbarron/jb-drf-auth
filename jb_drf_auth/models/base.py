from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

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


class AbstractUserOwnedModel(models.Model):
    """
    Abstract base for models owned by a user.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)

    class Meta:
        abstract = True


class AbstractProfileOwnedModel(models.Model):
    """
    Abstract base for models owned by a profile.
    """

    profile = models.ForeignKey(
        get_setting("PROFILE_MODEL") or "authentication.Profile",
        on_delete=models.CASCADE,
        db_index=True,
    )

    class Meta:
        abstract = True


class AbstractJbPersonDataModel(models.Model):
    """
    Abstract base for person-like profile fields.
    """

    GENDER_CHOICES = get_setting("PROFILE_GENDER_CHOICES")

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name_1 = models.CharField(max_length=150, blank=True, null=True)
    last_name_2 = models.CharField(max_length=150, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=50,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True


class AbstractPersonCore(AbstractJbPersonDataModel):
    """
    Abstract core for person identity fields.
    """

    national_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    # Contact
    contact_email = models.EmailField(blank=True, null=True, db_index=True)
    # Store phone numbers in E.164 format (e.g. +525512345678)
    mobile_phone = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    home_phone = models.CharField(max_length=20, blank=True, null=True)
    work_phone = models.CharField(max_length=20, blank=True, null=True)
    work_phone_ext = models.CharField(max_length=10, blank=True, null=True)

    # Address
    address_line_1 = models.CharField(max_length=255, blank=True, null=True)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    country_code = models.CharField(max_length=2, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)

    # Additional data
    marital_status = models.CharField(max_length=50, blank=True, null=True)
    birth_place = models.CharField(max_length=255, blank=True, null=True)
    insurance_number = models.CharField(max_length=100, blank=True, null=True)
    scholarship = models.CharField(max_length=100, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)

    # Emergency contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)

    # Document files
    id_document_front = models.ImageField(
        upload_to=get_setting("PERSON_ID_DOCUMENTS_UPLOAD_TO"),
        blank=True,
        null=True,
    )
    id_document_back = models.ImageField(
        upload_to=get_setting("PERSON_ID_DOCUMENTS_UPLOAD_TO"),
        blank=True,
        null=True,
    )

    is_identity_verified = models.BooleanField(default=False)

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
        error_messages={"unique": _("Ya existe un usuario con este correo.")},
    )
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_verified = models.BooleanField("verified", default=False)
    terms_and_conditions = models.DateTimeField(
        "terms_and_conditions",
        blank=True,
        null=True,
    )
    settings = models.JSONField(default=dict, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.email}-{self.username}"

    def get_default_profile(self):
        """
        Returns the default profile for this user.
        """
        return self.profiles.filter(is_default=True).first()

    def _user_settings(self):
        return self.settings if isinstance(self.settings, dict) else {}

    @property
    def language(self):
        return self._user_settings().get("language") or settings.LANGUAGE_CODE

    @language.setter
    def language(self, value):
        payload = self._user_settings()
        payload["language"] = value
        self.settings = payload

    @property
    def timezone(self):
        return self._user_settings().get("timezone") or settings.TIME_ZONE

    @timezone.setter
    def timezone(self, value):
        payload = self._user_settings()
        payload["timezone"] = value
        self.settings = payload


class AbstractJbProfile(AbstractSafeDeleteModel, AbstractTimeStampedModel, AbstractJbPersonDataModel):
    """
    Abstract base for Profile.
    NOTE: A User has MANY profiles.
    """
    ROLE_CHOICES = get_setting("PROFILE_ROLE_CHOICES")

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
    settings = models.JSONField(default=dict, blank=True)

    picture = models.ImageField(
        upload_to=get_setting("PERSON_PICTURE_UPLOAD_TO") or get_setting("PROFILE_PICTURE_UPLOAD_TO"),
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
        return self.full_name

    @staticmethod
    def _join_non_empty(parts):
        return " ".join([part for part in parts if part and str(part).strip()]).strip()

    @property
    def display_name(self):
        first_last_name = self.last_name_1 or self.last_name_2
        return self._join_non_empty([self.first_name, first_last_name])

    @property
    def full_name(self):
        return self._join_non_empty([self.first_name, self.last_name_1, self.last_name_2])

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
    notification_token = models.CharField(max_length=500, null=True, blank=True)
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
    last_sent_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return f"{self.channel} OTP for {self.email or self.phone}: {self.code}"


class AbstractJbSmsLog(AbstractTimeStampedModel):
    STATUS_CHOICES = (
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    phone = models.CharField(max_length=30)
    message = models.TextField()
    provider = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True


class AbstractJbEmailLog(AbstractTimeStampedModel):
    STATUS_CHOICES = (
        ("sent", "Sent"),
        ("failed", "Failed"),
    )

    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    text_body = models.TextField()
    html_body = models.TextField(blank=True, null=True)
    provider = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True, null=True)
    template_name = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        abstract = True


class AbstractJbSocialAccount(AbstractTimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="social_accounts",
    )
    provider = models.CharField(max_length=30, db_index=True)
    provider_user_id = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    email_verified = models.BooleanField(default=False)
    picture_url = models.URLField(max_length=1000, blank=True, null=True)
    raw_response = models.JSONField(default=dict, blank=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = (
            ("provider", "provider_user_id"),
            ("user", "provider"),
        )
        indexes = [
            models.Index(fields=["provider", "provider_user_id"]),
            models.Index(fields=["email"]),
        ]
