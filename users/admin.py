from django import forms
from django.contrib import admin
from .models import Profile

class ProfileAdminForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["followers"].queryset = Profile.objects.exclude(pk=self.instance.pk)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    filter_horizontal = ("followers",)
    list_display = ("user", "followers_count", "following_count")

    def followers_count(self, obj):
        return obj.followers.count()

    def following_count(self, obj):
        return obj.following.count()