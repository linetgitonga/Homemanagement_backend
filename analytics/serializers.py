from rest_framework import serializers

class ReportSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=('daily', 'weekly', 'monthly'))
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    format = serializers.ChoiceField(choices=('json', 'pdf', 'excel'), default='json')