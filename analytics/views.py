import io
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsHomeowner, IsViewerInHousehold, IsAdmin
from finances.models import Expense
from django.db.models import Sum
from django.http import HttpResponse
from openpyxl import Workbook

class ReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsHomeowner | IsViewerInHousehold | IsAdmin]

    def list(self, request):
        serializer = ReportSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        period = serializer.data['period']
        # Example aggregation
        queryset = Expense.objects.filter(household=request.user.householdmembership_set.first().household)
        if period == 'daily':
            data = queryset.values('date').annotate(total=Sum('amount'))
        # Similar for weekly/monthly using date_trunc

        fmt = serializer.data['format']
        if fmt == 'json':
            return Response(data)
        elif fmt == 'pdf':
            # Import WeasyPrint lazily to avoid import-time failures when
            # native libraries (cairo, pango, gobject) are not available on the system.
            try:
                from weasyprint import HTML
            except Exception as exc:
                # Provide a helpful error message for missing native dependencies
                return Response(
                    {'detail': 'PDF generation is unavailable: missing native dependencies for WeasyPrint. '
                               'See project docs or run the project on a system with Cairo/Pango/GObject installed. '
                               f'Underlying error: {exc!s}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            html = '<html><body><h1>Report</h1><p>Data: {}</p></body></html>'.format(data)
            pdf = HTML(string=html).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="report.pdf"'
            return response
        elif fmt == 'excel':
            wb = Workbook()
            ws = wb.active
            ws.append(['Date', 'Total'])
            for row in data:
                ws.append([row['date'], row['total']])
            output = io.BytesIO()
            wb.save(output)
            response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="report.xlsx"'
            return response