# serializers.py
from rest_framework import serializers
from .models import MetaKnowledge, Formula, Variable


class VariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variable
        fields = ['id', 'variable_name', 'variable_type']

class FormulaSerializer(serializers.ModelSerializer):
    variables = serializers.SerializerMethodField()

    class Meta:
        model = Formula
        fields = ['id', 'formula_string', 'variables']

    def get_variables(self, obj):
        variables = Variable.objects.filter(formula_variables__formula=obj)
        return VariableSerializer(variables, many=True).data

class MetaKnowledgeSerializer(serializers.ModelSerializer):
    formulas = FormulaSerializer(many=True, read_only=True)

    class Meta:
        model = MetaKnowledge
        fields = ['id', 'description', 'formulas']