from django.contrib import admin, messages
from .models import Plant, CommonName, Phytochemical, PlantRequest, CSVUpload
from django.db.models import Count


# --- Inline Admins ---
class CommonNameInline(admin.TabularInline):
    model = CommonName
    extra = 1  # Number of empty forms to display
    autocomplete_fields = ['plant']


class PhytochemicalInline(admin.TabularInline):
    model = Phytochemical
    extra = 1
    autocomplete_fields = ['plant']


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    search_fields = ('scientific_name',)
    list_display = (
        'scientific_name',
        'common_names_list',
        'phytochemicals_count',
    )
    inlines = [CommonNameInline, PhytochemicalInline]

    # 🔹 IMPORTANT: annotate queryset
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(phytochemicals_total=Count('phytochemicals'))

    def common_names_list(self, obj):
        return ", ".join(obj.common_names.values_list('name', flat=True))
    common_names_list.short_description = "Common Names"

    def phytochemicals_count(self, obj):
        return obj.phytochemicals_total

    # 🔹 Enable sorting
    phytochemicals_count.admin_order_field = 'phytochemicals_total'
    phytochemicals_count.short_description = "Number of Phytochemicals"



# --- Common Name Admin ---
# @admin.register(CommonName)
class CommonNameAdmin(admin.ModelAdmin):
    search_fields = ('name', 'plant__scientific_name')
    list_display = ('name', 'plant')
    list_filter = ('plant',)


# --- Phytochemical Admin ---
@admin.register(Phytochemical)
class PhytochemicalAdmin(admin.ModelAdmin):
    search_fields = ('compound_name', 'cid', 'plant__scientific_name')
    list_display = ('compound_name', 'plant', 'cid', 'reference')
    list_filter = ('plant',)
    autocomplete_fields = ['plant']





@admin.register(PlantRequest)
class PlantRequestAdmin(admin.ModelAdmin):
    list_display = ('plant_name', 'email', 'status', 'created_at', 'notified_at')
    list_filter = ('status', 'created_at')
    search_fields = ('plant_name', 'email')
    readonly_fields = ('created_at',)


@admin.register(CSVUpload)
class CSVUploadAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

    def save_model(self, request, obj, form, change):
        """
        Override save to import CSV automatically and show success message.
        """
        super().save_model(request, obj, form, change)  # Save first

        # Import CSV and get totals
        totals = obj.import_csv()

        # Display success message in admin
        messages.success(
            request,
            f"CSV import complete: "
            f"{totals['plants']} plant(s), "
            f"{totals['common_names']} common name(s), "
            f"{totals['phytochemicals']} phytochemical(s) imported."
        )


