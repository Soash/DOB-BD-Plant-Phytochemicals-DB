import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Prefetch, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Phytochemical, PlantRequest

def bmppd(request):
    return render(request, 'core/bmppd.html')

# def bmppd_result(request):
#     query = request.GET.get('q', '').strip()
#     results = []

#     if query:
#         qs = Phytochemical.objects.filter(
#             Q(plant__scientific_name__icontains=query) |
#             Q(plant__common_names__name__icontains=query) |
#             Q(compound_name__icontains=query) |
#             Q(cid__icontains=query)
#         ).select_related('plant').distinct()

#         # Prepare a list of dicts for the template
#         for p in qs:
#             # Combine all common names for this plant
#             common_names = p.plant.common_names.all()
#             common_name = ", ".join([c.name for c in common_names]) if common_names else ''
            
#             results.append({
#                 'plant_name': p.plant.scientific_name,
#                 'common_name': common_name,
#                 'compound_name': p.compound_name,
#                 'cid': p.cid,
#                 'reference': p.reference,
#             })

#     context = {
#         'query': query,
#         'results': results
#     }
#     return render(request, 'core/bmppd_result.html', context)




def bmppd_result(request):
    query = request.GET.get('q', '').strip()
    results = []
    warnings = []
    max_results = 800

    # Check if query is too short
    if not query or len(query) < 4:
        warnings.append("Too short query to search.")
    else:
        # Filter the queryset
        qs = (
            Phytochemical.objects
            .filter(
                Q(plant__scientific_name__icontains=query) |
                Q(plant__common_names__name__icontains=query) |
                Q(compound_name__icontains=query) |
                Q(cid__icontains=query)
            )
            .select_related('plant')
            .prefetch_related(Prefetch('plant__common_names'))
            .distinct()[:max_results]
        )

        # Prepare results
        for p in qs:
            common_name = ", ".join(c.name for c in p.plant.common_names.all())
            results.append({
                'plant_name': p.plant.scientific_name,
                'common_name': common_name,
                'compound_name': p.compound_name,
                'cid': p.cid,
                'reference': p.reference,
            })

        # Warn if results hit the limit
        # if len(results) == max_results:
        #     warnings.append(f"Showing only the first {max_results} results. Please refine your search to see more.")

    context = {
        'query': query,
        'results': results,
        'warnings': warnings,
    }

    return render(request, 'core/bmppd_result.html', context)











def reference(request):
    ref = request.GET.get("ref", "")
    return render(request, 'core/reference.html', {'reference': ref})

def about(request):
    return render(request, 'core/about.html')

def acknowledgement(request):
    # Aggregate compound counts in DB
    # compounds = (
    #     Phytochemical.objects
    #     .values('compound_name')
    #     .annotate(total_count=Count('id'))
    #     .order_by('-total_count')
    # )

    # # Write to log file (UTF-8 safe)
    # with open('phytochemical_log.txt', 'w', encoding='utf-8') as log_file:
    #     for c in compounds:
    #         log_file.write(f"{c['compound_name']}: {c['total_count']}\n")

    return render(
        request,
        'core/acknowledgement.html',
    )


def request_plant(request):
    if request.method == 'POST':
        plant_name = request.POST.get('plant_name', '').strip()
        email = request.POST.get('email', '').strip()

        if not plant_name or not email:
            return JsonResponse({'status': 'error', 'message': 'Plant name and email are required.'}, status=400)

        req = PlantRequest.objects.create(plant_name=plant_name, email=email)

        # Send email notification to dawn.of.bioinformatics@gmail.com
        try:
            send_mail(
                subject=f"[BMPPD] New Plant Data Requested: {plant_name}",
                message=f"A user has requested phytochemical data for a missing plant.\n\n"
                        f"Plant Name: {plant_name}\n"
                        f"Requester Email: {email}\n"
                        f"Requested At: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                        f"You can manage this request from the staff dashboard.",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bmppd.org'),
                recipient_list=['dawn.of.bioinformatics@gmail.com'],
                fail_silently=True,
            )
        except Exception:
            pass

        return JsonResponse({
            'status': 'success',
            'message': 'Your request has been submitted successfully! We will notify you via email once uploaded.'
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@staff_member_required
def manage_requests(request):
    requests_list = PlantRequest.objects.all().order_by('-created_at')
    return render(request, 'core/manage_requests.html', {'requests': requests_list})


@staff_member_required
def notify_plant_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(PlantRequest, pk=pk)
        try:
            send_mail(
                subject=f"[BMPPD] Requested Data Uploaded: {req.plant_name}",
                message=f"Dear User,\n\nWe are pleased to inform you that the phytochemical data for \"{req.plant_name}\" has been uploaded to the Bangladeshi Medicinal Plant Phytochemicals Database (BMPPD).\n\nYou can now search and explore the data at https://bmppd.org/\n\nBest regards,\nDawnilab / BMPPD Team",
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bmppd.org'),
                recipient_list=[req.email],
                fail_silently=False,
            )
            req.status = 'uploaded'
            req.notified_at = timezone.now()
            req.save()
            return JsonResponse({'status': 'success', 'message': f'Notification sent to {req.email}!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to send email: {str(e)}'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@staff_member_required
def edit_plant_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(PlantRequest, pk=pk)
        req.plant_name = request.POST.get('plant_name', req.plant_name).strip()
        req.email = request.POST.get('email', req.email).strip()
        req.status = request.POST.get('status', req.status).strip()
        req.save()
        return JsonResponse({'status': 'success', 'message': 'Request updated successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


@staff_member_required
def delete_plant_request(request, pk):
    if request.method == 'POST':
        req = get_object_or_404(PlantRequest, pk=pk)
        req.delete()
        return JsonResponse({'status': 'success', 'message': 'Request deleted successfully!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)





