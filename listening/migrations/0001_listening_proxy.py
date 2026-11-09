# Q5: A proxy model migration creates model state, not a database table.
from django.db import migrations

class Migration(migrations.Migration):
    initial = True
    dependencies = [("receptive", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="ListeningExercise",
            fields=[],
            options={"verbose_name": "Bài luyện Listening", "verbose_name_plural": "Quản lý bài Listening", "proxy": True, "indexes": [], "constraints": []},
            bases=("receptive.exercise",),
        ),
    ]
