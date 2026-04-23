from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('neo4j', 'neo4j User'),
        ('metaknowledge', 'metaknowledge User'),
    )
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES)

class MetaKnowledge(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description

class Formula(models.Model):
    """
    公式模型
    """
    meta_knowledge = models.ForeignKey(MetaKnowledge, related_name='formulas', on_delete=models.CASCADE, verbose_name="所属元知识")
    formula_string = models.TextField(verbose_name="公式内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return self.formula_string

class Variable(models.Model):
    """
    变量模型
    """
    variable_name = models.CharField(max_length=255, verbose_name="变量名称")
    variable_meaning = models.CharField(max_length=255, verbose_name="变量意义", help_text="例如：公司负债率")
    reference_count = models.PositiveIntegerField(default=0, verbose_name="引用计数器")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    def __str__(self):
        return f"{self.variable_name} ({self.variable_meaning})"

class FormulaVariable(models.Model):
    """
    公式与变量的关联模型
    """
    formula = models.ForeignKey(Formula, related_name='formula_variables', on_delete=models.CASCADE, verbose_name="公式")
    variable = models.ForeignKey(Variable, related_name='formula_variables', on_delete=models.CASCADE, verbose_name="变量")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        unique_together = ('formula', 'variable')  # 确保公式和变量的组合唯一
        verbose_name = "公式变量关联"
        verbose_name_plural = "公式变量关联"

    def save(self, *args, **kwargs):
        """
        增加引用计数
        """
        if not self.pk:  # 只有在创建时增加引用计数
            self.variable.reference_count += 1
            self.variable.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        减少引用计数，如果计数为0则删除变量
        """
        variable = self.variable
        super().delete(*args, **kwargs)

        # 减少引用计数
        if variable.reference_count > 0:
            variable.reference_count -= 1
            variable.save()

        # 如果引用计数为0，删除 Variable
        if variable.reference_count == 0:
            variable.delete()