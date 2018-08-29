from django.db import models
from jsonfield import JSONField

YES_or_NO=((0,'否'),(1,'是'))

class AuthToken(models.Model):
    username        = models.CharField('用户名称',max_length=8, default='', unique=True)
    token           = models.CharField('用户TOKEN',max_length=64, default='', unique=True)
    sign_date       = models.DateTimeField('注册日期',auto_now_add=True)
    expired_time    = models.IntegerField('有效期限',default=86400) ### Defautl is One day. '0' means never expired.

class Module(models.Model):
    id              = models.AutoField('ID',primary_key=True)
    name            = models.CharField('模块名称',max_length=128, default='', unique=True)
    pillar_required = JSONField(default=[])
    pillar_optional = JSONField(default=[])
    lock_count      = models.IntegerField('锁定计数', default='0')

    def __str__(self):
        return self.name

class Instance(models.Model):
    id                = models.AutoField('ID',primary_key=True)
    name              = models.CharField('子模块名称',max_length=128, default='', unique=True)
    module_belong     = models.ForeignKey('Module', on_delete=models.CASCADE, related_name="instances")
    is_lock           = models.IntegerField('是否锁定', choices=YES_or_NO, default='0')

    def __str__(self):
        return self.name
class IncludeRelationship(models.Model):
    id                = models.AutoField('ID',primary_key=True)
    r_instance        = models.OneToOneField(Instance, on_delete=models.CASCADE, related_name='r_instance')
    r_included        = models.ManyToManyField(Instance)

class Pillar(models.Model):
    id                = models.AutoField('ID',primary_key=True)
    pillar_name       = models.CharField('pillar名称', max_length=128, default='')
    pillar_value      = models.TextField('pillar值', default='')
    environment       = models.CharField('环境标签', max_length=128, default='')
    instance_belong   = models.ForeignKey('Instance', on_delete=models.CASCADE, related_name="pillars")

class Node(models.Model):
    id              = models.AutoField('ID',primary_key=True)
    name            = models.CharField('节点名称',max_length=128, default='', unique=True)
    environment     = models.CharField('所属环境', max_length=128, default='')
    is_lock         = models.IntegerField('是否锁定', choices=YES_or_NO, default='0')
    bind_modules    = models.ManyToManyField(Module)
    bind_instances  = models.ManyToManyField(Instance)

    def __str__(self):
        return self.name

    def pillar(self):
        pl = {}
        for m_obj in self.bind_modules.all():
            pl[m_obj.name] = {}
            for i_obj in self.bind_instances.all():
                if i_obj.module_belong == m_obj:
                    pl[m_obj.name][i_obj.name] = {}
                    ### To get default pillar without environment set.
                    for p_obj in i_obj.pillars.filter(environment=''):
                        pl[m_obj.name][i_obj.name][p_obj.pillar_name] = p_obj.pillar_value

                    ### To update node's pillar with envrironment pillar objects.
                    for p_obj in i_obj.pillars.filter(environment=self.environment):
                        pl[m_obj.name][i_obj.name][p_obj.pillar_name] = p_obj.pillar_value

                    ### To fill pillars of included instances.
                    r_queryset = IncludeRelationship.objects.filter(r_instance=i_obj)
                    if r_queryset.exists():
                        r_obj = r_queryset.get(r_instance=i_obj)
                        r_included = r_obj.r_included.all()
                        if r_included.exists():
                            pl[m_obj.name][i_obj.name]['__include__'] = {}
                            for ii_obj in r_included:
                                pl[m_obj.name][i_obj.name]['__include__'][ii_obj.name] = {}
                                ### To get default pillar without environment set.
                                for p in ii_obj.pillars.filter(environment=''):
                                    pl[m_obj.name][i_obj.name]['__include__'][ii_obj.name][p.pillar_name] = p.pillar_value

                                ### To update node's pillar with envrironment pillar objects.
                                for p in ii_obj.pillars.filter(environment=self.environment):
                                    pl[m_obj.name][i_obj.name]['__include__'][ii_obj.name][p.pillar_name] = p.pillar_value
        return pl
