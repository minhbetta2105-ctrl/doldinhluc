# Q5: A proxy model migration creates model state, not a database table.
from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies = [("receptive", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ReadingExercise",
            fields=[],
            options={"verbose_name": "Bài luyện Reading", "verbose_name_plural": "Quản lý bài Reading", "proxy": True, "indexes": [], "constraints": []},
            bases=("receptive.exercise",),
        ),
    ]
