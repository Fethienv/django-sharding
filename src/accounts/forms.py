from django import forms
from sharding.forms import ShardedUserRegisterForm, ShardedUserAdminCreationForm, ShardedUserAdminChangeForm, ShardedModelForm
from .models import User
from .models import Profile


class RegisterForm(ShardedUserRegisterForm):
    pass

class UserAdminCreationForm(ShardedUserAdminCreationForm):
    pass

class UserAdminChangeForm(ShardedUserAdminChangeForm):
    pass


class ProfileAdminCreationForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ( 'owner', 'location', )

    # def save(self, commit=True):
    #     print("form save")
    #     Profile = super(ProfileAdminCreationForm, self).save(commit=False)


    #     Profile.user.save(using="profile_1")
    #     #print(Profile.user)
    #     #Profile.save(using="profile_1")

    #     # service.member_id = service.member.pk # here is the key command
    #     # service.save()
    #     # if self.cleaned_data['multi_work_place']:
    #     #     work_place = WorkPlace(**{
    #     #         'city': self.cleaned_data['multi_work_place'][0],
    #     #         'street': self.cleaned_data['multi_work_place'][1],
    #     #     })
    #     #     # when there is brand new object is created, there is no service.pk
    #     #     work_place.service = service # how???
    #     #     work_place.save()

    #     return Profile
