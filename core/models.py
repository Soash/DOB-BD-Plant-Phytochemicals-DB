from django.db import models

class Plant(models.Model):
    scientific_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.scientific_name


class CommonName(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='common_names')
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ('plant', 'name')

    def __str__(self):
        return self.name


class Phytochemical(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='phytochemicals')
    compound_name = models.CharField(max_length=255)
    cid = models.CharField(max_length=100, blank=True)
    reference = models.TextField(blank=True)

    class Meta:
        unique_together = ('plant', 'compound_name', 'cid')

    def __str__(self):
        return self.compound_name





class PlantRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('uploaded', 'Uploaded/Notified'),
    ]
    plant_name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.plant_name} ({self.email}) - {self.get_status_display()}"


class CSVUpload(models.Model):
    file = models.FileField(upload_to='data/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def import_csv(self):
        """
        Reads the uploaded CSV and imports Plants, CommonNames, Phytochemicals.
        Returns a dict with totals for admin messages.
        """
        total_plants = 0
        total_common_names = 0
        total_phytochemicals = 0

        file_path = self.file.path

        # Try UTF-8 first, fallback to Latin1
        try:
            with open(file_path, encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except UnicodeDecodeError:
            with open(file_path, encoding='latin1', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

        current_plant = None

        for row in rows:
            # Normalize headers to lowercase
            row = {k.strip().lower(): (v or '').strip() for k, v in row.items()}

            plant_name = row.get('plant name', '')
            common_name = row.get('common name', '')
            compound = row.get('phytochemicals', '')
            cid = row.get('cid', '').replace('\xa0', '')
            reference = row.get('reference', '')

            if not compound:
                continue

            # Create or get Plant
            if plant_name:
                current_plant, created = Plant.objects.get_or_create(
                    scientific_name=plant_name
                )
                if created:
                    total_plants += 1

            if not current_plant:
                continue

            # Create or get CommonName
            if common_name:
                cn_obj, created = CommonName.objects.get_or_create(
                    plant=current_plant,
                    name=common_name
                )
                if created:
                    total_common_names += 1

            # Create or get Phytochemical
            obj, created = Phytochemical.objects.get_or_create(
                plant=current_plant,
                compound_name=compound,
                cid=cid,
                defaults={'reference': reference}
            )
            if not created and not obj.reference and reference:
                obj.reference = reference
                obj.save()

            total_phytochemicals += 1

        return {
            "plants": total_plants,
            "common_names": total_common_names,
            "phytochemicals": total_phytochemicals
        }
