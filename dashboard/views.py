from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from inspections.models import InspectionRecord
from defects.models import DefectRecord


@login_required
def dashboard(request):
    records = InspectionRecord.objects.all()
    today = records.filter(inspection_date__date=timezone.localdate())
    return render(request, "dashboard/index.html", {
        "today_total": today.count(),
        "today_pass": today.filter(overall_result="PASS").count(),
        "today_fail": today.filter(overall_result="FAIL").count(),
        "open_defects": DefectRecord.objects.exclude(status="CLOSED").count(),
        "recent_defects": DefectRecord.objects.select_related("inspection__batch__product", "defect_type").order_by("-created_at")[:8],
    })
