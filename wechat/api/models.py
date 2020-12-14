from django.db import models
from  django.contrib.auth.models  import  AbstractUser


# Create your models here.
class UserSimple(models.Model):
    userid = models.CharField(max_length=128,verbose_name='用户ID',unique=True)
    access_count = models.IntegerField(verbose_name='当天访问次数')
    canceled = models.BooleanField(verbose_name='是否关注')
    follow_time = models.DateTimeField(verbose_name='关注时间')
    last_update_time = models.DateTimeField(verbose_name='更新时间')
    is_sponer = models.BooleanField(verbose_name='是否赞赏用户')


    def __str__(self):
        return f'<userid {self.userid}>'

class UserCompleted(models.Model):
    username = models.CharField(max_length=128,verbose_name='用户名')
    userid = models.CharField(max_length=128,verbose_name='用户ID')
    access_count = models.IntegerField(verbose_name='当天访问次数')
    follow_time = models.DateTimeField(max_length=128,verbose_name='关注时间')
    is_sponer = models.BooleanField(verbose_name='是否赞赏用户')


