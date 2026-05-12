import csv
import json
from io import BytesIO, StringIO
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from scraper.models import Profile
from .models import ExportHistory

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


@login_required
def export_dashboard(request):
    """
    Export options dashboard
    """
    # Get export history for this user
    export_history = ExportHistory.objects.filter(user=request.user)[:20]
    
    # Get statistics
    total_profiles = Profile.objects.count()
    
    context = {
        'total_profiles': total_profiles,
        'export_history': export_history,
        'pandas_available': PANDAS_AVAILABLE,
        'reportlab_available': REPORTLAB_AVAILABLE,
    }
    
    return render(request, 'exports/dashboard.html', context)


@login_required
def export_csv(request):
    """
    Export profiles to CSV format
    """
    # Get filter parameters
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search = request.GET.get('search', '')
    
    # Get profiles based on filters
    profiles = Profile.objects.all().order_by('-created_at')
    
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    if location:
        profiles = profiles.filter(location__icontains=location)
    if search:
        profiles = profiles.filter(
            models.Q(name__icontains=search) |
            models.Q(headline__icontains=search) |
            models.Q(skills__icontains=search)
        )
    
    # Create response
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="linkedin_profiles_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'ID', 'Name', 'Headline', 'Location', 'Category',
        'LinkedIn URL', 'Skills', 'Search Keyword',
        'Created At', 'Last Scraped'
    ])
    
    # Write data
    for profile in profiles:
        writer.writerow([
            profile.id,
            profile.name,
            profile.headline or '',
            profile.location or '',
            profile.get_category_display(),
            profile.linkedin_url,
            profile.skills or '',
            profile.search_keyword or '',
            profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            profile.last_scraped_at.strftime('%Y-%m-%d %H:%M:%S') if profile.last_scraped_at else '',
        ])
    
    # Save export history
    ExportHistory.objects.create(
        user=request.user,
        export_format='csv',
        export_type='all',
        file_name=f'linkedin_profiles_{timestamp}.csv',
        record_count=profiles.count(),
        filters_used={
            'category': category,
            'location': location,
            'search': search
        }
    )
    
    messages.success(request, f'✅ CSV exported! Total {profiles.count()} profiles.')
    return response


