from django.db import models

class TravelQuery(models.Model):
    destination = models.CharField(max_length=100)
    duration = models.PositiveIntegerField()
    budget = models.CharField(max_length=50)
    styles = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.destination} ({self.duration} days)"