@login_required
def export_excel(request):
    """
    Export profiles to Excel format
    """
    if not PANDAS_AVAILABLE:
        messages.error(request, 'Pandas is not installed. Please contact administrator.')
        return redirect('export_dashboard')
    
    # Get filter parameters
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search = request.GET.get('search', '')
    
    # Get profiles
    profiles = Profile.objects.all().order_by('-created_at')
    
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    if location:
        profiles = profiles.filter(location__icontains=location)
    if search:
        profiles = profiles.filter(
            models.Q(name__icontains=search) |
            models.Q(headline__icontains=search) |
            models.Q(skills__icontains=search)
        )
    
    # Convert to DataFrame
    data = []
    for profile in profiles:
        data.append({
            'ID': profile.id,
            'Name': profile.name,
            'Headline': profile.headline or '',
            'Location': profile.location or '',
            'Category': profile.get_category_display(),
            'LinkedIn URL': profile.linkedin_url,
            'Skills': profile.skills or '',
            'Search Keyword': profile.search_keyword or '',
            'Created At': profile.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Last Scraped': profile.last_scraped_at.strftime('%Y-%m-%d %H:%M:%S') if profile.last_scraped_at else '',
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main sheet
        df.to_excel(writer, sheet_name='LinkedIn Profiles', index=False)
        
        # Statistics sheet
        stats_data = {
            'Metric': ['Total Profiles', 'Categories', 'Export Date'],
            'Value': [len(df), df['Category'].nunique(), timezone.now().strftime('%Y-%m-%d %H:%M:%S')]
        }
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='Statistics', index=False)
        
        # Category wise count
        category_counts = df['Category'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        category_counts.to_excel(writer, sheet_name='Category Summary', index=False)
    
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="linkedin_profiles_{timestamp}.xlsx"'
    
    # Save export history
    ExportHistory.objects.create(
        user=request.user,
        export_format='excel',
        export_type='all',
        file_name=f'linkedin_profiles_{timestamp}.xlsx',
        record_count=len(df),
        filters_used={
            'category': category,
            'location': location,
            'search': search
        }
    )
    
    messages.success(request, f'✅ Excel exported! Total {len(df)} profiles.')
    return response


@login_required
def export_pdf(request):
    """
    Export profiles to PDF format
    """
    if not REPORTLAB_AVAILABLE:
        messages.error(request, 'ReportLab is not installed. Please contact administrator.')
        return redirect('export_dashboard')
    
    from django.db import models
    
    # Get filter parameters
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')
    search = request.GET.get('search', '')
    
    # Get profiles (limit to 100 for PDF to avoid huge files)
    profiles = Profile.objects.all().order_by('-created_at')
    
    if category and category != 'all':
        profiles = profiles.filter(category=category)
    if location:
        profiles = profiles.filter(location__icontains=location)
    if search:
        profiles = profiles.filter(
            models.Q(name__icontains=search) |
            models.Q(headline__icontains=search) |
            models.Q(skills__icontains=search)
        )
    
    profiles = profiles[:100]  # Limit to 100 for PDF
    
    # Create PDF response
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="linkedin_profiles_{timestamp}.pdf"'
    
    # Build PDF
    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"LinkedIn Profiles Export - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))
    
    # Table data
    table_data = [
        ['Name', 'Headline', 'Location', 'Category', 'Skills']
    ]
    
    for profile in profiles[:20]:  # Limit to 20 for PDF readability
        table_data.append([
            Paragraph(profile.name[:40], styles['Normal']),
            Paragraph((profile.headline or '')[:50], styles['Normal']),
            Paragraph((profile.location or '')[:30], styles['Normal']),
            profile.get_category_display(),
            Paragraph((profile.skills or '')[:60], styles['Normal']),
        ])
    
    # Create table
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    # Save export history
    ExportHistory.objects.create(
        user=request.user,
        export_format='pdf',
        export_type='all',
        file_name=f'linkedin_profiles_{timestamp}.pdf',
        record_count=profiles.count(),
        filters_used={
            'category': category,
            'location': location,
            'search': search
        }
    )
    
    messages.success(request, f'✅ PDF exported! Total {profiles.count()} profiles.')
    return response


@login_required
def export_single_profile(request, profile_id, format='csv'):
    """
    Export a single profile
    """
    profile = get_object_or_404(Profile, id=profile_id)
    
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{profile.name}_profile.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Field', 'Value'])
        writer.writerow(['Name', profile.name])
        writer.writerow(['Headline', profile.headline or ''])
        writer.writerow(['Location', profile.location or ''])
        writer.writerow(['Category', profile.get_category_display()])
        writer.writerow(['LinkedIn URL', profile.linkedin_url])
        writer.writerow(['Skills', profile.skills or ''])
        writer.writerow(['Created At', profile.created_at.strftime('%Y-%m-%d %H:%M:%S')])
        
    elif format == 'json':
        response = JsonResponse({
            'id': profile.id,
            'name': profile.name,
            'headline': profile.headline,
            'location': profile.location,
            'category': profile.get_category_display(),
            'linkedin_url': profile.linkedin_url,
            'skills': profile.skills,
            'created_at': profile.created_at.isoformat(),
        })
        
    else:
        messages.error(request, 'Invalid format requested')
        return redirect('profile_detail', profile_id=profile_id)
    
    return response


@login_required
def export_history(request):
    """
    View export history
    """
    exports = ExportHistory.objects.filter(user=request.user)
    
    paginator = Paginator(exports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'exports/history.html', {'page_obj': page_obj})


@login_required
def download_export(request, export_id):
    """
    Download previously exported file (Note: Files are not stored, this is a placeholder)
    """
    export = get_object_or_404(ExportHistory, id=export_id, user=request.user)
    
    # Since we don't store actual files, show a message
    messages.info(request, f'Please regenerate the {export.export_format.upper()} export using the export buttons.')
    return redirect('export_dashboard')